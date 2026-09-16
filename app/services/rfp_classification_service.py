import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from openai import OpenAI
from google import genai
from google.genai import types
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.rfp import RFP
from app.schemas.rfp_classification import (
    ALLOWED_PRIMARY_CATEGORIES,
    ALLOWED_PROCUREMENT_TYPES,
    RFPClassificationResult,
)
from app.services.agent_config_service import agent_config_service

logger = logging.getLogger(__name__)

CLASSIFICATION_SYSTEM_PROMPT = """You are an expert Procurement and RFP Category Classification AI.
Your task is to classify an RFP (Request for Proposal) opportunity using a strict taxonomy.

TOP-LEVEL PRIMARY CATEGORIES (You must select EXACTLY ONE from this list):
- software: Software applications, commercial off-the-shelf platforms, enterprise software, licenses, SaaS, bespoke software products.
- hardware: Physical IT and computing equipment, desktops, laptops, servers, storage arrays, networking hardware (switches, routers, firewalls, cabling).
- it_services: Software development, custom development, systems integration, IT consulting, managed IT services, tech support, portal/web development, IT outsourcing.
- telecommunications: Internet connectivity, telecom infrastructure, mobile carrier services, satellite, VoIP, ISP services.
- cybersecurity: Security software, security assessments, SOC operations, penetration testing, vulnerability audits, managed security services.
- cloud: Cloud infrastructure (AWS, Azure, GCP), cloud hosting, cloud migration, PaaS, IaaS.
- professional_services: Legal, financial, audit, accounting, management consulting, general business advisory.
- construction: Civil engineering, building construction, renovation, architectural works.
- healthcare: Medical devices, pharmaceuticals, clinical services, hospital supplies.
- transportation: Logistics, fleet management, vehicles, shipping, public transit systems.
- security: Physical security, surveillance cameras, guard services, access control systems.
- office_supplies: Stationery, office furniture, printing paper, consumables.
- education: Training, curriculum development, learning materials, educational equipment.
- other: Any procurement that genuinely does not fit into any of the above categories.

STRICT CLASSIFICATION RULES:
1. Classify based on the PRIMARY PROCUREMENT OBJECTIVE, not merely mentioned keywords.
   - Do NOT classify an RFP as hardware simply because hardware is mentioned.
   - Do NOT classify an RFP as software simply because software is mentioned.
   - Example: "Supply and installation of 500 laptops" -> hardware / computers / product
   - Example: "Development and maintenance of an enterprise web portal" -> it_services / web_development / service
   - Example: "Microsoft 365 enterprise subscription" -> software / saas / subscription
   - Example: "Cloud infrastructure migration to AWS" -> cloud / cloud_migration / implementation
   - Example: "Supply and installation of network routers and switches" -> hardware / networking_equipment / product
   - Example: "Penetration testing and security assessment" -> cybersecurity / vulnerability_assessment / service
2. NEVER invent a category outside the allowed top-level categories.
3. ALLOWED PROCUREMENT TYPES (Choose EXACTLY ONE):
   - product
   - service
   - software_license
   - subscription
   - consulting
   - implementation
   - maintenance
   - mixed
   - other
4. Use 'secondary_categories' for materially important secondary aspects (must also be from allowed categories).
5. If information is insufficient, use 'other' with lower confidence.
6. Provide output in strictly valid JSON format matching:
{
  "primary_category": "category_name",
  "secondary_categories": ["optional_secondary_category"],
  "sub_category": "granular_subcategory_string",
  "procurement_type": "procurement_type_name",
  "confidence": 0.95,
  "keywords": ["keyword1", "keyword2"],
  "short_reason": "One concise sentence explaining the classification."
}
"""

CLASSIFICATION_USER_PROMPT = """Classify the following RFP opportunity:

Title: {title}
Organization: {organization}
Estimated Budget: {budget}
Deadline: {deadline}
Description: {description}
Key Requirements: {requirements}
Eligibility: {eligibility}

Respond ONLY with the structured JSON object.
"""


