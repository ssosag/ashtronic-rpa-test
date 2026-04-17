from fastapi import APIRouter
from app.api.v1 import health

router = APIRouter()

router.include_router(health.router, tags=["health"])
# rpa, jobs, records se añaden en Fase 3
