from typing import Optional, List
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.models.ai_agent_config import AIAgentConfig
from app.schemas.ai_agent_config import AIAgentConfigCreate, AIAgentConfigUpdate


class AIAgentConfigRepository(BaseRepository[AIAgentConfig, AIAgentConfigCreate, AIAgentConfigUpdate]):
    def get_active(self, db: Session) -> Optional[AIAgentConfig]:
        """
        Retrieves the single currently active AI agent configuration.
        """
        return db.query(AIAgentConfig).filter(AIAgentConfig.is_active == True).first()

    def activate(self, db: Session, *, config_id: int) -> Optional[AIAgentConfig]:
        """
        Activates the specified configuration and deactivates all others.
        """
        target = db.query(AIAgentConfig).filter(AIAgentConfig.id == config_id).first()
        if not target:
            return None

        # Deactivate all other configs
        db.query(AIAgentConfig).filter(AIAgentConfig.id != config_id).update(
            {"is_active": False}, synchronize_session="fetch"
        )

        target.is_active = True
        db.commit()
        db.refresh(target)
        return target

    def get_by_name(self, db: Session, *, name: str) -> Optional[AIAgentConfig]:
        return db.query(AIAgentConfig).filter(AIAgentConfig.name == name).first()


ai_agent_config_repo = AIAgentConfigRepository(AIAgentConfig)
