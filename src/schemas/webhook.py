from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class WebhookSubscriptionCreate(BaseModel):
    url: str
    events: List[str]
    secret_key: str
    retry_count: int = 3
    timeout: int = 10


class WebhookSubscriptionUpdate(BaseModel):
    is_active: Optional[bool] = None
    events: Optional[List[str]] = None
    retry_count: Optional[int] = None
    timeout: Optional[int] = None


class WebhookSubscriptionResponse(BaseModel):
    id: int
    url: str
    events: List[str]
    is_active: bool
    retry_count: int
    timeout: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WebhookDeliveryResponse(BaseModel):
    id: int
    subscription_id: int
    event_type: str
    payload: Dict[str, Any]
    status: str
    attempts: int
    response_status: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    delivered_at: Optional[datetime] = None

    class Config:
        from_attributes = True
