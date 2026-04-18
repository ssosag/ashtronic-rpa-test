from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.schemas.jobs import JobOut, JobDetail
from app.services import job_service

router = APIRouter()


@router.get("/jobs", response_model=list[JobOut])
async def list_jobs(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    return await job_service.list_jobs(db, skip=skip, limit=limit)


@router.get("/jobs/{job_id}", response_model=JobDetail)
async def get_job(job_id: int, db: AsyncSession = Depends(get_db)):
    job = await job_service.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
