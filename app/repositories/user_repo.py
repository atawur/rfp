from typing import Optional, List, Union, Dict, Any
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash

class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()
        
    def get_subscribed_users(self, db: Session) -> List[User]:
        return db.query(User).filter(User.notification_receive == True).all()
        
    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        db_obj = User(
            email=obj_in.email,
            name=obj_in.name,
            password_hash=get_password_hash(obj_in.password),
            status=obj_in.status,
            role_id=obj_in.role_id,
            notification_receive=bool(obj_in.notification_receive),
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        if isinstance(obj_in, dict):
            update_data = obj_in.copy()
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        if "password" in update_data:
            password = update_data.pop("password")
            if password:
                update_data["password_hash"] = get_password_hash(password)
        return super().update(db, db_obj=db_obj, obj_in=update_data)

user_repo = UserRepository(User)
