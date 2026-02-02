from pydantic import BaseModel
from datetime import datetime


class WorkCenterCreate(BaseModel):
    identifier: str
    name: str


class WorkCenterResponse(BaseModel):
    id: int
    identifier: str
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
