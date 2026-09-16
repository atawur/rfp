import re
from typing import List, Any
from app.parsers.base import BaseExtractionParser, ParsedRFPItem

class TableParser(BaseExtractionParser):
    @property
    def name(self) -> str:
        return "table"

    def can_parse(self, doc_or_candidate: Any) -> bool:
        candidate_type = getattr(doc_or_candidate, "candidate_type", "")
        raw_row = getattr(doc_or_candidate, "raw_row", None)
        return candidate_type == "listing_item" and (raw_row is not None or "row-" in getattr(doc_or_candidate, "candidate_id", ""))

    def parse(self, doc_or_candidate: Any) -> List[ParsedRFPItem]:
        title = getattr(doc_or_candidate, "title", "").strip()
        metadata = getattr(doc_or_candidate, "metadata", {})
        doc_urls = getattr(doc_or_candidate, "document_urls", [])
        source_url = getattr(doc_or_candidate, "source_url", "")
        content = getattr(doc_or_candidate, "normalized_content", "")

        ref_no = metadata.get("reference_number")
        deadline = metadata.get("submission_deadline")

        if not ref_no:
            # Check content for Reference Number:
            match = re.search(r"Reference\s*Number\s*[:=]\s*([^\n]+)", content, re.IGNORECASE)
            if match:
                ref_no = match.group(1).strip()

        if not deadline:
            match = re.search(r"(Submission\s*Deadline|Deadline|Closing\s*Date)\s*[:=]\s*([^\n]+)", content, re.IGNORECASE)
            if match:
                deadline = match.group(1).strip()

        item = ParsedRFPItem(
            title=title,
            reference_number=ref_no if ref_no else None,
            submission_deadline=deadline if deadline else None,
            description=content,
            document_urls=doc_urls,
            source_url=source_url,
            parser_name=self.name,
            confidence=0.85 if (ref_no and deadline) else 0.70,
        )

        return [item]

table_parser = TableParser()
