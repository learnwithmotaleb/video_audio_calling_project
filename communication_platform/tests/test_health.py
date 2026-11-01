import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI

from app.core.database import get_engine
from app.core.redis import get_redis
from app.main import create_app
from tests.test_config import make_settings

SECRET_ERROR = "connection to db-internal.example failed for user admin"


class FakeEngine:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error

    @asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncMock]:
        if self.error:
            raise self.error
        yield AsyncMock()


def build_app(engine: FakeEngine, redis: AsyncMock) -> FastAPI:
    app = create_app(make_settings(health_check_timeout_seconds=0.05))
    app.dependency_overrides[get_engine] = lambda: engine
    app.dependency_overrides[get_redis] = lambda: redis
    return app


async def get(app: FastAPI, path: str) -> httpx.Response:
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(path)


async def test_liveness_needs_no_dependencies():
    response = await get(create_app(make_settings()), "/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_ready_when_all_dependencies_respond():
    response = await get(build_app(FakeEngine(), AsyncMock()), "/api/v1/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "checks": {"database": "ok", "redis": "ok"}}


async def test_not_ready_when_database_fails():
    app = build_app(FakeEngine(OSError("down")), AsyncMock())
    response = await get(app, "/api/v1/health/ready")
    assert response.status_code == 503
    assert response.json() == {
        "status": "unavailable",
        "checks": {"database": "unavailable", "redis": "ok"},
    }


async def test_not_ready_when_redis_fails():
    redis = AsyncMock()
    redis.ping.side_effect = ConnectionError("down")
    response = await get(build_app(FakeEngine(), redis), "/api/v1/health/ready")
    assert response.status_code == 503
    assert response.json()["checks"] == {"database": "ok", "redis": "unavailable"}


async def test_hanging_dependency_times_out_instead_of_blocking():
    async def hang() -> None:
        await asyncio.Event().wait()

    redis = AsyncMock()
    redis.ping.side_effect = hang
    response = await asyncio.wait_for(
        get(build_app(FakeEngine(), redis), "/api/v1/health/ready"), timeout=1
    )
    assert response.status_code == 503
    assert response.json()["checks"]["redis"] == "unavailable"


async def test_failure_details_are_logged_but_not_returned(capsys):
    app = build_app(FakeEngine(OSError(SECRET_ERROR)), AsyncMock())
    response = await get(app, "/api/v1/health/ready")
    assert SECRET_ERROR not in response.text
    assert SECRET_ERROR in capsys.readouterr().out


async def test_unknown_route_uses_the_error_shape():
    response = await get(create_app(make_settings()), "/api/v1/missing")
    assert response.status_code == 404
    assert response.json() == {"error": {"code": "http_error", "message": "Not Found"}}


async def test_unexpected_error_hides_internals():
    app = create_app(make_settings())

    @app.get("/boom")
    async def boom() -> None:
        raise RuntimeError(SECRET_ERROR)

    response = await get(app, "/boom")
    assert response.status_code == 500
    assert response.json() == {
        "error": {"code": "internal_error", "message": "Internal server error"}
    }


@pytest.mark.parametrize("path", ["/docs", "/openapi.json"])
async def test_api_docs_are_disabled_in_production(path):
    production = make_settings(environment="production", livekit_public_url="wss://media.test")
    assert (await get(create_app(production), path)).status_code == 404
    assert (await get(create_app(make_settings()), path)).status_code == 200
