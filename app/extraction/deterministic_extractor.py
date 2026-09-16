import re
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple

from app.discovery.candidate_discovery import RFPCandidate
from app.parsers.base import ParsedRFPItem
from app.parsers.registry import parser_registry
from app.schemas.rfp_classification import ALLOWED_PRIMARY_CATEGORIES, ALLOWED_PROCUREMENT_TYPES
from app.validation.validator import unified_validator

logger = logging.getLogger(__name__)

CATEGORY_TAXONOMY_KEYWORDS: Dict[str, List[str]] = {
    "cybersecurity": [
        "soc", "siem", "firewall", "endpoint", "penetration testing", "pen test",
        "vulnerability", "dlp", "antivirus", "cyber", "infosec", "threat", "encryption",
        "security operations center", "incident response", "ids", "ips", "zero trust"
    ],
    "hardware": [
        "server", "workstation", "switch", "switches", "router", "routers", "cctv",
        "camera", "cameras", "laptop", "desktop", "storage", "nas", "san", "ups",
        "generator", "battery", "batteries", "hardware", "rack", "rfid", "avr", "nvr"
    ],
    "software": [
        "software", "erp", "crm", "application", "portal", "mobile app", "license",
        "saas", "api", "database", "oracle", "sap", "web development", "core banking",
        "virtualization", "operating system"
    ],
    "it_services": [
        "sla", "annual maintenance", "amc", "helpdesk", "managed service",
        "system integration", "it support", "maintenance contract", "technical support"
    ],
    "cloud": [
        "cloud", "aws", "azure", "gcp", "hosting", "migration", "kubernetes",
        "docker", "devops", "cloud backup", "disaster recovery"
    ],
    "telecommunications": [
        "fiber", "telecom", "broadband", "mpls", "voip", "bandwidth", "isp",
        "satellite", "radio", "internet", "leased line", "wan", "lan"
    ],
    "professional_services": [
        "audit", "consulting", "legal", "financial", "advisory", "accounting",
        "feasibility", "taxation", "valuation", "recruitment", "headhunting"
    ],
    "construction": [
        "civil", "renovation", "building", "hvac", "electrical", "wiring",
        "plumbing", "construction", "interior", "road", "bridge", "architecture"
    ],
    "healthcare": [
        "medical", "hospital", "pharmaceutical", "diagnostic", "clinic", "health",
        "medicine", "surgical", "laboratory"
    ],
    "transportation": [
        "vehicle", "fleet", "logistics", "transit", "car", "bus", "truck",
        "shipping", "courier", "transport"
    ],
    "security": [
        "guard", "patrol", "surveillance", "perimeter", "security guard",
        "access control", "physical security", "security personnel"
    ],
    "office_supplies": [
        "stationery", "paper", "toner", "cartridge", "furniture", "desk", "chair",
        "office supplies", "photocopier", "printing paper"
    ],
    "education": [
        "training", "curriculum", "elearning", "workshop", "course", "school",
        "academic", "capacity building"
    ],
}

PROCUREMENT_TYPE_PATTERNS = [
    ("software_license", re.compile(r"\b(software\s+license|licenses|licensing|subscription)\b", re.I)),
    ("product", re.compile(r"\b(supply|procurement\s+of|delivery\s+of|purchase\s+of|equipment|goods)\b", re.I)),
    ("consulting", re.compile(r"\b(consulting|consultancy|advisory|study|assessment)\b", re.I)),
    ("maintenance", re.compile(r"\b(maintenance|amc|sla|repair|servicing)\b", re.I)),
    ("implementation", re.compile(r"\b(implementation|deployment|installation|setup)\b", re.I)),
    ("service", re.compile(r"\b(service|services|hiring|outsourcing)\b", re.I)),
]

@dataclass
class DeterministicResult:
    item: ParsedRFPItem
    is_high_confidence: bool
    confidence_breakdown: Dict[str, float]
    validation_status: str
    validation_reason: str


