"""Call access."""

from app.core.config import Settings
from app.core.security import CurrentUser
from app.integrations.livekit.client import LiveKitGateway
from app.integrations.livekit.token import create_access_token
from app.modules.calls.schema import CallTokenResponse


async def issue_call_token(
    user: CurrentUser, room_id: str, livekit: LiveKitGateway, settings: Settings
) -> CallTokenResponse:
    """Prepare the room and issue a token for it.

    room_id is the LiveKit room name until the rooms module adds membership checks here.
    """
    await livekit.ensure_room(room_id)
    return CallTokenResponse(
        url=settings.livekit_public_url,
        token=create_access_token(settings, user, room_id),
        room_id=room_id,
        identity=user.user_id,
    )
