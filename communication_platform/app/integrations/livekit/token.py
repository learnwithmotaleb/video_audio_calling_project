"""LiveKit access token generation."""

from datetime import timedelta

from livekit import api

from app.core.config import Settings
from app.core.security import CurrentUser

TOKEN_TTL = timedelta(minutes=15)


def create_access_token(settings: Settings, user: CurrentUser, room_name: str) -> str:
    """Issue a token limited to one room. Grants are decided here, never by the client."""
    grants = api.VideoGrants(
        room_join=True,
        room=room_name,
        can_publish=True,
        can_subscribe=True,
        can_publish_data=True,
    )
    return (
        api.AccessToken(settings.livekit_api_key, settings.livekit_api_secret.get_secret_value())
        .with_identity(user.user_id)
        .with_name(user.display_name)
        .with_grants(grants)
        .with_ttl(TOKEN_TTL)
        .to_jwt()
    )
