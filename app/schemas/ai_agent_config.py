from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, computed_field


class AIAgentConfigBase(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    name: str = Field(description="Human-readable configuration name")
    provider: str = Field(description="AI provider: 'openai' or 'gemini'")
    model_name: str = Field(description="Model identifier, e.g. 'gpt-4o', 'gemini-2.5-flash'")
    temperature: float = Field(default=0.0, description="Sampling temperature between 0.0 and 1.0")
    extra_params: Optional[Dict[str, Any]] = Field(default=None, description="Optional extra parameters")


class AIAgentConfigCreate(AIAgentConfigBase):
    api_key: str = Field(description="Secret API key for the AI provider")
    is_active: bool = Field(default=False, description="Whether this agent is immediately active")


class AIAgentConfigUpdate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    name: Optional[str] = None
    provider: Optional[str] = None
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    is_active: Optional[bool] = None
    temperature: Optional[float] = None
    extra_params: Optional[Dict[str, Any]] = None


class AIAgentConfigResponse(AIAgentConfigBase):
    id: int
    is_active: bool
    api_key: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    @computed_field  # type: ignore[misc]
    @property
    def api_key_masked(self) -> str:
        key = self.api_key or ""
        if len(key) <= 8:
            return "******"
        return f"{key[:4]}...{key[-4:]}"
