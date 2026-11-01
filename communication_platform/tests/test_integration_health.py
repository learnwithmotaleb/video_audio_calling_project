"""Readiness against real PostgreSQL and Redis. Run with RUN_INTEGRATION=1."""

import os

import httpx
import pytest
from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import create_engine
from app.core.redis import create_redis
from app.main import create_app

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(os.getenv("RUN_INTEGRATION") != "1", reason="RUN_INTEGRATION=1 not set"),
]


async def test_ready_against_real_services():
    app = create_app(get_settings())
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "checks": {"database": "ok", "redis": "ok"}}


async def test_postgres_query_round_trip():
    engine = create_engine(get_settings())
    try:
        async with engine.connect() as connection:
            assert (await connection.execute(text("SELECT 1 + 1"))).scalar_one() == 2
    finally:
        await engine.dispose()


async def test_redis_write_read_round_trip():
    redis = create_redis(get_settings())
    try:
        await redis.set("phase1:integration", "ok", ex=10)
        assert await redis.get("phase1:integration") == "ok"
    finally:
        await redis.delete("phase1:integration")
        await redis.aclose()
