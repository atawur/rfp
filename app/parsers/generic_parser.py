import re
from typing import List, Any, Optional, Tuple
from app.parsers.base import BaseExtractionParser, ParsedRFPItem

REF_PATTERNS = [
    re.compile(r"Reference\s*(?:Number|No\.?|#)?\s*[:=\-]\s*([A-Za-z0-9\-_/.]{3,40})", re.IGNORECASE),
    re.compile(r"(?:RFP|Tender|Notice|Ref|Bid|Solicitation|IFB|EOI)\s*(?:No\.?|Number|#)?\s*[:=]\s*([A-Za-z0-9\-_/.]{3,40})", re.IGNORECASE),
]


DEADLINE_PATTERNS = [
    re.compile(r"(?:Submission\s+Deadline|Deadline|Closing\s+Date|Due\s+Date|Last\s+Date\s+of\s+Submission|Submission\s+Date)\s*(?:is|on)?\s*[:=\-]?\s*([0-9]{1,2}[-/\s]+[A-Za-z]+[-/\s]+[0-9]{2,4}|[0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{1,2}[-/.][0-9]{1,2}[-/.][0-9]{2,4})", re.IGNORECASE),
    re.compile(r"(?:close|closes|due)\s+at\s+([0-9]{1,2}[-/\s]+[A-Za-z]+[-/\s]+[0-9]{2,4}|[0-9]{4}-[0-9]{2}-[0-9]{2})", re.IGNORECASE),
]

PUBLISHED_PATTERNS = [
    re.compile(r"(?:Published\s+Date|Issue\s+Date|Posting\s+Date|Published\s+On)\s*[:=\-]?\s*([0-9]{1,2}[-/\s]+[A-Za-z]+[-/\s]+[0-9]{2,4}|[0-9]{4}-[0-9]{2}-[0-9]{2})", re.IGNORECASE),
]

BUDGET_PATTERNS = [
    re.compile(r"(?:Budget|Estimated\s+Cost|Estimated\s+Value|Value)\s*[:=\-]?\s*([$€£¥]|USD|EUR|GBP|BDT|INR)?\s*([\d,]+(?:\.\d{2})?)", re.IGNORECASE),
]

EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
PHONE_PATTERN = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b")

class GenericParser(BaseExtractionParser):
    @property
    def name(self) -> str:
        return "generic_regex"

    def can_parse(self, doc_or_candidate: Any) -> bool:
        # Generic heuristic parser can always attempt to parse
        return True

    def _extract_ref_no(self, text: str) -> Optional[str]:
        for pattern in REF_PATTERNS:
            match = pattern.search(text)
            if match:
                ref = match.group(1).strip()
                if len(ref) >= 3 and not ref.lower() in {"n/a", "na", "none", "null"}:
                    return ref
        return None

    def _extract_deadline(self, text: str) -> Optional[str]:
        for pattern in DEADLINE_PATTERNS:
            match = pattern.search(text)
            if match:
                val = match.group(1).strip()
                return val
        return None

    def _extract_published(self, text: str) -> Optional[str]:
        for pattern in PUBLISHED_PATTERNS:
            match = pattern.search(text)
            if match:
                return match.group(1).strip()
        return None

    def _extract_budget(self, text: str) -> Tuple[Optional[float], Optional[str]]:
        for pattern in BUDGET_PATTERNS:
            match = pattern.search(text)
            if match:
                curr = match.group(1) or None
                num_str = match.group(2).replace(",", "")
                try:
                    val = float(num_str)
                    if val > 0:
                        return val, curr
                except ValueError:
                    pass
        return None, None

    def _extract_contacts(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        email = None
        phone = None
        email_match = EMAIL_PATTERN.search(text)
        if email_match:
            email = email_match.group(0).strip()

        phone_match = PHONE_PATTERN.search(text)
        if phone_match:
            phone = phone_match.group(0).strip()

        return email, phone

    def parse(self, doc_or_candidate: Any) -> List[ParsedRFPItem]:
        title = getattr(doc_or_candidate, "title", "")
        content = getattr(doc_or_candidate, "normalized_content", "") or getattr(doc_or_candidate, "raw_relevant_text", "")
        source_url = getattr(doc_or_candidate, "source_url", "")
        doc_urls = getattr(doc_or_candidate, "document_urls", [])

        ref_no = self._extract_ref_no(content)
        deadline = self._extract_deadline(content)
        published = self._extract_published(content)
        budget, currency = self._extract_budget(content)
        email, phone = self._extract_contacts(content)

        # Truncate clean description
        desc_lines = [l.strip() for l in content.splitlines() if l.strip() and not l.startswith(("URL:", "Type:"))]
        description = "\n".join(desc_lines[:15]) if desc_lines else None

        item = ParsedRFPItem(
            title=title or "Procurement Notice",
            reference_number=ref_no,
            submission_deadline=deadline,
            published_date=published,
            estimated_budget=budget,
            currency=currency,
            contact_email=email,
            contact_phone=phone,
            description=description,
            document_urls=doc_urls,
            source_url=source_url,
            parser_name=self.name,
            confidence=0.5,
        )
        return [item]

generic_parser = GenericParser()