class RFPClassificationService:
    def __init__(self, max_retries: int = 2):
        self.max_retries = max_retries

    def _resolve_provider_and_client(
        self, db: Optional[Session]
    ) -> Tuple[str, Any, str, float]:
        """
        Resolves the active AI provider, client instance, model name, and temperature.
        Checks active database config first, then falls back to environment variables.
        """
        if db:
            try:
                active_config = agent_config_service.get_active_config(db)
                if active_config and active_config.api_key:
                    provider = (active_config.provider or "openai").lower().strip()
                    api_key = active_config.api_key.strip()
                    model_name = active_config.model_name or ("gpt-4o" if provider == "openai" else "gemini-2.5-flash")
                    temperature = float(active_config.temperature or 0.0)

                    if provider == "openai":
                        client = OpenAI(api_key=api_key)
                        return "openai", client, model_name, temperature
                    elif provider in {"gemini", "google"}:
                        client = genai.Client(api_key=api_key)
                        return "gemini", client, model_name, temperature
            except Exception as e:
                logger.warning(f"Could not load active AI config from DB: {e}. Falling back to env.")

        # Fallback to environment variables
        env_openai_key = settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY")
        env_gemini_key = os.environ.get("GEMINI_API_KEY")
        default_provider = os.environ.get("AI_PROVIDER", "openai").lower().strip()

        if default_provider in {"gemini", "google"} and env_gemini_key:
            return "gemini", genai.Client(api_key=env_gemini_key), "gemini-2.5-flash", 0.0
        elif env_openai_key:
            return "openai", OpenAI(api_key=env_openai_key), "gpt-4o", 0.0
        elif env_gemini_key:
            return "gemini", genai.Client(api_key=env_gemini_key), "gemini-2.5-flash", 0.0

        raise ValueError("No AI provider configured. Please provide an active configuration or API key.")

    def get_current_model_name(self, db: Optional[Session] = None) -> str:
        """
        Returns the active model name for audit/metadata tracking.
        """
        try:
            _, _, model_name, _ = self._resolve_provider_and_client(db)
            return model_name
        except Exception:
            return "unknown-model"

    def _build_user_prompt(self, rfp_data: dict) -> str:
        """
        Compacts the normalized RFP fields to avoid sending unnecessary raw content or HTML.
        """
        title = str(rfp_data.get("title") or "").strip()
        org = str(rfp_data.get("organization") or "Not specified").strip()
        desc = str(rfp_data.get("description") or "").strip()
        if len(desc) > 1500:
            desc = desc[:1500] + " ...[truncated]"

        deadline = str(rfp_data.get("submission_deadline") or "Not specified").strip()
        budget = f"{rfp_data.get('estimated_budget') or ''} {rfp_data.get('currency') or ''}".strip()
        if not budget:
            budget = "Not specified"

        reqs = rfp_data.get("requirements")
        if isinstance(reqs, list):
            reqs_str = "; ".join(str(r) for r in reqs[:6])
        else:
            reqs_str = str(reqs or "None specified")[:500]

        elig = rfp_data.get("eligibility")
        if isinstance(elig, list):
            elig_str = "; ".join(str(e) for e in elig[:4])
        else:
            elig_str = str(elig or "None specified")[:300]

        return CLASSIFICATION_USER_PROMPT.format(
            title=title,
            organization=org,
            budget=budget,
            deadline=deadline,
            description=desc or "No additional description provided.",
            requirements=reqs_str,
            eligibility=elig_str,
        )

    def _call_ai_model(
        self,
        provider: str,
        client: Any,
        model_name: str,
        temperature: float,
        user_prompt: str,
    ) -> str:
        """
        Executes structured JSON query against the target provider.
        """
        if provider == "openai":
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": CLASSIFICATION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                response_format={"type": "json_object"},
            )
            return response.choices[0].message.content or "{}"
        elif provider in {"gemini", "google"}:
            config = types.GenerateContentConfig(
                system_instruction=CLASSIFICATION_SYSTEM_PROMPT,
                response_mime_type="application/json",
                temperature=temperature,
            )
            response = client.models.generate_content(
                model=model_name,
                contents=user_prompt,
                config=config,
            )
            return response.text or "{}"
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def classify_rfp(
        self, rfp_data: dict, db: Optional[Session] = None
    ) -> Optional[RFPClassificationResult]:
        """
        Classifies a single normalized RFP dictionary.
        Returns a validated RFPClassificationResult or None if classification fails.
        """
        title = str(rfp_data.get("title") or "").strip()
        if not title:
            logger.warning("RFP classification skipped: Empty title")
            return None

        logger.info(f"RFP classification started: title='{title[:60]}'")
        user_prompt = self._build_user_prompt(rfp_data)

        try:
            provider, client, model_name, temp = self._resolve_provider_and_client(db)
        except Exception as e:
            logger.error(f"RFP classification failed: Provider resolution error: {e}")
            return None

        last_err: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                raw_json = self._call_ai_model(
                    provider=provider,
                    client=client,
                    model_name=model_name,
                    temperature=temp,
                    user_prompt=user_prompt,
                )

                # Validate against structured Pydantic schema
                result = RFPClassificationResult.model_validate_json(raw_json)

                logger.info(
                    f"RFP classification completed: "
                    f"category={result.primary_category}, "
                    f"subcategory={result.sub_category}, "
                    f"type={result.procurement_type}, "
                    f"confidence={result.confidence:.2f}"
                )
                return result

            except Exception as exc:
                last_err = exc
                is_rate_limit_or_timeout = any(
                    err_hint in str(exc).lower()
                    for err_hint in ["429", "rate limit", "timeout", "timed out", "connection", "overloaded"]
                )
                if attempt < self.max_retries and is_rate_limit_or_timeout:
                    wait_time = 1.5 * (attempt + 1)
                    logger.warning(
                        f"RFP classification transient error (attempt {attempt + 1}/{self.max_retries + 1}): {exc}. Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    break

        logger.error(f"RFP classification failed for title='{title[:60]}': {last_err}")
        return None

    def classify_existing_rfp(
        self, db: Session, rfp_id: int, force: bool = False
    ) -> Optional[RFP]:
        """
        Idempotent method to classify an existing RFP in the database.
        If force=False and rfp is already completed, skips classification.
        """
        rfp = db.query(RFP).filter(RFP.id == rfp_id).first()
        if not rfp:
            logger.error(f"RFP with id {rfp_id} not found for classification.")
            return None

        if not force and rfp.classification_status == "completed" and rfp.primary_category:
            logger.info(f"RFP {rfp_id} already classified ({rfp.primary_category}). Skipping.")
            return rfp

        rfp_data = {
            "title": rfp.title,
            "organization": rfp.organization,
            "description": rfp.description,
            "submission_deadline": str(rfp.submission_deadline or ""),
            "estimated_budget": rfp.estimated_budget,
            "currency": rfp.currency,
            "requirements": rfp.requirements,
            "eligibility": rfp.eligibility,
        }

        classification = self.classify_rfp(rfp_data, db=db)
        rfp.classification_attempts = (rfp.classification_attempts or 0) + 1

        if classification:
            rfp.primary_category = classification.primary_category
            rfp.sub_category = classification.sub_category
            rfp.procurement_type = classification.procurement_type
            rfp.confidence = classification.confidence
            rfp.keywords = classification.keywords
            rfp.secondary_categories = classification.secondary_categories
            rfp.classification_reason = classification.short_reason
            rfp.classified_at = datetime.now(timezone.utc)
            rfp.classification_model = self.get_current_model_name(db=db)
            rfp.classification_status = "completed"
        else:
            rfp.classification_status = "failed"

        db.add(rfp)
        db.commit()
        db.refresh(rfp)
        return rfp

    def classify_pending_or_failed_rfps(
        self, db: Session, limit: int = 50
    ) -> Dict[str, int]:
        """
        Reprocessing utility: searches for RFPs in 'pending' or 'failed' status
        and re-attempts classification up to the specified limit.
        """
        query = (
            db.query(RFP)
            .filter(
                (RFP.classification_status.in_(["pending", "failed"]))
                | (RFP.primary_category.is_(None))
            )
            .order_by(RFP.id.desc())
            .limit(limit)
        )
        rfps_to_process = query.all()

        succeeded = 0
        failed = 0

        for rfp in rfps_to_process:
            updated_rfp = self.classify_existing_rfp(db, rfp.id, force=True)
            if updated_rfp and updated_rfp.classification_status == "completed":
                succeeded += 1
            else:
                failed += 1

        return {
            "processed": len(rfps_to_process),
            "succeeded": succeeded,
            "failed": failed,
        }


rfp_classification_service = RFPClassificationService()
