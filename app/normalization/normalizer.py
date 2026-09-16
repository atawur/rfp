import re
import urllib.parse
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup, Comment

DOC_EXTENSIONS = {
    "pdf": "pdf",
    "doc": "doc",
    "docx": "docx",
    "xls": "xls",
    "xlsx": "xlsx",
    "csv": "csv",
    "zip": "zip",
    "rar": "rar",
}

RFP_URL_KEYWORDS = {
    "rfp", "tender", "procurement", "proposal", "bid", "notice",
    "eoi", "quotation", "solicitation", "bidding", "auction"
}

RFP_TEXT_KEYWORDS = {
    "rfp", "request for proposal", "request for quotation", "rfq",
    "tender", "tender notice", "procurement", "proposal", "bid document",
    "download rfp", "download tender", "bidding document", "invitation for bids",
    "ifb", "expression of interest", "eoi", "invitation to tender", "itt"
}

NOISE_TAGS = ["script", "style", "noscript", "svg", "iframe", "canvas"]
NOISE_CLASSES_IDS = re.compile(
    r"(ad|ads|advert|banner|cookie|consent|tracking|social|share|nav|navigation|menu|footer|header|sidebar)",
    re.IGNORECASE
)

@dataclass
class NormalizedLink:
    text: str
    url: str
    type: str  # html, pdf, doc, docx, xls, xlsx, etc.
    is_rfp_signal: bool = False

@dataclass
class NormalizedPage:
    title: str
    headings: List[str]
    text: str
    semantic_sections: List[Dict[str, Any]]
    tables: List[List[List[str]]]
    metadata: Dict[str, Any]

@dataclass
class NormalizedDocument:
    source: Dict[str, str]  # {url, domain, website_name}
    page: NormalizedPage
    links: List[NormalizedLink]
    raw_relevant_text: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "page": {
                "title": self.page.title,
                "headings": self.page.headings,
                "text": self.page.text,
                "metadata": self.page.metadata,
            },
            "links": [
                {
                    "text": link.text,
                    "url": link.url,
                    "type": link.type,
                }
                for link in self.links
            ],
        }

    def to_compact_llm_payload(self) -> Dict[str, Any]:
        """Returns clean representation without boilerplate for LLM consumption."""
        return {
            "source": self.source,
            "page": {
                "title": self.page.title,
                "headings": self.page.headings[:15],
                "text": self.page.text[:12000],
                "metadata": {
                    k: v for k, v in self.page.metadata.items()
                    if k in {"description", "keywords", "author"}
                },
            },
            "links": [
                {
                    "text": link.text,
                    "url": link.url,
                    "type": link.type,
                }
                for link in self.links if link.is_rfp_signal or link.type != "html"
            ][:30],
        }


