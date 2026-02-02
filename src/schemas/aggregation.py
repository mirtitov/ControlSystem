from pydantic import BaseModel


class AggregateRequest(BaseModel):
    unique_codes: list[str]


class AggregateAsyncRequest(BaseModel):
    unique_codes: list[str]
