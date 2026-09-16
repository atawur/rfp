from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base

class CrawlRun(Base):
    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("website.id"), nullable=False)
    status = Column(String, default="running") # running, completed, failed
    metrics = Column(JSON, nullable=True) # candidates_found, new_rfps, updated_rfps
    error = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    website = relationship("Website", back_populates="crawl_runs")
