import json
import logging
from typing import List, Any
from bs4 import BeautifulSoup
from app.parsers.base import BaseExtractionParser, ParsedRFPItem

logger = logging.getLogger(__name__)

class JSONLDParser(BaseExtractionParser):
    @property
    def name(self) -> str:
        return "json_ld"

    def can_parse(self, doc_or_candidate: Any) -> bool:
        raw_html = getattr(doc_or_candidate, "raw_html", "") or getattr(doc_or_candidate, "normalized_content", "")
        return "application/ld+json" in raw_html

    def parse(self, doc_or_candidate: Any) -> List[ParsedRFPItem]:
        raw_html = getattr(doc_or_candidate, "raw_html", "") or getattr(doc_or_candidate, "normalized_content", "")
        source_url = getattr(doc_or_candidate, "source_url", "")

        soup = BeautifulSoup(raw_html, "html.parser")
        items: List[ParsedRFPItem] = []

        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "{}")
                if isinstance(data, list):
                    nodes = data
                else:
                    nodes = [data]

                for node in nodes:
                    if not isinstance(node, dict):
                        continue

                    title = node.get("name") or node.get("headline") or node.get("title")
                    if not title or len(str(title).strip()) < 5:
                        continue

                    desc = node.get("description") or ""
                    ref_no = node.get("identifier") or node.get("serialNumber") or ""
                    deadline = node.get("endDate") or node.get("expires")
                    published = node.get("startDate") or node.get("datePublished")
                    org_info = node.get("organizer") or node.get("provider") or node.get("publisher") or {}
                    org_name = org_info.get("name", "") if isinstance(org_info, dict) else str(org_info)

                    items.append(ParsedRFPItem(
                        title=str(title).strip(),
                        reference_number=str(ref_no).strip() if ref_no else None,
                        organization=str(org_name).strip() if org_name else None,
                        description=str(desc).strip() if desc else None,
                        published_date=str(published)[:10] if published else None,
                        submission_deadline=str(deadline)[:10] if deadline else None,
                        source_url=source_url,
                        parser_name=self.name,
                        confidence=0.85,
                    ))
            except Exception as e:
                logger.debug(f"Failed to parse JSON-LD script: {e}")

        return items

jsonld_parser = JSONLDParser()
