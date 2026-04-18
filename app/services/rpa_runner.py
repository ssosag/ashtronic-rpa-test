import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy import update
from app.db.database import async_session
from app.db.models import Job, Record
from app.services import job_service
from app.rpa import bot
from app.rpa.errors import BotError

logger = logging.getLogger(__name__)


async def run(job_id: int) -> None:
    """Orchestrates a single extraction job.

    Opens its own DB session (BackgroundTask runs outside the request lifecycle).
    Runs the sync Selenium bot in a worker thread via `asyncio.to_thread` so it does
    not block the event loop.

    Persistence is atomic: the records INSERTs and the `mark_done` UPDATE happen in
    the same transaction, so a job can never end up with orphan records and a
    non-terminal status.
    """
    async with async_session() as db:
        job = await job_service.get_job(db, job_id)
        if job is None:
            logger.error(f"job_id={job_id} not found, cannot run extraction")
            return

        fecha_inicial = job.fecha_inicial
        fecha_final = job.fecha_final
        limit = job.limit

        logger.info(f"job_id={job_id} step=start")
        await job_service.mark_running(db, job_id)

        try:
            rows = await asyncio.to_thread(
                bot.run, job_id, fecha_inicial, fecha_final, limit
            )
        except BotError as exc:
            logger.error(f"job_id={job_id} step={exc.step} error={exc.message}")
            await job_service.mark_error(db, job_id, str(exc))
            return
        except Exception as exc:
            logger.exception(f"job_id={job_id} step=unexpected error={exc}")
            await job_service.mark_error(db, job_id, str(exc))
            return

        # Atomic: all records + job status transition succeed or fail together.
        try:
            async with db.begin():
                for data in rows:
                    db.add(
                        Record(
                            job_id=job_id,
                            external_row_id=data.get("external_row_id"),
                            patient_name=data.get("patient_name"),
                            patient_document=data.get("patient_document"),
                            date_service=data.get("date_service"),
                            sede=data.get("sede"),
                            contrato=data.get("contrato"),
                            raw_row_json=data["raw_row_json"],
                        )
                    )
                await db.execute(
                    update(Job)
                    .where(Job.id == job_id)
                    .values(
                        status="done",
                        finished_at=datetime.now(timezone.utc),
                        records_count=len(rows),
                    )
                )
            logger.info(f"job_id={job_id} step=done records={len(rows)}")
        except Exception as exc:
            logger.exception(f"job_id={job_id} step=persist error={exc}")
            await job_service.mark_error(db, job_id, f"persist error: {exc}")
