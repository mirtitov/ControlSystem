from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import date


class ExportRequest(BaseModel):
    format: str = "excel"  # "excel" или "csv"
    filters: Optional[Dict[str, Any]] = None
