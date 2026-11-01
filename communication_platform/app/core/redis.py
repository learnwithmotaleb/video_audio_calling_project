"""Redis client lifecycle and dependency."""

from fastapi import Request
from redis.asyncio import Redis

from app.core.config import Settings


def create_redis(settings: Settings) -> Redis:
    """Build the client. No connection is opened until the first command."""
    return Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        password=settings.redis_password.get_secret_value() or None,
        db=settings.redis_db,
        decode_responses=True,
        socket_connect_timeout=settings.health_check_timeout_seconds,
        socket_timeout=settings.health_check_timeout_seconds,
    )


def get_redis(request: Request) -> Redis:
    return request.app.state.redis
