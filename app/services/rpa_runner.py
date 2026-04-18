import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy import update
from app.core.config import get_settings
from app.db.database import async_session
from app.db.models import Job, Record
from app.services import job_service
from app.rpa import bot
from app.rpa.errors import BotError

logger = logging.getLogger(__name__)

# Caps bot execution concurrency to the amount of Selenium sessions available.
_runner_slots = asyncio.Semaphore(max(1, get_settings().selenium_max_sessions))


async def run(job_id: int) -> None:
    """Orchestrates a single extraction job.

    Opens its own DB session (BackgroundTask runs outside the request lifecycle).
    Runs the sync Selenium bot in a worker thread via `asyncio.to_thread` so it does
    not block the event loop.

    Persistence is atomic: the records INSERTs and the `mark_done` UPDATE happen in
    the same transaction, so a job can never end up with orphan records and a
    non-terminal status.
    """
    logger.info(f"job_id={job_id} step=wait_slot")
    async with _runner_slots:
        logger.info(f"job_id={job_id} step=slot_acquired")
        async with async_session() as db:
            job = await job_service.get_job(db, job_id)
            if job is None:
                logger.error(f"job_id={job_id} not found, cannot run extraction")
                return

            fecha_inicial = job.fecha_inicial
            fecha_final = job.fecha_final
            limit = job.limit

            logger.info(f"job_id={job_id} step=start")

            stats: dict = {"retries": 0}
            loop = asyncio.get_running_loop()
            session_started = asyncio.Event()

            def _on_session_started() -> None:
                loop.call_soon_threadsafe(session_started.set)

            bot_task = asyncio.create_task(
                asyncio.to_thread(
                    bot.run,
                    job_id,
                    fecha_inicial,
                    fecha_final,
                    limit,
                    stats,
                    _on_session_started,
                )
            )
            wait_started_task = asyncio.create_task(session_started.wait())
            running_marked = False

            await asyncio.wait(
                {bot_task, wait_started_task},
                return_when=asyncio.FIRST_COMPLETED,
            )

            # Keep queued while waiting for a Selenium slot; move to running only
            # after a webdriver session is actually started.
            if session_started.is_set():
                await job_service.mark_running(db, job_id)
                running_marked = True

            if not bot_task.done() and not running_marked:
                await wait_started_task
                await job_service.mark_running(db, job_id)
                running_marked = True

            if not wait_started_task.done():
                wait_started_task.cancel()

            try:
                rows = await bot_task
            except BotError as exc:
                logger.error(f"job_id={job_id} step={exc.step} error={exc.message}")
                await job_service.set_retries_count(db, job_id, stats.get("retries", 0))
                await job_service.mark_error(db, job_id, str(exc))
                return
            except Exception as exc:
                logger.exception(f"job_id={job_id} step=unexpected error={exc}")
                await job_service.set_retries_count(db, job_id, stats.get("retries", 0))
                await job_service.mark_error(db, job_id, str(exc))
                return

            await job_service.set_retries_count(db, job_id, stats.get("retries", 0))

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
