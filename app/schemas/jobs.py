from datetime import datetime, date
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    done = "done"
    error = "error"


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: JobStatus
    fecha_inicial: date
    fecha_final: date
    limit: int
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    records_count: int
    error_message: Optional[str]
    created_at: datetime


class JobDetail(JobOut):
    pass
