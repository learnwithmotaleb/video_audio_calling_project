from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.database import get_engine
from app.core.redis import get_redis
from app.modules.health.schema import LivenessResponse, ReadinessResponse
from app.modules.health.service import check_readiness

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", summary="Liveness: the process is serving requests")
async def liveness() -> LivenessResponse:
    return LivenessResponse()


@router.get(
    "/ready",
    summary="Readiness: PostgreSQL and Redis are reachable",
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ReadinessResponse}},
)
async def readiness(
    request: Request,
    response: Response,
    engine: Annotated[AsyncEngine, Depends(get_engine)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> ReadinessResponse:
    timeout = request.app.state.settings.health_check_timeout_seconds
    result = await check_readiness(engine, redis, timeout)
    if result.status != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return result
