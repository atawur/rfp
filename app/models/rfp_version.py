from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship, declared_attr
from sqlalchemy.sql import func

from app.db.base_class import Base

class RFPVersion(Base):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return "rfp_version"

    id = Column(Integer, primary_key=True, index=True)
    rfp_id = Column(Integer, ForeignKey("rfp.id"), nullable=False)
    version_no = Column(Integer, nullable=False)
    snapshot = Column(JSON, nullable=False)
    content_hash = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    rfp = relationship("RFP", back_populates="versions")
