from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base

class Notification(Base):
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    receiver_id = Column(Integer, ForeignKey("notification_receiver.id", ondelete="SET NULL"), nullable=True)
    rfp_id = Column(Integer, ForeignKey("rfp.id"), nullable=True)
    type = Column(String, nullable=False) # e.g. "NEW_RFP"
    status = Column(String, default="PENDING") # PENDING, QUEUED, SENT, FAILED
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    sent_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User")
    receiver = relationship("NotificationReceiver")
    rfp = relationship("RFP")

