import asyncio
import logging
from app.db.database import async_session
from app.db.models import Record
from app.services import job_service
from app.rpa import bot
from app.rpa.errors import BotError

logger = logging.getLogger(__name__)


async def run(job_id: int) -> None:
    """Orchestrates a single extraction job.

    Opens its own DB session (BackgroundTask runs outside the request lifecycle).
    Runs the sync Selenium bot in a worker thread via `asyncio.to_thread` so it does
    not block the event loop.
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

            for data in rows:
                record = Record(
                    job_id=job_id,
                    external_row_id=data.get("external_row_id"),
                    patient_name=data.get("patient_name"),
                    patient_document=data.get("patient_document"),
                    date_service=data.get("date_service"),
                    sede=data.get("sede"),
                    contrato=data.get("contrato"),
                    raw_row_json=data.get("raw_row_json", data),
                )
                await job_service.save_record(db, record)
            await db.commit()

            await job_service.mark_done(db, job_id, records_count=len(rows))
            logger.info(f"job_id={job_id} step=done records={len(rows)}")

        except BotError as exc:
            logger.error(f"job_id={job_id} step={exc.step} error={exc.message}")
            await job_service.mark_error(db, job_id, str(exc))
        except Exception as exc:
            logger.error(f"job_id={job_id} step=unexpected error={exc}")
            await job_service.mark_error(db, job_id, str(exc))