class DeterministicExtractor:
    """
    Executes deterministic parsing, keyword taxonomy classification,
    and confidence scoring prior to entering the LLM queue.
    """

    def classify_category(self, text: str) -> Tuple[str, str, str, float, List[str], str]:
        """
        Classifies domain category, subcategory, and procurement type
        strictly against ALLOWED_PRIMARY_CATEGORIES and ALLOWED_PROCUREMENT_TYPES.
        """
        lower_text = text.lower()

        scores: Dict[str, List[str]] = {}
        for category, kws in CATEGORY_TAXONOMY_KEYWORDS.items():
            matched_kws = [kw for kw in kws if re.search(r"\b" + re.escape(kw) + r"\b", lower_text)]
            if matched_kws:
                scores[category] = matched_kws

        if not scores:
            return "other", "general", "service", 0.3, [], "No domain keywords matched; defaulted to other"

        # Best category is the one with the most distinct keyword matches
        sorted_categories = sorted(scores.items(), key=lambda x: len(x[1]), reverse=True)
        best_cat, matched_tokens = sorted_categories[0]

        # Calculate confidence based on token count
        confidence = min(0.60 + (len(matched_tokens) * 0.10), 0.95)

        sub_cat = matched_tokens[0].replace(" ", "_") if matched_tokens else "general"

        # Determine procurement type
        proc_type = "service"
        for p_type, regex in PROCUREMENT_TYPE_PATTERNS:
            if regex.search(lower_text):
                proc_type = p_type
                break

        reason = f"Deterministically matched keywords: {', '.join(matched_tokens[:3])}"
        return best_cat, sub_cat, proc_type, confidence, matched_tokens[:5], reason

    def compute_confidence(self, item: ParsedRFPItem) -> Tuple[float, Dict[str, float]]:
        breakdown: Dict[str, float] = {}

        # 1. Title quality (max 0.25)
        title = item.title.strip()
        if len(title) >= 10 and not title.lower() in unified_validator.GENERIC_TITLE_BLACKLIST:
            breakdown["title"] = 0.25
        elif len(title) >= 5:
            breakdown["title"] = 0.15
        else:
            breakdown["title"] = 0.0

        # 2. Actionable Deadline (max 0.25)
        deadline = item.submission_deadline
        if deadline and len(str(deadline).strip()) >= 6:
            breakdown["deadline"] = 0.25
        else:
            breakdown["deadline"] = 0.0

        # 3. Reference Number or Organization (max 0.20)
        ref_no = item.reference_number
        org = item.organization
        if ref_no and len(str(ref_no).strip()) >= 3:
            breakdown["reference_or_org"] = 0.20
        elif org and len(str(org).strip()) >= 3:
            breakdown["reference_or_org"] = 0.15
        else:
            breakdown["reference_or_org"] = 0.0

        # 4. Content Substantiveness: description or document links (max 0.15)
        desc = item.description or ""
        docs = item.document_urls or []
        if len(desc) >= 50 or len(docs) > 0:
            breakdown["content"] = 0.15
        elif len(desc) >= 15:
            breakdown["content"] = 0.10
        else:
            breakdown["content"] = 0.0

        # 5. Category Confidence (max 0.15)
        cat_conf = item.category_confidence or 0.0
        if cat_conf >= 0.8:
            breakdown["category"] = 0.15
        elif cat_conf >= 0.6:
            breakdown["category"] = 0.10
        else:
            breakdown["category"] = 0.05

        total = sum(breakdown.values())
        return round(total, 2), breakdown

    def extract_candidate(self, candidate: RFPCandidate) -> DeterministicResult:
        parser = parser_registry.get_parser_for_candidate(candidate)
        parsed_items = parser.parse(candidate)

        if not parsed_items:
            item = ParsedRFPItem(
                title=candidate.title,
                description=candidate.normalized_content,
                document_urls=candidate.document_urls,
                source_url=candidate.source_url,
                parser_name="fallback",
            )
        else:
            item = parsed_items[0]

        # Classify category deterministically
        full_text = f"{item.title} {item.description or ''} {candidate.normalized_content}"
        cat, sub, proc, cat_conf, kws, reason = self.classify_category(full_text)
        item.primary_category = cat
        item.sub_category = sub
        item.procurement_type = proc
        item.category_confidence = cat_conf
        item.keywords = kws
        item.short_reason = reason

        # Calculate overall extraction confidence
        total_conf, breakdown = self.compute_confidence(item)
        item.confidence = total_conf

        # Validate with unified validation rules
        is_valid, val_reason = unified_validator.validate_item(item.to_dict())

        # High confidence threshold: >= 0.80 and valid candidate
        is_high = is_valid and total_conf >= 0.80

        return DeterministicResult(
            item=item,
            is_high_confidence=is_high,
            confidence_breakdown=breakdown,
            validation_status="VALID" if is_valid else "INVALID",
            validation_reason=val_reason,
        )

deterministic_extractor = DeterministicExtractor()
