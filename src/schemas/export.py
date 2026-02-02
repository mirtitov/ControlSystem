from pydantic import BaseModel
from typing import Optional, Dict, Any


class ExportRequest(BaseModel):
    format: str = "excel"  # "excel" или "csv"
    filters: Optional[Dict[str, Any]] = None
