from datetime import timedelta
from typing import Optional
from fastapi import HTTPException, status
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core import security
from app.core.config import settings
from app.models.user import User
from app.repositories.user_repo import user_repo
from app.schemas.token import Token, TokenPayload


class AuthService:
    def authenticate(self, db: Session, email: str, password: str) -> Optional[User]:
        user = user_repo.get_by_email(db, email=email)
        if not user:
            return None
        if not security.verify_password(password, user.password_hash):
            return None
        return user

    def login_access_token(self, db: Session, username: str, password: str) -> Token:
        user = self.authenticate(db, email=username, password=password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect email or password",
            )
        elif user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user",
            )

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        return Token(
            access_token=security.create_access_token(
                user.id, expires_delta=access_token_expires
            ),
            token_type="bearer",
        )

    def get_user_from_token(self, db: Session, token: str) -> User:
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=["HS256"]
            )
            token_data = TokenPayload(**payload)
        except (jwt.JWTError, ValidationError):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate credentials",
            )
        user = user_repo.get(db, id=int(token_data.sub))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user

    def check_superuser(self, user: User) -> User:
        # Check role or superuser permissions
        if user.role_id != 1 and getattr(user, "is_superuser", False) is not True:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user doesn't have enough privileges",
            )
        return user


auth_service = AuthService()
