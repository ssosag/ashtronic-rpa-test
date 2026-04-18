import logging
from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.schemas.rpa import ExtractRequest, ExtractResponse
from app.services import job_service, rpa_runner

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/rpa/extract", response_model=ExtractResponse, status_code=202)
async def extract(
    request: ExtractRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    job = await job_service.create_job(db, request)
    background_tasks.add_task(rpa_runner.run, job.id)
    logger.info(f"job_id={job.id} queued fecha_inicial={request.fecha_inicial} fecha_final={request.fecha_final} limit={request.limit}")
    return ExtractResponse(job_id=job.id, status="queued", message="Extraction queued")
