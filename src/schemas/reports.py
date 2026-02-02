from pydantic import BaseModel


class GenerateReportRequest(BaseModel):
    format: str = "excel"  # "excel" или "pdf"
    email: str | None = None
