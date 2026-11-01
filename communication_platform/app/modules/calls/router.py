from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.core.security import CurrentUser, get_current_user
from app.integrations.livekit.client import LiveKitGateway, get_livekit
from app.modules.calls.schema import CallTokenRequest, CallTokenResponse
from app.modules.calls.service import issue_call_token

router = APIRouter(prefix="/calls", tags=["calls"])


@router.post("/token", summary="Get a LiveKit token for the current user")
async def create_call_token(
    body: CallTokenRequest,
    request: Request,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    livekit: Annotated[LiveKitGateway, Depends(get_livekit)],
) -> CallTokenResponse:
    return await issue_call_token(user, body.room_id, livekit, request.app.state.settings)
