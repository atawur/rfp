import logging
from typing import List, Dict, Type, Any, Optional
from app.parsers.base import BaseExtractionParser
from app.parsers.jsonld_parser import jsonld_parser
from app.parsers.table_parser import table_parser
from app.parsers.generic_parser import generic_parser

logger = logging.getLogger(__name__)

class ParserRegistry:
    """
    Extensible Parser Registry that matches candidates against registered parsers:
    - Specific website parsers (highest priority)
    - JSON-LD parser
    - Table parser
    - Generic heuristic parser (fallback)
    """

    def __init__(self):
        self._parsers: List[BaseExtractionParser] = [
            jsonld_parser,
            table_parser,
            generic_parser,
        ]
        self._website_parsers: Dict[str, BaseExtractionParser] = {}

    def register_parser(self, parser: BaseExtractionParser, domain_or_name: Optional[str] = None):
        if domain_or_name:
            self._website_parsers[domain_or_name.lower()] = parser
        else:
            # Prepend before generic fallback
            self._parsers.insert(0, parser)
        logger.info(f"Registered extraction parser: {parser.name} (domain={domain_or_name})")

    def get_parser_for_candidate(self, candidate: Any) -> BaseExtractionParser:
        source_url = getattr(candidate, "source_url", "")
        # Check domain-specific parsers
        for domain, parser in self._website_parsers.items():
            if domain in source_url.lower():
                return parser

        # Check standard parsers in order of priority
        for parser in self._parsers:
            if parser.can_parse(candidate):
                return parser

        return generic_parser

parser_registry = ParserRegistry()
