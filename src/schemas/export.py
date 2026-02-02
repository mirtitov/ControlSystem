from typing import Any

from pydantic import BaseModel


class ExportRequest(BaseModel):
    format: str = "excel"  # "excel" или "csv"
    filters: dict[str, Any] | None = None
