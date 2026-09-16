from typing import Optional, Any, List
from pydantic import BaseModel
from datetime import datetime

from app.schemas.notification_receiver import NotificationReceiver as NotificationReceiverSchema


class WebsiteBase(BaseModel):
    name: str
    base_url: str
    start_url: str
    status: Optional[str] = "active"
    crawl_frequency: Optional[str] = "daily"
    config: Optional[Any] = None
    notify_all_receivers: Optional[bool] = True


class WebsiteCreate(WebsiteBase):
    receiver_ids: Optional[List[int]] = []


class WebsiteUpdate(BaseModel):
    name: Optional[str] = None
    base_url: Optional[str] = None
    start_url: Optional[str] = None
    status: Optional[str] = None
    crawl_frequency: Optional[str] = None
    config: Optional[Any] = None
    notify_all_receivers: Optional[bool] = None
    receiver_ids: Optional[List[int]] = None


class WebsiteInDBBase(WebsiteBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Website(WebsiteInDBBase):
    notification_receivers: List[NotificationReceiverSchema] = []



class WebsiteTestExtractionRequest(BaseModel):
    url: str


TestExtractionRequest = WebsiteTestExtractionRequest
