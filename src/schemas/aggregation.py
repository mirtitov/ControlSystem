from pydantic import BaseModel
from typing import List


class AggregateRequest(BaseModel):
    unique_codes: List[str]


class AggregateAsyncRequest(BaseModel):
    unique_codes: List[str]
