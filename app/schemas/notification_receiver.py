from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr


class NotificationReceiverBase(BaseModel):
    name: str
    email: EmailStr
    designation: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = "active"


class NotificationReceiverCreate(NotificationReceiverBase):
    pass


class NotificationReceiverUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    designation: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None



class NotificationReceiverInDBBase(NotificationReceiverBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NotificationReceiver(NotificationReceiverInDBBase):
    pass
