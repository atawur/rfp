from typing import List, Optional
from pydantic import BaseModel, Field

class RFPExtractionSchema(BaseModel):
    title: str = Field(description="The title of the RFP/tender")
    reference_number: str = Field(default="", description="Reference or tracking number")
    organization: str = Field(default="", description="The issuing organization")
    description: str = Field(default="", description="Short description or summary of the RFP")
    published_date: Optional[str] = Field(default=None, description="ISO format published date")
    submission_deadline: Optional[str] = Field(default=None, description="ISO format deadline, carefully extract this from text like 'Date of submission: ...'")
    estimated_budget: Optional[float] = Field(default=None, description="Estimated budget if available")
    currency: Optional[str] = Field(default=None, description="Currency of the budget")
    location: Optional[str] = Field(default=None, description="Location for the work or organization")
    category: Optional[str] = Field(default=None, description="Category/Industry of the RFP")
    primary_category: Optional[str] = Field(
        default=None,
        description="Dominant procurement category chosen strictly from: software, hardware, it_services, telecommunications, cybersecurity, cloud, professional_services, construction, healthcare, transportation, security, office_supplies, education, other",
    )
    sub_category: Optional[str] = Field(
        default="general",
        description="Specific granular subcategory (e.g. 'virtualization', 'networking_equipment', 'web_development')",
    )
    procurement_type: Optional[str] = Field(
        default="service",
        description="Procurement nature: product, service, software_license, subscription, consulting, implementation, maintenance, mixed, other",
    )
    secondary_categories: List[str] = Field(
        default_factory=list,
        description="Materially important additional categories from the taxonomy if applicable",
    )
    keywords: List[str] = Field(
        default_factory=list,
        description="Relevant extracted domain keywords indicating why this category was selected",
    )
    short_reason: Optional[str] = Field(
        default=None,
        description="Concise justification of the category classification based on primary procurement objective",
    )
    eligibility: List[str] = Field(default_factory=list, description="List of eligibility requirements")
    requirements: List[str] = Field(default_factory=list, description="List of technical/business requirements")
    submission_method: Optional[str] = Field(default=None, description="How to submit the proposal")
    contact_person: Optional[str] = Field(default=None, description="Name of contact person")
    contact_email: Optional[str] = Field(default=None, description="Email of contact person")
    contact_phone: Optional[str] = Field(default=None, description="Phone of contact person")
    documents: List[str] = Field(default_factory=list, description="List of related documents or attachments")
    source_url: str = Field(description="The source URL")
    confidence: float = Field(default=0.0, description="Confidence score between 0.0 and 1.0")
    validation_flags: List[str] = Field(default_factory=list, description="Any ambiguities or flags")

class RFPExtractionListSchema(BaseModel):
    rfps: List[RFPExtractionSchema] = Field(description="A comprehensive list of all RFPs found on the page.")
