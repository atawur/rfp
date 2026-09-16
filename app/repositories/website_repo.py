from typing import List, Union, Dict, Any
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.models.website import Website
from app.models.notification_receiver import NotificationReceiver
from app.schemas.website import WebsiteCreate, WebsiteUpdate


class WebsiteRepository(BaseRepository[Website, WebsiteCreate, WebsiteUpdate]):
    def get_active_websites(self, db: Session) -> List[Website]:
        return db.query(Website).filter(Website.status == "active").all()

    def create(self, db: Session, *, obj_in: WebsiteCreate) -> Website:
        obj_in_data = obj_in.model_dump()
        receiver_ids = obj_in_data.pop("receiver_ids", None)
        db_obj = self.model(**obj_in_data)
        if receiver_ids:
            receivers = db.query(NotificationReceiver).filter(NotificationReceiver.id.in_(receiver_ids)).all()
            db_obj.notification_receivers = receivers
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: Website, obj_in: Union[WebsiteUpdate, Dict[str, Any]]
    ) -> Website:
        if isinstance(obj_in, dict):
            update_data = obj_in.copy()
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        if "receiver_ids" in update_data:
            receiver_ids = update_data.pop("receiver_ids")
            if receiver_ids is not None:
                receivers = db.query(NotificationReceiver).filter(NotificationReceiver.id.in_(receiver_ids)).all()
                db_obj.notification_receivers = receivers

        for field in list(update_data.keys()):
            if hasattr(db_obj, field):
                setattr(db_obj, field, update_data[field])

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


website_repo = WebsiteRepository(Website)

