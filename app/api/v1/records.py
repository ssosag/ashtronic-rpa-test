from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.schemas.records import RecordOut, RecordDetail
from app.services import job_service

router = APIRouter()


@router.get("/records", response_model=list[RecordOut])
async def list_records(
    job_id: Optional[int] = Query(default=None, description="Filter by job"),
    patient_document: Optional[str] = Query(default=None, description="Partial match on document"),
    patient_name: Optional[str] = Query(default=None, description="Partial match on name"),
    sede: Optional[str] = Query(default=None, description="Partial match on sede"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    return await job_service.list_records(
        db,
        job_id=job_id,
        patient_document=patient_document,
        patient_name=patient_name,
        sede=sede,
        skip=skip,
        limit=limit,
    )


@router.get("/records/{record_id}", response_model=RecordDetail)
async def get_record(record_id: int, db: AsyncSession = Depends(get_db)):
    record = await job_service.get_record(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record
