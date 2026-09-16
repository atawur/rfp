from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Table, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base

website_notification_receivers = Table(
    "website_notification_receivers",
    Base.metadata,
    Column("website_id", Integer, ForeignKey("website.id", ondelete="CASCADE"), primary_key=True),
    Column("receiver_id", Integer, ForeignKey("notification_receiver.id", ondelete="CASCADE"), primary_key=True),
)

class Website(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    base_url = Column(String, nullable=False)
    start_url = Column(String, nullable=False)
    status = Column(String, default="active") # active, inactive, testing
    crawl_frequency = Column(String, default="daily")
    config = Column(JSON, nullable=True) # Site-specific config if generic fails
    notify_all_receivers = Column(Boolean, default=True, server_default="true", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    rfps = relationship("RFP", back_populates="website")
    crawl_runs = relationship("CrawlRun", back_populates="website")
    notification_receivers = relationship(
        "NotificationReceiver",
        secondary=website_notification_receivers,
        back_populates="websites",
    )

