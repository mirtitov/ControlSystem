from datetime import datetime

from pydantic import BaseModel


class ProductCreate(BaseModel):
    unique_code: str
    batch_id: int


class ProductResponse(BaseModel):
    id: int
    unique_code: str
    batch_id: int
    is_aggregated: bool
    aggregated_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True
