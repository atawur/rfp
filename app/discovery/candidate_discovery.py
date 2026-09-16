import re
import urllib.parse
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from app.normalization.normalizer import NormalizedDocument, NormalizedLink

@dataclass
class RFPCandidate:
    candidate_id: str
    source_url: str
    candidate_type: str  # "individual_page" | "listing_item"
    title: str
    normalized_content: str
    document_urls: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw_row: Optional[List[str]] = None

class CandidateDiscoveryService:
    """
    Separates candidate discovery from extraction.
    Identifies whether a normalized document contains individual RFP candidates
    (e.g. from procurement tables, tender lists) or is a single dedicated RFP page.
    Enables RFP-level hashing and change detection.
    """

    PROCUREMENT_HEADER_TERMS = {
        "title", "tender", "rfp", "description", "subject", "name",
        "deadline", "closing", "due date", "submission", "opening",
        "reference", "ref no", "tender no", "solicitation", "document", "download"
    }

    def _is_procurement_table(self, table: List[List[str]]) -> bool:
        if not table or len(table) < 2:
            return False
        header = " ".join(table[0]).lower()
        matches = sum(1 for term in self.PROCUREMENT_HEADER_TERMS if term in header)
        return matches >= 2

    def _extract_candidates_from_tables(
        self,
        doc: NormalizedDocument
    ) -> List[RFPCandidate]:
        candidates: List[RFPCandidate] = []
        base_url = doc.source.get("url", "")

        for table_idx, table in enumerate(doc.page.tables):
            if not self._is_procurement_table(table):
                continue

            header_row = [c.lower() for c in table[0]]
            title_col = -1
            ref_col = -1
            deadline_col = -1

            for col_idx, col_name in enumerate(header_row):
                if any(t in col_name for t in ["title", "tender", "description", "subject", "name"]):
                    if title_col == -1:
                        title_col = col_idx
                if any(t in col_name for t in ["ref", "number", "no."]):
                    ref_col = col_idx
                if any(t in col_name for t in ["deadline", "closing", "due", "submission"]):
                    deadline_col = col_idx

            if title_col == -1:
                title_col = 0

            for row_idx, row in enumerate(table[1:], start=1):
                if len(row) <= title_col or not row[title_col].strip():
                    continue

                candidate_title = row[title_col].strip()
                if len(candidate_title) < 4:
                    continue

                ref_val = row[ref_col].strip() if (ref_col != -1 and len(row) > ref_col) else ""
                deadline_val = row[deadline_col].strip() if (deadline_col != -1 and len(row) > deadline_col) else ""

                # Construct clean normalized text snippet for this specific table item
                row_text_parts = [f"Title: {candidate_title}"]
                if ref_val:
                    row_text_parts.append(f"Reference Number: {ref_val}")
                if deadline_val:
                    row_text_parts.append(f"Submission Deadline: {deadline_val}")

                other_cells = [
                    f"{header_row[i]}: {cell}" for i, cell in enumerate(row)
                    if i not in [title_col, ref_col, deadline_col] and i < len(header_row) and cell.strip()
                ]
                row_text_parts.extend(other_cells)
                item_content = "\n".join(row_text_parts)

                # Match candidate links
                item_links = []
                for link in doc.links:
                    if link.text and (link.text.lower() in candidate_title.lower() or candidate_title.lower() in link.text.lower()):
                        item_links.append(link.url)
                    elif ref_val and ref_val.lower() in link.url.lower():
                        item_links.append(link.url)

                cid = f"{base_url}#row-{table_idx}-{row_idx}"
                candidates.append(RFPCandidate(
                    candidate_id=cid,
                    source_url=base_url,
                    candidate_type="listing_item",
                    title=candidate_title,
                    normalized_content=item_content,
                    document_urls=item_links,
                    metadata={
                        "reference_number": ref_val,
                        "submission_deadline": deadline_val,
                        "table_index": table_idx,
                        "row_index": row_idx,
                    },
                    raw_row=row,
                ))

        return candidates

    def _extract_candidates_from_links(
        self,
        doc: NormalizedDocument
    ) -> List[RFPCandidate]:
        candidates: List[RFPCandidate] = []
        base_url = doc.source.get("url", "")

        rfp_links = [l for l in doc.links if l.is_rfp_signal and len(l.text) >= 6]
        if len(rfp_links) >= 3:
            # We are on a directory/listing of RFPs
            for idx, link in enumerate(rfp_links):
                item_content = f"Title: {link.text}\nURL: {link.url}\nType: {link.type}"
                candidates.append(RFPCandidate(
                    candidate_id=link.url,
                    source_url=link.url,
                    candidate_type="listing_item",
                    title=link.text,
                    normalized_content=item_content,
                    document_urls=[link.url] if link.type != "html" else [],
                    metadata={"link_type": link.type},
                ))

        return candidates

    def discover_candidates(self, doc: NormalizedDocument) -> List[RFPCandidate]:
        """
        Discovers RFP candidates from a normalized document.
        Prefers fine-grained RFP-level candidates for listing pages,
        and falls back to page-level candidate for dedicated RFP detail pages.
        """
        # 1. Check for procurement tables (e.g., City Bank or government portal lists)
        table_candidates = self._extract_candidates_from_tables(doc)
        if table_candidates:
            return table_candidates

        # 2. Check for distinct RFP link listings
        link_candidates = self._extract_candidates_from_links(doc)
        if link_candidates:
            return link_candidates

        # 3. Fallback: Treat as a single individual RFP page
        base_url = doc.source.get("url", "")
        doc_urls = [l.url for l in doc.links if l.type != "html"]
        title = doc.page.title or "Untitled Procurement Notice"

        if doc.page.headings:
            first_h = doc.page.headings[0].strip()
            if len(first_h) >= 8 and (
                any(w in title.lower() for w in ["portal", "home", "website", "tenders", "procurement", "official", "welcome"])
                or len(title) < 10
            ):
                title = first_h

        return [
            RFPCandidate(
                candidate_id=base_url,
                source_url=base_url,
                candidate_type="individual_page",
                title=title,
                normalized_content=doc.raw_relevant_text,
                document_urls=doc_urls,
                metadata=doc.page.metadata,
            )
        ]

candidate_discovery_service = CandidateDiscoveryService()
