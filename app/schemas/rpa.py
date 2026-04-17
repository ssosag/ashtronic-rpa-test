from datetime import date
from pydantic import BaseModel, Field, model_validator


class ExtractRequest(BaseModel):
    fecha_inicial: date
    fecha_final: date
    limit: int = Field(gt=0, le=1000)

    @model_validator(mode="after")
    def validate_dates(self) -> "ExtractRequest":
        if self.fecha_inicial > self.fecha_final:
            raise ValueError("fecha_inicial must be less than or equal to fecha_final")
        return self


class ExtractResponse(BaseModel):
    job_id: int
    status: str
    message: str
