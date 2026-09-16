from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.base_class import Base

class ContentFingerprint(Base):
    __tablename__ = "content_fingerprint"

    id = Column(Integer, primary_key=True, index=True)
    source_url = Column(String, index=True, nullable=False)
    normalized_url = Column(String, index=True, nullable=False)
    content_hash = Column(String(64), index=True, nullable=False)
    website_id = Column(Integer, ForeignKey("website.id"), nullable=True, index=True)
    rfp_id = Column(Integer, ForeignKey("rfp.id"), nullable=True, index=True)
    extraction_version = Column(Integer, default=1, nullable=False)
    parser_version = Column(Integer, default=1, nullable=False)
    first_seen_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_seen_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_processed_at = Column(DateTime(timezone=True), nullable=True)
