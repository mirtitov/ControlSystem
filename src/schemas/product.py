from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ProductCreate(BaseModel):
    unique_code: str
    batch_id: int


class ProductResponse(BaseModel):
    id: int
    unique_code: str
    batch_id: int
    is_aggregated: bool
    aggregated_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
