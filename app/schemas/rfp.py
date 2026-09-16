from typing import Optional, List, Any
from pydantic import BaseModel
from datetime import datetime, date

class RFPBase(BaseModel):
    title: str
    external_rfp_id: Optional[str] = None
    reference_number: Optional[str] = None
    organization: Optional[str] = None
    description: Optional[str] = None
    published_date: Optional[date] = None
    submission_deadline: Optional[date] = None
    estimated_budget: Optional[float] = None
    currency: Optional[str] = None
    location: Optional[str] = None
    eligibility: Optional[Any] = None
    requirements: Optional[Any] = None
    submission_method: Optional[str] = None
    contact_person: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    source_url: str
    status: Optional[str] = "NEW"
    website_id: Optional[int] = None
    website_name: Optional[str] = None

    # AI Classification Fields
    primary_category: Optional[str] = None
    sub_category: Optional[str] = None
    procurement_type: Optional[str] = None
    confidence: Optional[float] = None
    keywords: Optional[List[str]] = None
    secondary_categories: Optional[List[str]] = None
    classification_reason: Optional[str] = None
    classified_at: Optional[datetime] = None
    classification_model: Optional[str] = None
    classification_status: Optional[str] = "pending"
    classification_attempts: Optional[int] = 0

class RFPCreate(RFPBase):
    pass

class RFPUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    # Add other fields as necessary

class RFPInDBBase(RFPBase):
    id: int
    content_hash: Optional[str] = None
    first_seen_at: datetime
    last_seen_at: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class RFP(RFPInDBBase):
    pass


class PaginatedRFPResponse(BaseModel):
    items: List[RFP]
    total: int
    page: int
    size: int
    pages: int


class RFPImportURLRequest(BaseModel):
    url: str


class RFPProcessResult(BaseModel):
    status: str
    title: Optional[str] = None
    reason: Optional[str] = None
    id: Optional[int] = None


class RFPImportResponse(BaseModel):
    message: str
    results: List[RFPProcessResult]
