import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sentence_transformers import SentenceTransformer

from app.change_detection.comparator import compare_and_update
from app.duplicate_detection.detector import find_duplicate
from app.email.provider import email_provider
from app.models.rfp import RFP
from app.repositories.rfp_repo import rfp_repo
from app.repositories.user_repo import user_repo
from app.schemas.rfp import RFPCreate, RFPUpdate
from app.schemas.rfp_classification import ALLOWED_PRIMARY_CATEGORIES, ALLOWED_PROCUREMENT_TYPES
from app.services.rfp_classification_service import rfp_classification_service

from app.crawler.playwright_crawler import playwright_crawler
from app.normalization.normalizer import generic_normalizer
from app.discovery.candidate_discovery import candidate_discovery_service, RFPCandidate
from app.fingerprint.change_detector import change_detection_service
from app.fingerprint.hasher import content_fingerprinter
from app.extraction.deterministic_extractor import deterministic_extractor
from app.llm_pipeline.llm_queue import llm_queue, QueueItem
from app.llm_pipeline.batch_processor import batch_processor
from app.validation.validator import unified_validator
from app.metrics.pipeline_metrics import PipelineMetrics


logger = logging.getLogger(__name__)


class RFPService:
    GENERIC_TITLE_BLACKLIST = {
        "rfp",
        "tender",
        "tenders",
        "procurement",
        "procurements",
        "notice",
        "notices",
        "untitled",
        "untitled rfp",
        "unknown rfp",
        "n/a",
        "na",
        "none",
        "placeholder",
        "home",
        "homepage",
        "welcome",
    }

    def get_rfps(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        website_id: Optional[int] = None,
        category: Optional[str] = None,
        sub_category: Optional[str] = None,
        procurement_type: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[RFP]:
        return rfp_repo.get_filtered_rfps(
            db,
            skip=skip,
            limit=limit,
            website_id=website_id,
            category=category,
            sub_category=sub_category,
            procurement_type=procurement_type,
            status=status,
            search=search,
        )

    def get_paginated_rfps(
        self,
        db: Session,
        page: int = 1,
        size: int = 20,
        website_id: Optional[int] = None,
        category: Optional[str] = None,
        sub_category: Optional[str] = None,
        procurement_type: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        import math
        skip = max(0, (page - 1) * size)
        items, total = rfp_repo.get_filtered_rfps_with_total(
            db,
            skip=skip,
            limit=size,
            website_id=website_id,
            category=category,
            sub_category=sub_category,
            procurement_type=procurement_type,
            status=status,
            search=search,
        )
        pages = math.ceil(total / size) if size > 0 and total > 0 else 1
        return {
            "items": items,
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
        }


    def get_rfp_by_id(self, db: Session, rfp_id: int) -> RFP:
        rfp = rfp_repo.get(db, id=rfp_id)
        if not rfp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="RFP not found"
            )
        return rfp

    def create_rfp(self, db: Session, rfp_in: RFPCreate) -> RFP:
        return rfp_repo.create(db, obj_in=rfp_in)

    def process_extracted_rfp(self, db: Session, rfp_data: dict) -> RFP:
        """
        Orchestrates duplicate detection, change detection, and persistence.
        """
        existing_rfp = find_duplicate(db, rfp_data)

        if existing_rfp:
            logger.info(f"RFP {existing_rfp.id} exists. Checking for changes...")
            existing_rfp, _ = compare_and_update(db, existing_rfp, rfp_data)
            return existing_rfp
        else:
            logger.info("Creating new RFP...")
            new_rfp_schema = RFPCreate(**rfp_data)
            new_rfp = rfp_repo.create(db, obj_in=new_rfp_schema)

            # Trigger notification
            evaluate_and_notify_users(db, new_rfp)

            return new_rfp

    def _is_valid_rfp_candidate(self, item: dict) -> Tuple[bool, str]:
        """
        Generic, website-agnostic validation to ensure extracted content
        represents a genuine RFP opportunity rather than a placeholder,
        navigation artifact, or failed extraction.
        """
        raw_title = item.get("title")
        if not raw_title or not isinstance(raw_title, str):
            return False, "missing or non-string title"

        clean_title = raw_title.strip()
        if len(clean_title) < 5:
            return False, "title is too short (< 5 characters)"

        lower_title = clean_title.lower()
        if lower_title in self.GENERIC_TITLE_BLACKLIST:
            return False, f"generic non-descriptive title: '{clean_title}'"

        # Check confidence score if provided by extraction agent
        confidence = item.get("confidence")
        if confidence is not None and isinstance(confidence, (int, float)) and confidence < 0.3:
            return False, f"confidence score too low: {confidence}"

        # Substantive content verification:
        # A valid procurement record must carry at least one actionable detail
        # (deadline, reference number, meaningful description, requirements, or budget)
        description = str(item.get("description") or "").strip()
        ref_no = str(item.get("reference_number") or "").strip()
        deadline = str(item.get("submission_deadline") or "").strip()
        budget = item.get("estimated_budget")
        requirements = item.get("requirements")
        eligibility = item.get("eligibility")

        has_substantive_details = (
            len(description) > 15
            or bool(ref_no)
            or bool(deadline)
            or budget is not None
            or bool(requirements)
            or bool(eligibility)
        )

        if not has_substantive_details:
            return False, "insufficient procurement details (no description, deadline, ref number, or requirements)"

        return True, "valid"

    def process_extracted_data_synchronous(
        self,
        db: Session,
        extracted_data: Any,
        url_str: str,
        website_id: Optional[int] = None,
        notify: bool = True,
    ) -> List[dict]:
        if isinstance(extracted_data, dict):
            rfp_list = [extracted_data]
        elif isinstance(extracted_data, list):
            rfp_list = extracted_data
        else:
            return []

        model = SentenceTransformer('all-MiniLM-L6-v2')
        results = []
        newly_inserted_rfps = []

        for item in rfp_list:
            if not isinstance(item, dict):
                continue

            # 1. Generic candidate validation (replaces any static/hardcoded checks)
            is_valid, validation_reason = self._is_valid_rfp_candidate(item)
            title = str(item.get("title", "")).strip()

            if not is_valid:
                logger.info(f"Skipping invalid RFP candidate '{title}': {validation_reason}")
                results.append({
                    "status": "ignored",
                    "reason": validation_reason,
                    "title": title or "Unknown",
                })
                continue

            description = str(item.get("description") or "").strip()
            text_to_embed = f"{title} {description}".strip()

            embedding = model.encode(text_to_embed).tolist()

            # 2. Check for existing RFP via identity signals first, then semantic similarity
            match_source = "identity"
            existing_rfp = find_duplicate(db, item)
            if not existing_rfp:
                existing_rfp = rfp_repo.get_similar_by_embedding(db, embedding=embedding, threshold=0.15)
                if existing_rfp:
                    match_source = "semantic"

            if existing_rfp:
                existing_rfp, was_updated = compare_and_update(db, existing_rfp, item)
                reason_str = (
                    f"{match_source} duplicate found, updated changes"
                    if was_updated
                    else f"{match_source} duplicate found, already up to date"
                )
                results.append({
                    "status": "updated" if was_updated else "ignored",
                    "reason": reason_str,
                    "title": title,
                    "id": existing_rfp.id,
                })
                continue

            deadline_raw = item.get("submission_deadline")
            deadline_str = deadline_raw if deadline_raw and str(deadline_raw).strip() else None

            # Determine initial status based on agent validation flags if present
            status_val = item.get("status") or ("NEEDS_REVIEW" if item.get("validation_flags") else "NEW")

            # Resolve website_id: prefer item's website_id, then method argument website_id
            resolved_website_id = item.get("website_id") or website_id

            # Resolve source_url: prefer item's valid source_url, never save "bulk_crawl" placeholder
            raw_source_url = item.get("source_url")
            if raw_source_url and str(raw_source_url).strip() and str(raw_source_url).strip() != "bulk_crawl":
                resolved_source_url = str(raw_source_url).strip()
            elif url_str and url_str != "bulk_crawl":
                resolved_source_url = url_str
            elif resolved_website_id:
                from app.models.website import Website
                ws_obj = db.query(Website).filter(Website.id == resolved_website_id).first()
                resolved_source_url = ws_obj.start_url or ws_obj.base_url if ws_obj else "https://example.com/rfp"
            else:
                resolved_source_url = "https://example.com/rfp"

            norm_url = item.get("normalized_url")
            resolved_norm_url = norm_url if (norm_url and norm_url != "bulk_crawl") else resolved_source_url

            rfp_kwargs = {
                "website_id": resolved_website_id,
                "title": title,
                "reference_number": item.get("reference_number"),
                "organization": item.get("organization"),
                "description": description,
                "published_date": item.get("published_date"),
                "submission_deadline": deadline_str,
                "estimated_budget": item.get("estimated_budget"),
                "currency": item.get("currency"),
                "location": item.get("location"),
                "eligibility": item.get("eligibility"),
                "requirements": item.get("requirements"),
                "submission_method": item.get("submission_method"),
                "contact_person": item.get("contact_person"),
                "contact_email": item.get("contact_email"),
                "contact_phone": item.get("contact_phone"),
                "source_url": resolved_source_url,
                "normalized_url": resolved_norm_url,
                "content_hash": item.get("content_hash"),
                "extraction_method": item.get("extraction_method") or "deterministic",
                "parser_version": item.get("parser_version") or 1,
                "extraction_version": item.get("extraction_version") or 1,
                "last_processed_at": datetime.now(timezone.utc),
                "status": status_val,
                "embedding": embedding,
            }

            # 3. AI Category Classification for genuinely new RFP
            classification_data = {
                "classification_status": "pending",
                "classification_attempts": 0,
            }

            # Check if extraction agent already classified this opportunity in one shot
            raw_primary = item.get("primary_category") or item.get("category")
            norm_primary = None
            if raw_primary and isinstance(raw_primary, str):
                cleaned = raw_primary.strip().lower().replace(" ", "_").replace("-", "_")
                if cleaned in ALLOWED_PRIMARY_CATEGORIES:
                    norm_primary = cleaned

            if norm_primary:
                # Optimized path: Reuse classification already extracted by the agent
                raw_proc_type = str(item.get("procurement_type") or "service").strip().lower().replace(" ", "_").replace("-", "_")
                norm_proc_type = raw_proc_type if raw_proc_type in ALLOWED_PROCUREMENT_TYPES else "service"
                sub_cat = str(item.get("sub_category") or "general").strip().lower()
                conf = float(item.get("confidence") or 0.9)
                conf = min(max(conf, 0.0), 1.0)
                reason = str(item.get("short_reason") or "Classified during agent extraction").strip()
                keywords = item.get("keywords") if isinstance(item.get("keywords"), list) else []
                sec_cats = item.get("secondary_categories") if isinstance(item.get("secondary_categories"), list) else []

                classification_data = {
                    "primary_category": norm_primary,
                    "sub_category": sub_cat,
                    "procurement_type": norm_proc_type,
                    "confidence": conf,
                    "keywords": keywords,
                    "secondary_categories": sec_cats,
                    "classification_reason": reason,
                    "classified_at": datetime.now(timezone.utc),
                    "classification_model": rfp_classification_service.get_current_model_name(db=db),
                    "classification_status": "completed",
                    "classification_attempts": 1,
                }
                logger.info(
                    f"Reused agent-extracted classification for '{title}': "
                    f"category='{norm_primary}', sub='{sub_cat}' (0 extra API calls)"
                )
            else:
                # Fallback path: Standalone classification service call
                try:
                    classification = rfp_classification_service.classify_rfp(item, db=db)
                    if classification:
                        classification_data = {
                            "primary_category": classification.primary_category,
                            "sub_category": classification.sub_category,
                            "procurement_type": classification.procurement_type,
                            "confidence": classification.confidence,
                            "keywords": classification.keywords,
                            "secondary_categories": classification.secondary_categories,
                            "classification_reason": classification.short_reason,
                            "classified_at": datetime.now(timezone.utc),
                            "classification_model": rfp_classification_service.get_current_model_name(db=db),
                            "classification_status": "completed",
                            "classification_attempts": 1,
                        }
                    else:
                        classification_data["classification_status"] = "failed"
                        classification_data["classification_attempts"] = 1
                except Exception as cls_err:
                    logger.error(f"Classification fallback failed for candidate '{title}': {cls_err}")
                    classification_data["classification_status"] = "failed"
                    classification_data["classification_attempts"] = 1

            rfp_kwargs.update(classification_data)
            new_rfp = RFP(**rfp_kwargs)  # type: ignore
            db.add(new_rfp)
            db.commit()
            db.refresh(new_rfp)

            newly_inserted_rfps.append(new_rfp)
            results.append({"status": "inserted", "title": title, "id": new_rfp.id})

        # Asynchronously evaluate and notify eligible users with ALL newly inserted RFPs in a single email
        if notify and newly_inserted_rfps:
            try:
                from app.services.notification_service import evaluate_and_notify_users_batch
                evaluate_and_notify_users_batch(db, newly_inserted_rfps)
            except Exception as notify_err:
                logger.warning(f"Failed to trigger batch notifications for {len(newly_inserted_rfps)} newly inserted RFPs: {notify_err}")

        return results

    def extract_and_process_url(
        self,
        db: Session,
        url: str,
        website_id: Optional[int] = None,
        notify: bool = True,
        metrics: Optional[PipelineMetrics] = None,
    ) -> List[dict]:
        """
        Orchestrates target pipeline for a URL:
        1. Dynamic content fetching (Playwright / HTTP fallback)
        2. Dynamic normalization (BeautifulSoup noise stripping & title fallback)
        3. Candidate discovery (individual RFP vs listing items)
        4. SHA-256 fingerprinting & change detection (unchanged -> skip!)
        5. Deterministic extraction & category classification
        6. Confidence check: high-confidence -> direct save; low-confidence -> cached LLM batch queue
        7. Validation, deduplication, and persistence
        """
        url_str = str(url).strip()
        raw_html = playwright_crawler.fetch_page_content(url_str)
        if not raw_html or len(raw_html.strip()) < 20:
            if metrics:
                metrics.record_scrape(False)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error fetching page: Unable to retrieve content from {url_str}",
            )

        if metrics:
            metrics.record_scrape(True)

        # 2. Dynamic Normalization
        doc = generic_normalizer.normalize(raw_html, source_url=url_str)

        # 3. Candidate Discovery
        candidates = candidate_discovery_service.discover_candidates(doc)

        items_to_persist: List[dict] = []
        queue_items: List[QueueItem] = []
        ignored_results: List[dict] = []

        # 4 & 5. Fingerprinting, Change Detection, and Deterministic Extraction
        for candidate in candidates:
            eval_res = change_detection_service.evaluate_candidate(db, candidate, website_id=website_id)
            if metrics:
                metrics.record_candidate(eval_res.status)

            if eval_res.should_skip:
                logger.info(f"[Pipeline] UNCHANGED content for '{candidate.title}'. Skipping extraction & LLM.")
                ignored_results.append({
                    "status": "ignored",
                    "reason": f"unchanged content (hash={eval_res.content_hash[:8]})",
                    "title": candidate.title,
                })
                continue

            # Deterministic extraction attempt
            det_res = deterministic_extractor.extract_candidate(candidate)
            if det_res.is_high_confidence:
                if metrics:
                    metrics.record_deterministic()
                logger.info(
                    f"[Pipeline] High confidence deterministic extraction ({det_res.item.confidence}) "
                    f"for '{candidate.title}'. Skipping LLM."
                )
                rfp_dict = det_res.item.to_dict()
                rfp_dict["source_url"] = candidate.source_url
                rfp_dict["normalized_url"] = eval_res.normalized_url
                rfp_dict["content_hash"] = eval_res.content_hash
                rfp_dict["extraction_method"] = "deterministic"
                items_to_persist.append(rfp_dict)
            else:
                # Add to queue for LLM batching
                if metrics:
                    metrics.record_llm_queue()
                queue_items.append(QueueItem(
                    candidate=candidate,
                    content_hash=eval_res.content_hash,
                    normalized_url=eval_res.normalized_url,
                    website_id=website_id,
                    initial_deterministic=det_res.item,
                ))

        # 6. Process LLM Queue in Batches with Caching
        if queue_items:
            logger.info(f"[Pipeline] Processing {len(queue_items)} low-confidence items via cached batch processor.")
            llm_results = batch_processor.process_queue(db, queue_items, metrics=metrics)
            items_to_persist.extend(llm_results)

        # 7. Validate & Persist
        persisted_results = []
        if items_to_persist:
            persisted_results = self.process_extracted_data_synchronous(
                db,
                items_to_persist,
                url_str,
                website_id=website_id,
                notify=notify,
            )

        # 8. Record / Update Fingerprints in DB
        for item in items_to_persist:
            c_hash = item.get("content_hash")
            rfp_id = item.get("id")
            for cand in candidates:
                if cand.title == item.get("title") or cand.source_url == item.get("source_url"):
                    change_detection_service.record_or_update_fingerprint(
                        db=db,
                        candidate=cand,
                        rfp_id=rfp_id,
                        website_id=website_id,
                    )
                    break

        return ignored_results + persisted_results

    def crawl_multiple_websites(
        self,
        db: Session,
        websites: List[Any],
        batch_size: int = 5,
    ) -> Dict[str, Any]:
        """
        Processes a collection of websites according to Task.md target architecture:
        Phase 1: Scraping loop (fetch, normalize, candidate discover, hash, check unchanged, deterministic extract).
                 LLM is strictly NOT called in this loop!
        Phase 2: LLM Queue batching & persistent caching outside the scraping loop.
        Phase 3: Validation, deduplication, persistence & metrics reporting.
        """
        metrics = PipelineMetrics(total_websites=len(websites))
        all_queue_items: List[QueueItem] = []
        all_high_confidence_items: List[dict] = []
        site_candidates_map: Dict[str, List[RFPCandidate]] = {}

        logger.info(f"--- [Phase 1: Scraping & Deterministic Phase across {len(websites)} websites] ---")
        for website in websites:
            target_url = str(website.start_url or website.base_url).strip()
            logger.info(f"Scraping website {website.id} ('{website.name}'): {target_url}")

            raw_html = playwright_crawler.fetch_page_content(target_url)
            if not raw_html or len(raw_html.strip()) < 20:
                metrics.record_scrape(False)
                continue

            metrics.record_scrape(True)
            doc = generic_normalizer.normalize(raw_html, source_url=target_url, website_name=website.name)
            candidates = candidate_discovery_service.discover_candidates(doc)
            site_candidates_map[target_url] = candidates

            for candidate in candidates:
                eval_res = change_detection_service.evaluate_candidate(db, candidate, website_id=website.id)
                metrics.record_candidate(eval_res.status)

                if eval_res.should_skip:
                    continue

                det_res = deterministic_extractor.extract_candidate(candidate)
                if det_res.is_high_confidence:
                    metrics.record_deterministic()
                    rfp_dict = det_res.item.to_dict()
                    rfp_dict["source_url"] = candidate.source_url
                    rfp_dict["normalized_url"] = eval_res.normalized_url
                    rfp_dict["content_hash"] = eval_res.content_hash
                    rfp_dict["website_id"] = website.id
                    rfp_dict["extraction_method"] = "deterministic"
                    all_high_confidence_items.append(rfp_dict)
                else:
                    metrics.record_llm_queue()
                    all_queue_items.append(QueueItem(
                        candidate=candidate,
                        content_hash=eval_res.content_hash,
                        normalized_url=eval_res.normalized_url,
                        website_id=website.id,
                        initial_deterministic=det_res.item,
                    ))

        logger.info(f"--- [Phase 2: LLM Queue Processing ({len(all_queue_items)} items queued)] ---")
        llm_extracted_items: List[dict] = []
        if all_queue_items:
            batch_processor.batch_size = batch_size
            llm_extracted_items = batch_processor.process_queue(db, all_queue_items, metrics=metrics)

        total_items_to_save = all_high_confidence_items + llm_extracted_items

        logger.info(f"--- [Phase 3: Persistence & Notifications ({len(total_items_to_save)} items to save)] ---")
        persisted_results = []
        if total_items_to_save:
            persisted_results = self.process_extracted_data_synchronous(
                db,
                total_items_to_save,
                url_str="bulk_crawl",
                notify=True,
            )

        # Update fingerprints
        for item in total_items_to_save:
            for url, candidates in site_candidates_map.items():
                for cand in candidates:
                    if cand.title == item.get("title") or cand.source_url == item.get("source_url"):
                        change_detection_service.record_or_update_fingerprint(
                            db=db,
                            candidate=cand,
                            rfp_id=item.get("id"),
                            website_id=item.get("website_id"),
                        )
                        break

        summary = metrics.summary_report()
        logger.info(summary)

        return {
            "metrics": metrics.to_dict(),
            "summary_report": summary,
            "persisted_count": len(persisted_results),
            "results": persisted_results,
        }

    def import_from_url(self, db: Session, url: str) -> Dict[str, Any]:
        """
        Mode A import API helper returning standard response structure.
        """
        results = self.extract_and_process_url(db, url)
        return {
            "message": "Extraction and processing completed successfully",
            "results": results,
        }



rfp_service = RFPService()
