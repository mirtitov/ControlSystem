from datetime import date, datetime

from pydantic import BaseModel


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
    is_closed: bool | None = None
    task_description: str | None = None
    shift: str | None = None
    team: str | None = None
    nomenclature: str | None = None
    ekn_code: str | None = None
    shift_start: datetime | None = None
    shift_end: datetime | None = None


class ProductShortResponse(BaseModel):
    id: int
    unique_code: str
    is_aggregated: bool
    aggregated_at: datetime | None = None

    class Config:
        from_attributes = True


class BatchResponse(BaseModel):
    id: int
    is_closed: bool
    closed_at: datetime | None = None
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
    products: list[ProductShortResponse] = []

    class Config:
        from_attributes = True


class BatchListResponse(BaseModel):
    items: list[BatchResponse]
    total: int
    offset: int
    limit: int
