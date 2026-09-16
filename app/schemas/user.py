from typing import Optional
from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    email: EmailStr
    name: str
    status: Optional[str] = "active"
    notification_receive: Optional[bool] = False

class UserCreate(UserBase):
    password: str
    role_id: Optional[int] = None

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    password: Optional[str] = None
    status: Optional[str] = None
    role_id: Optional[int] = None
    notification_receive: Optional[bool] = None

class UserInDBBase(UserBase):
    id: int
    role_id: Optional[int] = None
    notification_receive: Optional[bool] = False

    class Config:
        from_attributes = True

class User(UserInDBBase):
    pass
