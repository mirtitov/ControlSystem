from datetime import datetime
from typing import Any

from pydantic import BaseModel


class WebhookSubscriptionCreate(BaseModel):
    url: str
    events: list[str]
    secret_key: str
    retry_count: int = 3
    timeout: int = 10


class WebhookSubscriptionUpdate(BaseModel):
    is_active: bool | None = None
    events: list[str] | None = None
    retry_count: int | None = None
    timeout: int | None = None


class WebhookSubscriptionResponse(BaseModel):
    id: int
    url: str
    events: list[str]
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
    payload: dict[str, Any]
    status: str
    attempts: int
    response_status: int | None = None
    response_body: str | None = None
    error_message: str | None = None
    created_at: datetime
    delivered_at: datetime | None = None

    class Config:
        from_attributes = True
