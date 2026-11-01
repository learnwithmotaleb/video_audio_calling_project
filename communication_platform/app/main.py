"""FastAPI application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import Environment, Settings, get_settings
from app.core.database import create_engine
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.redis import create_redis
from app.integrations.livekit.client import LiveKitGateway
from app.modules.calls.router import router as calls_router
from app.modules.health.router import router as health_router

API_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    app.state.engine = create_engine(settings)
    app.state.redis = create_redis(settings)
    app.state.livekit = LiveKitGateway(settings)
    yield
    await app.state.livekit.close()
    await app.state.redis.aclose()
    await app.state.engine.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    is_production = settings.environment is Environment.PRODUCTION
    app = FastAPI(
        title="Communication Platform API",
        version="0.1.0",
        lifespan=lifespan,
        docs_url=None if is_production else "/docs",
        redoc_url=None,
        openapi_url=None if is_production else "/openapi.json",
    )
    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    app.include_router(health_router, prefix=API_PREFIX)
    app.include_router(calls_router, prefix=API_PREFIX)
    return app


app = create_app()
