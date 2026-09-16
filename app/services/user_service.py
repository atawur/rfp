from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.user_repo import user_repo
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    def get_users(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        return user_repo.get_multi(db, skip=skip, limit=limit)

    def get_user_by_id(self, db: Session, user_id: int) -> Optional[User]:
        return user_repo.get(db, id=user_id)

    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        return user_repo.get_by_email(db, email=email)

    def create_user(self, db: Session, user_in: UserCreate) -> User:
        user = user_repo.get_by_email(db, email=user_in.email)
        if user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The user with this username already exists in the system.",
            )
        return user_repo.create(db, obj_in=user_in)

    def update_user(self, db: Session, user_id: int, user_in: UserUpdate) -> User:
        user = user_repo.get(db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        if user_in.email and user_in.email != user.email:
            existing = user_repo.get_by_email(db, email=user_in.email)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A user with this email already exists.",
                )
        return user_repo.update(db, db_obj=user, obj_in=user_in)

    def get_user_me(self, current_user: User) -> User:
        return current_user


user_service = UserService()
