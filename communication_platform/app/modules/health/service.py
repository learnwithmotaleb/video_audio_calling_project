"""Dependency health checks."""

import asyncio
import logging
from collections.abc import Awaitable

from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.modules.health.schema import CheckStatus, ReadinessChecks, ReadinessResponse

logger = logging.getLogger(__name__)


async def _ping_database(engine: AsyncEngine) -> None:
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))


async def _run_check(name: str, check: Awaitable[object], timeout: float) -> CheckStatus:
    """Run one check. Failure details go to the logs, never to the HTTP response."""
    try:
        await asyncio.wait_for(check, timeout)
    except Exception:
        logger.warning("Readiness check failed: %s", name, exc_info=True)
        return "unavailable"
    return "ok"


async def check_readiness(engine: AsyncEngine, redis: Redis, timeout: float) -> ReadinessResponse:
    database, redis_status = await asyncio.gather(
        _run_check("database", _ping_database(engine), timeout),
        _run_check("redis", redis.ping(), timeout),
    )
    checks = ReadinessChecks(database=database, redis=redis_status)
    overall = "ok" if database == "ok" and redis_status == "ok" else "unavailable"
    return ReadinessResponse(status=overall, checks=checks)
