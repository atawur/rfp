from sqlalchemy import Column, Integer, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship, declared_attr

from app.db.base_class import Base

class NotificationPreference(Base):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return "notification_preference"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), unique=True, nullable=False)
    email_enabled = Column(Boolean, default=True)
    new_rfp_enabled = Column(Boolean, default=True)
    filters = Column(JSON, nullable=True) # e.g. keywords, categories

    user = relationship("User")
