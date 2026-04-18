from fastapi import APIRouter
from app.api.v1 import health, rpa, jobs, records

router = APIRouter()

router.include_router(health.router, tags=["health"])
router.include_router(rpa.router, tags=["rpa"])
router.include_router(jobs.router, tags=["jobs"])
router.include_router(records.router, tags=["records"])
