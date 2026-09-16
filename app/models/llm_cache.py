from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from app.db.base_class import Base

class LLMCache(Base):
    __tablename__ = "llm_cache"

    id = Column(Integer, primary_key=True, index=True)
    cache_key = Column(String(64), unique=True, index=True, nullable=False)
    content_hash = Column(String(64), index=True, nullable=False)
    prompt_version = Column(Integer, default=1, nullable=False)
    schema_version = Column(Integer, default=1, nullable=False)
    model_name = Column(String, index=True, nullable=False)
    response_json = Column(JSON, nullable=False)
    input_tokens = Column(Integer, default=0, nullable=False)
    output_tokens = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
