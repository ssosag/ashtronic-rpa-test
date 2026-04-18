import asyncio
import logging
from app.db.database import async_session
from app.db.models import Record
from app.services import job_service

logger = logging.getLogger(__name__)


async def run(job_id: int) -> None:
    """Orchestrates a single extraction job. Opens its own DB session (BackgroundTask
    runs outside the request lifecycle, so the request session is already closed)."""
    async with async_session() as db:
        logger.info(f"job_id={job_id} step=start")
        await job_service.mark_running(db, job_id)

        try:
            logger.info(f"job_id={job_id} step=stub_extraction")
            # --- STUB: replace with real bot call in Phase 5 ---
            await asyncio.sleep(3)

            stub_records = [
                Record(
                    job_id=job_id,
                    patient_name="Paciente Ejemplo Uno",
                    patient_document="1000000001",
                    date_service="2026-01-15",
                    sede="Sede Principal",
                    contrato="Savia Salud Subsidiado",
                    raw_row_json={
                        "row": 1,
                        "stub": True,
                        "note": "replaced by real bot in Phase 5",
                    },
                ),
                Record(
                    job_id=job_id,
                    patient_name="Paciente Ejemplo Dos",
                    patient_document="1000000002",
                    date_service="2026-01-16",
                    sede="Sede Norte",
                    contrato="Savia Salud Subsidiado",
                    raw_row_json={
                        "row": 2,
                        "stub": True,
                        "note": "replaced by real bot in Phase 5",
                    },
                ),
            ]

            for record in stub_records:
                await job_service.save_record(db, record)
            await db.commit()
            # ---------------------------------------------------

            await job_service.mark_done(db, job_id, records_count=len(stub_records))

        except Exception as exc:
            logger.error(f"job_id={job_id} step=error error={exc}")
            await job_service.mark_error(db, job_id, str(exc))
            raise
