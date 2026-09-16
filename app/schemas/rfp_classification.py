from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator

AllowedPrimaryCategory = Literal[
    "software",
    "hardware",
    "it_services",
    "telecommunications",
    "cybersecurity",
    "cloud",
    "professional_services",
    "construction",
    "healthcare",
    "transportation",
    "security",
    "office_supplies",
    "education",
    "other",
]

ALLOWED_PRIMARY_CATEGORIES: set[str] = {
    "software",
    "hardware",
    "it_services",
    "telecommunications",
    "cybersecurity",
    "cloud",
    "professional_services",
    "construction",
    "healthcare",
    "transportation",
    "security",
    "office_supplies",
    "education",
    "other",
}

AllowedProcurementType = Literal[
    "product",
    "service",
    "software_license",
    "subscription",
    "consulting",
    "implementation",
    "maintenance",
    "mixed",
    "other",
]

ALLOWED_PROCUREMENT_TYPES: set[str] = {
    "product",
    "service",
    "software_license",
    "subscription",
    "consulting",
    "implementation",
    "maintenance",
    "mixed",
    "other",
}


class RFPClassificationResult(BaseModel):
    """
    Structured response and validation model for AI-based RFP category classification.
    """
    primary_category: AllowedPrimaryCategory = Field(
        description="The dominant procurement category chosen strictly from the allowed taxonomy."
    )
    secondary_categories: List[AllowedPrimaryCategory] = Field(
        default_factory=list,
        description="Materially important additional categories from the taxonomy (if applicable).",
    )
    sub_category: str = Field(
        default="general",
        description="Specific granular subcategory (e.g., 'computers', 'networking_equipment', 'web_development').",
    )
    procurement_type: AllowedProcurementType = Field(
        description="Procurement nature: product, service, software_license, subscription, consulting, implementation, maintenance, mixed, or other.",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Model confidence score strictly between 0.0 and 1.0.",
    )
    keywords: List[str] = Field(
        default_factory=list,
        description="Relevant extracted domain keywords indicating why this category was selected.",
    )
    short_reason: str = Field(
        ...,
        description="Concise justification of the classification based on primary procurement objective.",
    )

    @field_validator("primary_category", mode="before")
    @classmethod
    def validate_primary_category(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError(f"primary_category must be a string, got {type(v)}")
        norm_v = v.strip().lower().replace(" ", "_").replace("-", "_")
        if norm_v not in ALLOWED_PRIMARY_CATEGORIES:
            raise ValueError(
                f"primary_category '{v}' is not in allowed taxonomy: {sorted(ALLOWED_PRIMARY_CATEGORIES)}"
            )
        return norm_v

    @field_validator("secondary_categories", mode="before")
    @classmethod
    def validate_secondary_categories(cls, v: any) -> List[str]:
        if not v:
            return []
        if not isinstance(v, list):
            raise ValueError("secondary_categories must be a list")
        validated: List[str] = []
        for item in v:
            if not isinstance(item, str):
                continue
            norm_item = item.strip().lower().replace(" ", "_").replace("-", "_")
            if norm_item in ALLOWED_PRIMARY_CATEGORIES:
                validated.append(norm_item)
            else:
                raise ValueError(
                    f"secondary category '{item}' is not in allowed taxonomy: {sorted(ALLOWED_PRIMARY_CATEGORIES)}"
                )
        return validated

    @field_validator("procurement_type", mode="before")
    @classmethod
    def validate_procurement_type(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError(f"procurement_type must be a string, got {type(v)}")
        norm_v = v.strip().lower().replace(" ", "_").replace("-", "_")
        if norm_v not in ALLOWED_PROCUREMENT_TYPES:
            raise ValueError(
                f"procurement_type '{v}' is not in allowed types: {sorted(ALLOWED_PROCUREMENT_TYPES)}"
            )
        return norm_v

    @field_validator("keywords", mode="before")
    @classmethod
    def validate_keywords(cls, v: any) -> List[str]:
        if not v:
            return []
        if isinstance(v, list):
            return [str(item).strip() for item in v if str(item).strip()]
        return [str(v).strip()]
