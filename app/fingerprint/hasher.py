import hashlib
import re
import urllib.parse
from typing import Optional

VOLATILE_PATTERNS = [
    re.compile(r"(page\s+generated|rendered|crawled|current\s+time|timestamp)[\s:=]+[^\n\r,;]+", re.IGNORECASE),
    re.compile(r"(csrf[-_]?token|session[-_]?id|request[-_]?id)[\s:=]+[^\n\r,;]+", re.IGNORECASE),
    re.compile(r"(copyright\s*©?\s*\d{4})", re.IGNORECASE),
]

TRACKING_QUERY_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "msclkid", "_ga", "_gl", "ref", "source", "sessionid",
    "timestamp", "nocache", "v",
}

class ContentFingerprinter:
    """
    Computes deterministic SHA-256 fingerprints for candidate RFP content and URLs.
    Ensures volatile noise (tracking IDs, transient timestamps, ads) does not invalidate hashes.
    """

    @staticmethod
    def normalize_url(raw_url: str) -> str:
        if not raw_url:
            return ""
        parsed = urllib.parse.urlparse(raw_url.strip())
        scheme = (parsed.scheme or "http").lower()
        netloc = parsed.netloc.lower()
        path = parsed.path or "/"

        # Filter out tracking params
        query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=False)
        clean_queries = [
            (k, v) for k, v in query_pairs
            if k.lower() not in TRACKING_QUERY_PARAMS
        ]
        clean_queries.sort(key=lambda x: x[0])
        clean_query = urllib.parse.urlencode(clean_queries)

        normalized = urllib.parse.urlunparse((scheme, netloc, path, parsed.params, clean_query, parsed.fragment))
        return normalized

    @staticmethod
    def canonicalize_content(content: str) -> str:
        if not content:
            return ""

        text = content
        for pattern in VOLATILE_PATTERNS:
            text = pattern.sub("", text)

        # Normalize unicode and whitespace
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
        clean_lines = [line for line in lines if line]
        canonical = "\n".join(clean_lines).strip().lower()
        return canonical

    @classmethod
    def compute_hash(cls, content: str) -> str:
        canonical = cls.canonicalize_content(content)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

content_fingerprinter = ContentFingerprinter()
