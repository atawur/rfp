from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship, declared_attr
from sqlalchemy.sql import func

from app.db.base_class import Base

class AuditLog(Base):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    action = Column(String, nullable=False) # e.g. "CREATE", "UPDATE", "DELETE", "LOGIN"
    entity_type = Column(String, nullable=False) # e.g. "USER", "RFP", "WEBSITE"
    entity_id = Column(String, nullable=True)
    metadata_info = Column(JSON, nullable=True) # Changed from 'metadata' as it's reserved by SQLAlchemy
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    actor = relationship("User")
