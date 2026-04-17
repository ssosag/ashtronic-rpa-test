import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db import models as _models  # noqa: F401 — registers models with Base.metadata
from app.db.database import init_db, close_db
from app.api.v1.router import router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    logger.info("app_event=startup")
    await init_db()
    logger.info("database=initialized")
    yield
    await close_db()
    logger.info("app_event=shutdown")


settings = get_settings()

app = FastAPI(
    title="Ashtronic RPA API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")
