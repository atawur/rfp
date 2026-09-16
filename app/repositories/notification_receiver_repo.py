from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.models.notification_receiver import NotificationReceiver
from app.schemas.notification_receiver import NotificationReceiverCreate, NotificationReceiverUpdate


class NotificationReceiverRepository(
    BaseRepository[NotificationReceiver, NotificationReceiverCreate, NotificationReceiverUpdate]
):
    def get_by_email(self, db: Session, email: str) -> Optional[NotificationReceiver]:
        return db.query(NotificationReceiver).filter(NotificationReceiver.email == email).first()

    def get_active_receivers(self, db: Session) -> List[NotificationReceiver]:
        return db.query(NotificationReceiver).filter(NotificationReceiver.status == "active").all()


notification_receiver_repo = NotificationReceiverRepository(NotificationReceiver)
