"""Pytest fixtures: in-memory SQLite DB + FastAPI test client.

Env vars are set BEFORE any `app.*` import so pydantic-settings does not try to
read the real `.env` for required fields like PORTAL_USER.
"""
import os

os.environ.setdefault("PORTAL_USER", "test-user")
os.environ.setdefault("PORTAL_PASSWORD", "test-pass")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("SELENIUM_HUB_URL", "http://selenium:4444/wd/hub")

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.database import Base, get_db
from app.main import app
from app.db import models  # noqa: F401 — register models with Base.metadata


@pytest_asyncio.fixture
async def db_engine():
    """Fresh in-memory SQLite engine per test."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncSession:
    Session = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_engine):
    """FastAPI client whose DB dependency uses the in-memory engine."""
    Session = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async def _override_get_db():
        async with Session() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