class GenericContentNormalizer:
    """
    Standardized, website-agnostic document normalizer that cleans raw HTML,
    resolves titles with hierarchical fallbacks, extracts semantic content,
    and classifies document links.
    """

    def clean_html(self, raw_html: str) -> BeautifulSoup:
        soup = BeautifulSoup(raw_html or "", "html.parser")

        # 1. Remove comments
        for comment in soup.find_all(string=lambda s: isinstance(s, Comment)):
            comment.extract()

        # 2. Remove script, style, noscript, etc.
        for tag in soup.find_all(NOISE_TAGS):
            tag.decompose()

        # 3. Remove prominent ad/cookie/nav banners
        for element in list(soup.find_all(True)):
            if not getattr(element, "attrs", None):
                continue

            # Preserve main semantic content even if it has classes like 'main-nav'
            if element.name in ["main", "article", "section", "table", "body", "html"]:
                continue

            element_role = str(element.attrs.get("role") or "").lower()
            if element_role in ["banner", "navigation", "complementary"] or element.name in ["nav", "footer", "header", "aside"]:
                element.decompose()
                continue

            class_val = " ".join(element.attrs.get("class", [])) if isinstance(element.attrs.get("class"), list) else str(element.attrs.get("class") or "")
            id_val = str(element.attrs.get("id") or "")

            if NOISE_CLASSES_IDS.search(class_val) or NOISE_CLASSES_IDS.search(id_val):
                # Only decompose if not containing an RFP link or table
                has_rfp_keyword = False
                text_preview = element.get_text()[:200].lower()
                for kw in ["tender", "rfp", "procurement"]:
                    if kw in text_preview:
                        has_rfp_keyword = True
                        break
                if not has_rfp_keyword:
                    element.decompose()

        return soup

    def extract_title(self, soup: BeautifulSoup, page_title: Optional[str] = None) -> str:
        """
        Dynamic fallback hierarchy for title extraction:
        1. <title>
        2. <h1>
        3. OpenGraph title (og:title)
        4. Twitter title (twitter:title)
        5. Useful metadata (meta description or first h2)
        6. Empty string
        """
        # 1. <title> tag
        title_tag = soup.find("title")
        if title_tag and title_tag.get_text(strip=True):
            clean = re.sub(r"\s+", " ", title_tag.get_text(strip=True))
            if clean:
                return clean

        # If page_title was supplied from Playwright page.title()
        if page_title and page_title.strip():
            clean = re.sub(r"\s+", " ", page_title.strip())
            if clean:
                return clean

        # 2. <h1> tag
        h1 = soup.find("h1")
        if h1 and h1.get_text(strip=True):
            clean = re.sub(r"\s+", " ", h1.get_text(strip=True))
            if clean:
                return clean

        # 3. OpenGraph title
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            clean = re.sub(r"\s+", " ", str(og_title.get("content")).strip())
            if clean:
                return clean

        # 4. Twitter title
        tw_title = soup.find("meta", attrs={"name": "twitter:title"})
        if tw_title and tw_title.get("content"):
            clean = re.sub(r"\s+", " ", str(tw_title.get("content")).strip())
            if clean:
                return clean

        # 5. First <h2> tag
        h2 = soup.find("h2")
        if h2 and h2.get_text(strip=True):
            clean = re.sub(r"\s+", " ", h2.get_text(strip=True))
            if clean:
                return clean

        return ""

    def extract_links(self, soup: BeautifulSoup, base_url: str) -> List[NormalizedLink]:
        links: List[NormalizedLink] = []
        seen_urls = set()

        for a in soup.find_all("a", href=True):
            raw_href = str(a.get("href") or "").strip()
            if not raw_href or raw_href.startswith(("#", "javascript:", "mailto:", "tel:")):
                continue

            absolute_url = urllib.parse.urljoin(base_url, raw_href)
            if absolute_url in seen_urls:
                continue
            seen_urls.add(absolute_url)

            link_text = re.sub(r"\s+", " ", a.get_text(strip=True))
            parsed = urllib.parse.urlparse(absolute_url)
            path = parsed.path.lower()

            doc_type = "html"
            for ext, typ in DOC_EXTENSIONS.items():
                if path.endswith(f".{ext}"):
                    doc_type = typ
                    break

            is_signal = False
            lower_text = link_text.lower()
            lower_url = absolute_url.lower()

            for kw in RFP_URL_KEYWORDS:
                if kw in lower_url:
                    is_signal = True
                    break

            if not is_signal:
                for kw in RFP_TEXT_KEYWORDS:
                    if kw in lower_text:
                        is_signal = True
                        break

            if doc_type != "html":
                is_signal = True

            links.append(NormalizedLink(
                text=link_text,
                url=absolute_url,
                type=doc_type,
                is_rfp_signal=is_signal,
            ))

        return links

    def extract_headings(self, soup: BeautifulSoup) -> List[str]:
        headings = []
        for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
            text = re.sub(r"\s+", " ", tag.get_text(strip=True))
            if text and len(text) > 2:
                headings.append(text)
        return headings

    def extract_tables(self, soup: BeautifulSoup) -> List[List[List[str]]]:
        tables_data = []
        for table in soup.find_all("table"):
            rows = []
            for tr in table.find_all("tr"):
                cells = [
                    re.sub(r"\s+", " ", cell.get_text(strip=True))
                    for cell in tr.find_all(["th", "td"])
                ]
                if any(cells):
                    rows.append(cells)
            if len(rows) > 1:
                tables_data.append(rows)
        return tables_data

    def extract_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        metadata: Dict[str, Any] = {}
        for meta in soup.find_all("meta"):
            name = meta.get("name") or meta.get("property")
            content = meta.get("content")
            if name and content:
                key = str(name).strip().lower()
                metadata[key] = str(content).strip()
        return metadata

    def extract_semantic_text(self, soup: BeautifulSoup) -> str:
        # Prefer main or article if present
        container = soup.find("main") or soup.find("article") or soup.find("div", {"id": re.compile(r"content|main", re.I)})
        if not container:
            container = soup.body or soup

        # Extract text with line breaks for paragraphs, list items, table rows
        lines = []
        for elem in container.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "tr", "dt", "dd"]):
            text = re.sub(r"\s+", " ", elem.get_text(strip=True))
            if text:
                lines.append(text)

        if not lines:
            raw_text = container.get_text(separator="\n", strip=True)
            lines = [re.sub(r"\s+", " ", l) for l in raw_text.split("\n") if l.strip()]

        return "\n".join(lines)

    def normalize(
        self,
        raw_html: str,
        source_url: str,
        page_title: Optional[str] = None,
        website_name: Optional[str] = None
    ) -> NormalizedDocument:
        parsed_url = urllib.parse.urlparse(source_url)
        domain = parsed_url.netloc or ""
        site_name = website_name or domain

        soup = self.clean_html(raw_html)
        title = self.extract_title(soup, page_title)
        headings = self.extract_headings(soup)
        links = self.extract_links(soup, source_url)
        tables = self.extract_tables(soup)
        metadata = self.extract_metadata(soup)
        text = self.extract_semantic_text(soup)

        page = NormalizedPage(
            title=title,
            headings=headings,
            text=text,
            semantic_sections=[],
            tables=tables,
            metadata=metadata,
        )

        return NormalizedDocument(
            source={
                "url": source_url,
                "domain": domain,
                "website_name": site_name,
            },
            page=page,
            links=links,
            raw_relevant_text=f"{title}\n\n{text}",
        )

generic_normalizer = GenericContentNormalizer()
