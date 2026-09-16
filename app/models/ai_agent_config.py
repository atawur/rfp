from sqlalchemy import Column, Integer, String, Boolean, Float, JSON, DateTime
from sqlalchemy.orm import declared_attr
from sqlalchemy.sql import func
from app.db.base_class import Base


class AIAgentConfig(Base):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return "ai_agent_config"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    provider = Column(String, index=True, nullable=False)  # "openai", "gemini"
    model_name = Column(String, nullable=False)  # e.g. "gpt-4o", "gemini-2.5-flash"
    api_key = Column(String, nullable=False)  # API key stored in DB
    is_active = Column(Boolean, default=False, nullable=False, index=True)
    temperature = Column(Float, default=0.0, nullable=False)
    extra_params = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
