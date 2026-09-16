from sqlalchemy import Column, Integer, String, Date, Float, JSON, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from app.db.base_class import Base

class RFP(Base):
    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("website.id"), nullable=True)
    external_rfp_id = Column(String, index=True, nullable=True)
    title = Column(String, index=True, nullable=False)
    reference_number = Column(String, index=True, nullable=True)
    organization = Column(String, index=True, nullable=True)
    description = Column(Text, nullable=True)
    published_date = Column(Date, nullable=True)
    submission_deadline = Column(Date, nullable=True)
    estimated_budget = Column(Float, nullable=True)
    currency = Column(String, nullable=True)
    location = Column(String, nullable=True)
    eligibility = Column(JSON, nullable=True)
    requirements = Column(JSON, nullable=True)
    submission_method = Column(String, nullable=True)
    contact_person = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    source_url = Column(String, nullable=False)
    normalized_url = Column(String, nullable=True)
    status = Column(String, default="NEW")
    content_hash = Column(String, nullable=True)
    embedding = Column(Vector(384), nullable=True)
    extraction_method = Column(String, default="deterministic", nullable=True)
    parser_version = Column(Integer, default=1, nullable=True)
    extraction_version = Column(Integer, default=1, nullable=True)
    first_seen_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen_at = Column(DateTime(timezone=True), server_default=func.now())
    last_processed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # AI Classification Fields
    primary_category = Column(String, index=True, nullable=True)
    sub_category = Column(String, index=True, nullable=True)
    procurement_type = Column(String, index=True, nullable=True)
    confidence = Column(Float, nullable=True)
    keywords = Column(JSON, nullable=True)
    secondary_categories = Column(JSON, nullable=True)
    classification_reason = Column(Text, nullable=True)
    classified_at = Column(DateTime(timezone=True), nullable=True)
    classification_model = Column(String, nullable=True)
    classification_status = Column(String, default="pending", index=True, nullable=True)
    classification_attempts = Column(Integer, default=0, nullable=False)

    website = relationship("Website", back_populates="rfps")
    documents = relationship("RFPDocument", back_populates="rfp")
    versions = relationship("RFPVersion", back_populates="rfp")
    changes = relationship("RFPChange", back_populates="rfp")

    @property
    def website_name(self):
        return self.website.name if self.website else None

