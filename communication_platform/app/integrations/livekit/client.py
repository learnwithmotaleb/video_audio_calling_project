"""LiveKit server API client lifecycle and room operations."""

import logging

import aiohttp
from fastapi import Request, status
from livekit import api

from app.core.config import Settings
from app.core.exceptions import AppError

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_SECONDS = 5


class LiveKitGateway:
    def __init__(self, settings: Settings) -> None:
        self._api = api.LiveKitAPI(
            settings.livekit_host,
            settings.livekit_api_key,
            settings.livekit_api_secret.get_secret_value(),
            timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT_SECONDS),
            failover=False,
        )

    async def ensure_room(self, name: str) -> None:
        """Create the room if needed. LiveKit returns the existing room otherwise."""
        try:
            await self._api.room.create_room(api.CreateRoomRequest(name=name))
        except (api.TwirpError, aiohttp.ClientError, TimeoutError) as exc:
            logger.error("LiveKit room creation failed", exc_info=exc)
            raise AppError(
                status.HTTP_502_BAD_GATEWAY,
                "livekit_unavailable",
                "The media server is unavailable",
            ) from exc

    async def close(self) -> None:
        await self._api.aclose()


def get_livekit(request: Request) -> LiveKitGateway:
    return request.app.state.livekit
