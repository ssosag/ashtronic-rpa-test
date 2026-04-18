import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Job, Record
from app.schemas.rpa import ExtractRequest

logger = logging.getLogger(__name__)


async def create_job(db: AsyncSession, request: ExtractRequest) -> Job:
    job = Job(
        status="queued",
        fecha_inicial=request.fecha_inicial,
        fecha_final=request.fecha_final,
        limit=request.limit,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    logger.info(f"job_id={job.id} status=queued created")
    return job


async def mark_running(db: AsyncSession, job_id: int) -> None:
    await db.execute(
        update(Job)
        .where(Job.id == job_id)
        .values(status="running", started_at=datetime.now(timezone.utc))
    )
    await db.commit()
    logger.info(f"job_id={job_id} status=running")


async def mark_done(db: AsyncSession, job_id: int, records_count: int) -> None:
    await db.execute(
        update(Job)
        .where(Job.id == job_id)
        .values(
            status="done",
            finished_at=datetime.now(timezone.utc),
            records_count=records_count,
        )
    )
    await db.commit()
    logger.info(f"job_id={job_id} status=done records_count={records_count}")


async def mark_error(db: AsyncSession, job_id: int, error_message: str) -> None:
    await db.execute(
        update(Job)
        .where(Job.id == job_id)
        .values(
            status="error",
            finished_at=datetime.now(timezone.utc),
            error_message=error_message,
        )
    )
    await db.commit()
    logger.info(f"job_id={job_id} status=error")


async def list_jobs(db: AsyncSession, skip: int = 0, limit: int = 50) -> list[Job]:
    result = await db.execute(
        select(Job).order_by(Job.created_at.desc()).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def get_job(db: AsyncSession, job_id: int) -> Job | None:
    return await db.get(Job, job_id)


async def save_record(db: AsyncSession, record: Record) -> Record:
    db.add(record)
    await db.flush()
    return record


async def list_records(
    db: AsyncSession,
    job_id: Optional[int] = None,
    patient_document: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> list[Record]:
    q = select(Record).order_by(Record.captured_at.desc())
    if job_id is not None:
        q = q.where(Record.job_id == job_id)
    if patient_document is not None:
        q = q.where(Record.patient_document.ilike(f"%{patient_document}%"))
    result = await db.execute(q.offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_record(db: AsyncSession, record_id: int) -> Record | None:
    return await db.get(Record, record_id)
