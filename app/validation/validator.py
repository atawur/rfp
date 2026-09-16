import re
from typing import Tuple, Dict, Any, Optional
from app.schemas.rfp_classification import ALLOWED_PRIMARY_CATEGORIES, ALLOWED_PROCUREMENT_TYPES

EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
DATE_ISO_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")

class UnifiedValidator:
    """
    Unified validation layer enforced equally on deterministic extraction
    and LLM batch outputs before persisting to the database.
    """

    GENERIC_TITLE_BLACKLIST = {
        "rfp", "tender", "tenders", "procurement", "procurements",
        "notice", "notices", "untitled", "untitled rfp", "unknown rfp",
        "n/a", "na", "none", "placeholder", "home", "homepage",
        "welcome", "procurement notice", "invitation to tender"
    }

    def validate_item(self, item: Dict[str, Any]) -> Tuple[bool, str]:
        # 1. Title validation
        raw_title = item.get("title")
        if not raw_title or not isinstance(raw_title, str):
            return False, "missing or non-string title"

        clean_title = raw_title.strip()
        if len(clean_title) < 5:
            return False, f"title is too short (< 5 characters): '{clean_title}'"

        if clean_title.lower() in self.GENERIC_TITLE_BLACKLIST:
            return False, f"generic non-descriptive title: '{clean_title}'"

        # 2. Category taxonomy validation
        cat = item.get("primary_category") or item.get("category")
        if cat and isinstance(cat, str):
            norm_cat = cat.strip().lower().replace(" ", "_").replace("-", "_")
            if norm_cat not in ALLOWED_PRIMARY_CATEGORIES:
                return False, f"invalid primary_category '{cat}' not in taxonomy"

        proc_type = item.get("procurement_type")
        if proc_type and isinstance(proc_type, str):
            norm_proc = proc_type.strip().lower().replace(" ", "_").replace("-", "_")
            if norm_proc not in ALLOWED_PROCUREMENT_TYPES:
                return False, f"invalid procurement_type '{proc_type}' not in taxonomy"

        # 3. Substantive content verification
        description = str(item.get("description") or "").strip()
        ref_no = str(item.get("reference_number") or "").strip()
        deadline = str(item.get("submission_deadline") or "").strip()
        budget = item.get("estimated_budget")
        requirements = item.get("requirements")
        eligibility = item.get("eligibility")
        docs = item.get("documents") or item.get("document_urls") or []

        has_substantive_details = (
            len(description) > 15
            or bool(ref_no)
            or bool(deadline)
            or budget is not None
            or bool(requirements)
            or bool(eligibility)
            or len(docs) > 0
        )

        if not has_substantive_details:
            return False, "insufficient procurement details (no description, deadline, ref number, or documents)"

        # 4. Email validation if provided
        contact_email = item.get("contact_email")
        if contact_email and isinstance(contact_email, str) and contact_email.strip():
            if not EMAIL_REGEX.search(contact_email):
                # Flag but don't reject if other details are strong
                pass

        return True, "valid"

    def normalize_for_persistence(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizes and canonicalizes fields before RFP database insertion."""
        clean = dict(item)

        # Ensure title is trimmed
        clean["title"] = str(clean.get("title", "")).strip()

        # Normalize category
        cat = clean.get("primary_category") or clean.get("category")
        if cat and isinstance(cat, str):
            norm_cat = cat.strip().lower().replace(" ", "_").replace("-", "_")
            if norm_cat in ALLOWED_PRIMARY_CATEGORIES:
                clean["primary_category"] = norm_cat
            else:
                clean["primary_category"] = "other"
        else:
            clean["primary_category"] = "other"

        # Normalize procurement_type
        pt = clean.get("procurement_type")
        if pt and isinstance(pt, str):
            norm_pt = pt.strip().lower().replace(" ", "_").replace("-", "_")
            if norm_pt in ALLOWED_PROCUREMENT_TYPES:
                clean["procurement_type"] = norm_pt
            else:
                clean["procurement_type"] = "service"
        else:
            clean["procurement_type"] = "service"

        # Normalize confidence to [0.0, 1.0]
        conf = clean.get("confidence")
        if conf is not None:
            try:
                clean["confidence"] = min(max(float(conf), 0.0), 1.0)
            except (ValueError, TypeError):
                clean["confidence"] = 0.5

        return clean

unified_validator = UnifiedValidator()
