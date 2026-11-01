from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI, status
from livekit import api

from app.core.exceptions import AppError
from app.integrations.livekit.client import get_livekit
from app.main import create_app
from tests.test_config import make_settings

SECRET = "s" * 64
HEADERS = {"X-Dev-User-Id": "alice"}


def build_app(livekit: AsyncMock | None = None, **overrides) -> tuple[FastAPI, AsyncMock]:
    livekit = livekit or AsyncMock()
    app = create_app(make_settings(livekit_api_secret=SECRET, **overrides))
    app.dependency_overrides[get_livekit] = lambda: livekit
    return app, livekit


async def post_token(app: FastAPI, body: dict, headers: dict | None = None) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post("/api/v1/calls/token", json=body, headers=headers)


async def test_token_is_limited_to_the_requested_room():
    app, livekit = build_app()
    response = await post_token(app, {"room_id": "room-1"}, HEADERS)

    assert response.status_code == 200
    body = response.json()
    assert body["url"] == "ws://localhost:7880"
    livekit.ensure_room.assert_awaited_once_with("room-1")

    claims = api.TokenVerifier("key", SECRET).verify(body["token"])
    assert claims.identity == "alice"
    assert claims.video.room == "room-1"
    assert claims.video.room_join is True
    assert not claims.video.room_admin
    assert not claims.video.room_create


async def test_client_cannot_choose_identity_or_grants_through_the_body():
    app, _ = build_app()
    response = await post_token(
        app, {"room_id": "room-1", "identity": "admin", "room_admin": True}, HEADERS
    )
    claims = api.TokenVerifier("key", SECRET).verify(response.json()["token"])
    assert claims.identity == "alice"
    assert not claims.video.room_admin


async def test_missing_identity_is_rejected():
    app, livekit = build_app()
    response = await post_token(app, {"room_id": "room-1"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"
    livekit.ensure_room.assert_not_awaited()


async def test_development_identity_is_disabled_in_production():
    app, livekit = build_app(environment="production", livekit_public_url="wss://media.test")
    response = await post_token(app, {"room_id": "room-1"}, HEADERS)
    assert response.status_code == 401
    livekit.ensure_room.assert_not_awaited()


@pytest.mark.parametrize("room_id", ["", "has space", "../etc", "x" * 65])
async def test_invalid_room_id_is_rejected(room_id):
    app, _ = build_app()
    response = await post_token(app, {"room_id": room_id}, HEADERS)
    assert response.status_code == 422


async def test_invalid_identity_header_is_rejected():
    app, _ = build_app()
    response = await post_token(app, {"room_id": "room-1"}, {"X-Dev-User-Id": "bad id!"})
    assert response.status_code == 422


async def test_media_server_failure_issues_no_token():
    livekit = AsyncMock()
    livekit.ensure_room.side_effect = AppError(
        status.HTTP_502_BAD_GATEWAY, "livekit_unavailable", "The media server is unavailable"
    )
    app, _ = build_app(livekit)
    response = await post_token(app, {"room_id": "room-1"}, HEADERS)
    assert response.status_code == 502
    assert "token" not in response.json()
