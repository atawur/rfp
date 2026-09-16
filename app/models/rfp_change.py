from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship, declared_attr
from sqlalchemy.sql import func

from app.db.base_class import Base

class RFPChange(Base):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return "rfp_change"

    id = Column(Integer, primary_key=True, index=True)
    rfp_id = Column(Integer, ForeignKey("rfp.id"), nullable=False)
    versions = Column(String, nullable=False) # e.g. "1->2"
    field = Column(String, nullable=False)
    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    detected_at = Column(DateTime(timezone=True), server_default=func.now())

    rfp = relationship("RFP", back_populates="changes")
