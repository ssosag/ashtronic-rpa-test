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


async def recover_orphan_jobs(db: AsyncSession) -> int:
    """Mark as 'error' any jobs left in a non-terminal state by a previous run.

    Runs at startup. If the api container crashed or was restarted mid-extraction,
    a job can stay in 'queued' or 'running' forever — the frontend would poll it
    indefinitely. This resolves them as errors with a clear message.
    """
    result = await db.execute(
        update(Job)
        .where(Job.status.in_(("queued", "running")))
        .values(
            status="error",
            finished_at=datetime.now(timezone.utc),
            error_message="orphaned: api restarted mid-extraction",
        )
    )
    await db.commit()
    count = result.rowcount or 0
    if count:
        logger.warning(f"recovered orphan_jobs count={count}")
    return count


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
    patient_name: Optional[str] = None,
    sede: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> list[Record]:
    # Tie-breaker by id so pagination is stable when records share captured_at
    q = select(Record).order_by(Record.captured_at.desc(), Record.id.desc())
    if job_id is not None:
        q = q.where(Record.job_id == job_id)
    if patient_document:
        q = q.where(Record.patient_document.ilike(f"%{patient_document}%"))
    if patient_name:
        q = q.where(Record.patient_name.ilike(f"%{patient_name}%"))
    if sede:
        q = q.where(Record.sede.ilike(f"%{sede}%"))
    result = await db.execute(q.offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_record(db: AsyncSession, record_id: int) -> Record | None:
    return await db.get(Record, record_id)
