from functools import lru_cache
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


@lru_cache
def _engine() -> AsyncEngine:
    return create_async_engine(get_settings().database_url, echo=False)


@lru_cache
def _sessionmaker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(_engine(), class_=AsyncSession, expire_on_commit=False)


def async_session() -> AsyncSession:
    """Return a new AsyncSession. Callers must use it as an async context manager."""
    return _sessionmaker()()


async def get_db():
    async with _sessionmaker()() as session:
        yield session


async def init_db():
    async with _engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    await _engine().dispose()
