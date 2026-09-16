from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship, declared_attr
from sqlalchemy.sql import func

from app.db.base_class import Base

class EmailLog(Base):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return "email_log"

    id = Column(Integer, primary_key=True, index=True)
    notification_id = Column(Integer, ForeignKey("notification.id"), nullable=False)
    provider = Column(String, nullable=True) # e.g. "SES", "Console"
    status = Column(String, nullable=False)
    attempts = Column(Integer, default=1)
    error = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    notification = relationship("Notification")
