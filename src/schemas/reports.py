from pydantic import BaseModel
from typing import Optional


class GenerateReportRequest(BaseModel):
    format: str = "excel"  # "excel" или "pdf"
    email: Optional[str] = None
