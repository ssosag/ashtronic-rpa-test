from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict


class RecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    external_row_id: Optional[str]
    patient_name: Optional[str]
    patient_document: Optional[str]
    date_service: Optional[str]
    sede: Optional[str]
    contrato: Optional[str]
    captured_at: datetime


class RecordDetail(RecordOut):
    raw_row_json: Any
