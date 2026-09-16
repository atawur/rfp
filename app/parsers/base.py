from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass
class ParsedRFPItem:
    title: str
    reference_number: Optional[str] = None
    organization: Optional[str] = None
    description: Optional[str] = None
    published_date: Optional[str] = None
    submission_deadline: Optional[str] = None
    estimated_budget: Optional[float] = None
    currency: Optional[str] = None
    location: Optional[str] = None
    contact_person: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    submission_method: Optional[str] = None
    document_urls: List[str] = field(default_factory=list)
    eligibility: List[str] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)
    source_url: str = ""
    parser_name: str = "generic"
    confidence: float = 0.0
    primary_category: Optional[str] = None
    sub_category: Optional[str] = None
    procurement_type: Optional[str] = None
    category_confidence: float = 0.0
    keywords: List[str] = field(default_factory=list)
    short_reason: Optional[str] = None
    validation_flags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "reference_number": self.reference_number or "",
            "organization": self.organization or "",
            "description": self.description or "",
            "published_date": self.published_date,
            "submission_deadline": self.submission_deadline,
            "estimated_budget": self.estimated_budget,
            "currency": self.currency,
            "location": self.location,
            "contact_person": self.contact_person,
            "contact_email": self.contact_email,
            "contact_phone": self.contact_phone,
            "submission_method": self.submission_method,
            "documents": self.document_urls,
            "eligibility": self.eligibility,
            "requirements": self.requirements,
            "source_url": self.source_url,
            "confidence": self.confidence,
            "primary_category": self.primary_category,
            "sub_category": self.sub_category or "general",
            "procurement_type": self.procurement_type or "service",
            "category_confidence": self.category_confidence,
            "keywords": self.keywords,
            "short_reason": self.short_reason or "Deterministically classified",
            "validation_flags": self.validation_flags,
        }

class BaseExtractionParser(ABC):
    """Abstract interface for all deterministic and custom website parsers."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def can_parse(self, doc_or_candidate: Any) -> bool:
        """Determines whether this parser can extract data from the given candidate/document."""
        pass

    @abstractmethod
    def parse(self, doc_or_candidate: Any) -> List[ParsedRFPItem]:
        """Extracts structured RFP items deterministically."""
        pass
