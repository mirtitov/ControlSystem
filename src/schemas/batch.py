from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date


class BatchCreateRequest(BaseModel):
    СтатусЗакрытия: bool = False
    ПредставлениеЗаданияНаСмену: str
    РабочийЦентр: str
    Смена: str
    Бригада: str
    НомерПартии: int
    ДатаПартии: date
    Номенклатура: str
    КодЕКН: str
    ИдентификаторРЦ: str
    ДатаВремяНачалаСмены: datetime
    ДатаВремяОкончанияСмены: datetime


class BatchCreate(BaseModel):
    is_closed: bool = False
    task_description: str
    work_center_id: int
    shift: str
    team: str
    batch_number: int
    batch_date: date
    nomenclature: str
    ekn_code: str
    shift_start: datetime
    shift_end: datetime


class BatchUpdate(BaseModel):
    is_closed: Optional[bool] = None
    task_description: Optional[str] = None
    shift: Optional[str] = None
    team: Optional[str] = None
    nomenclature: Optional[str] = None
    ekn_code: Optional[str] = None
    shift_start: Optional[datetime] = None
    shift_end: Optional[datetime] = None


class ProductShortResponse(BaseModel):
    id: int
    unique_code: str
    is_aggregated: bool
    aggregated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BatchResponse(BaseModel):
    id: int
    is_closed: bool
    closed_at: Optional[datetime] = None
    task_description: str
    work_center_id: int
    shift: str
    team: str
    batch_number: int
    batch_date: date
    nomenclature: str
    ekn_code: str
    shift_start: datetime
    shift_end: datetime
    created_at: datetime
    updated_at: datetime
    products: List[ProductShortResponse] = []

    class Config:
        from_attributes = True


class BatchListResponse(BaseModel):
    items: List[BatchResponse]
    total: int
    offset: int
    limit: int
