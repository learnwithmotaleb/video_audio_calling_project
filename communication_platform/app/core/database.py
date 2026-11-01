"""PostgreSQL engine lifecycle and session dependency."""

from collections.abc import AsyncIterator

from fastapi import Request
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings


def create_engine(settings: Settings) -> AsyncEngine:
    """Build the engine. No connection is opened until the first query."""
    return create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
        connect_args={"timeout": settings.health_check_timeout_seconds},
    )


def get_engine(request: Request) -> AsyncEngine:
    return request.app.state.engine


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    sessionmaker = async_sessionmaker(request.app.state.engine, expire_on_commit=False)
    async with sessionmaker() as session:
        yield session
