import logging
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.ai_agent_config import AIAgentConfig
from app.repositories.ai_agent_config_repo import ai_agent_config_repo
from app.schemas.ai_agent_config import AIAgentConfigCreate, AIAgentConfigUpdate
from app.agents.rfp_agent.agent import BaseRFPAgent, AgentFactory

logger = logging.getLogger(__name__)


class AgentConfigService:
    def list_configs(self, db: Session, skip: int = 0, limit: int = 100) -> List[AIAgentConfig]:
        self._ensure_initial_config_if_empty(db)
        return ai_agent_config_repo.get_multi(db, skip=skip, limit=limit)

    def get_config(self, db: Session, config_id: int) -> AIAgentConfig:
        config = ai_agent_config_repo.get(db, id=config_id)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AI Agent configuration not found",
            )
        return config

    def get_active_config(self, db: Session) -> Optional[AIAgentConfig]:
        self._ensure_initial_config_if_empty(db)
        active = ai_agent_config_repo.get_active(db)
        if not active:
            # Auto-recovery: if configs exist in database but none is active,
            # automatically activate the most recent valid configuration!
            candidates = (
                db.query(AIAgentConfig)
                .order_by(AIAgentConfig.id.desc())
                .all()
            )
            valid_candidate = next(
                (c for c in candidates if c.api_key and len(c.api_key.strip()) > 10 and c.api_key.strip() != "string"),
                candidates[0] if candidates else None
            )
            if valid_candidate:
                logger.info(
                    f"No active AI agent found, automatically restoring active status on config ID {valid_candidate.id} ('{valid_candidate.name}')"
                )
                valid_candidate.is_active = True
                db.commit()
                db.refresh(valid_candidate)
                return valid_candidate

        return active

    def create_config(self, db: Session, config_in: AIAgentConfigCreate) -> AIAgentConfig:
        if not config_in.api_key or not config_in.api_key.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A valid API key must be provided for the AI provider.",
            )

        provider_norm = config_in.provider.lower().strip()
        if provider_norm not in {"openai", "gemini"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid provider: '{config_in.provider}'. Supported providers are: 'openai', 'gemini'.",
            )

        # If marking this config active, deactivate others
        if config_in.is_active:
            db.query(AIAgentConfig).update({"is_active": False})
            db.commit()

        return ai_agent_config_repo.create(db, obj_in=config_in)

    def update_config(self, db: Session, config_id: int, config_in: AIAgentConfigUpdate) -> AIAgentConfig:
        existing = self.get_config(db, config_id=config_id)

        if config_in.provider is not None:
            provider_norm = config_in.provider.lower().strip()
            if provider_norm not in {"openai", "gemini"}:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid provider: '{config_in.provider}'. Supported providers are: 'openai', 'gemini'.",
                )

        if config_in.is_active:
            db.query(AIAgentConfig).filter(AIAgentConfig.id != config_id).update(
                {"is_active": False}, synchronize_session="fetch"
            )
            db.commit()

        return ai_agent_config_repo.update(db, db_obj=existing, obj_in=config_in)

    def activate_config(self, db: Session, config_id: int) -> AIAgentConfig:
        activated = ai_agent_config_repo.activate(db, config_id=config_id)
        if not activated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AI Agent configuration not found",
            )
        logger.info(f"Activated AI Agent configuration: {activated.name} ({activated.provider} - {activated.model_name})")
        return activated

    def delete_config(self, db: Session, config_id: int) -> AIAgentConfig:
        existing = self.get_config(db, config_id=config_id)
        was_active = bool(existing.is_active)
        removed = ai_agent_config_repo.remove(db, id=config_id)

        if was_active:
            # Automatically activate another remaining valid config if available
            remaining = (
                db.query(AIAgentConfig)
                .filter(AIAgentConfig.id != config_id)
                .order_by(AIAgentConfig.id.desc())
                .all()
            )
            valid_remaining = next(
                (c for c in remaining if c.api_key and len(c.api_key.strip()) > 10 and c.api_key.strip() != "string"),
                remaining[0] if remaining else None
            )
            if valid_remaining:
                valid_remaining.is_active = True
                db.commit()
                logger.info(
                    f"Deleted active config {config_id}, auto-activated remaining config {valid_remaining.id} ('{valid_remaining.name}')"
                )

        return removed

    def get_active_agent(self, db: Session) -> BaseRFPAgent:
        """
        Retrieves the active AI Agent configuration from the database,
        then uses AgentFactory to instantiate the concrete BaseRFPAgent strategy.
        """
        active_config = self.get_active_config(db)
        if not active_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active AI Agent configured in database. Please configure and activate an AI agent.",
            )

        return AgentFactory.create_agent(
            provider=active_config.provider,
            api_key=active_config.api_key,
            model_name=active_config.model_name,
            temperature=active_config.temperature,
            **(active_config.extra_params or {}),
        )

    def _ensure_initial_config_if_empty(self, db: Session) -> None:
        """
        If the ai_agent_config table is empty, seeds an initial active configuration
        using any available API key to ensure out-of-the-box operation.
        """
        count = db.query(AIAgentConfig).count()
        if count == 0 and settings.OPENAI_API_KEY:
            logger.info("Seeding initial OpenAI configuration into ai_agent_config table...")
            initial_config = AIAgentConfig(
                name="Default OpenAI GPT-4o",
                provider="openai",
                model_name="gpt-4o",
                api_key=settings.OPENAI_API_KEY,
                is_active=True,
                temperature=0.0,
            )
            db.add(initial_config)
            db.commit()
            db.refresh(initial_config)


agent_config_service = AgentConfigService()
