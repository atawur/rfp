from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base


class NotificationReceiver(Base):
    __tablename__ = "notification_receiver"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    email = Column(String, index=True, nullable=False)
    designation = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    status = Column(String, default="active", nullable=False)  # "active", "inactive"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


    websites = relationship(
        "Website",
        secondary="website_notification_receivers",
        back_populates="notification_receivers",
    )
