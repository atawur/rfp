from typing import Any, List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.ai_agent_config import (
    AIAgentConfigCreate,
    AIAgentConfigUpdate,
    AIAgentConfigResponse,
)
from app.services.agent_config_service import agent_config_service

router = APIRouter()


@router.get("/", response_model=List[AIAgentConfigResponse])
def read_agent_configs(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    List all configured AI agents.
    """
    return agent_config_service.list_configs(db, skip=skip, limit=limit)


@router.post("/", response_model=AIAgentConfigResponse)
def create_agent_config(
    *,
    db: Session = Depends(deps.get_db),
    config_in: AIAgentConfigCreate,
    current_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Register a new AI agent configuration (OpenAI or Gemini) with its API key.
    """
    return agent_config_service.create_config(db, config_in=config_in)


@router.get("/active", response_model=Optional[AIAgentConfigResponse])
def get_active_agent_config(
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get the currently active AI agent configuration.
    """
    return agent_config_service.get_active_config(db)


@router.get("/{config_id}", response_model=AIAgentConfigResponse)
def read_agent_config(
    config_id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get an AI agent configuration by ID.
    """
    return agent_config_service.get_config(db, config_id=config_id)


@router.put("/{config_id}", response_model=AIAgentConfigResponse)
def update_agent_config(
    config_id: int,
    config_in: AIAgentConfigUpdate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update an existing AI agent configuration.
    """
    return agent_config_service.update_config(db, config_id=config_id, config_in=config_in)


@router.post("/{config_id}/activate", response_model=AIAgentConfigResponse)
def activate_agent_config(
    config_id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Activate the specified AI agent configuration (sets this agent as active and deactivates all others).
    """
    return agent_config_service.activate_config(db, config_id=config_id)


@router.delete("/{config_id}", response_model=AIAgentConfigResponse)
def delete_agent_config(
    config_id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete an AI agent configuration.
    """
    return agent_config_service.delete_config(db, config_id=config_id)
