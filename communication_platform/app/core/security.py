"""User identity interface.

The external authentication service will replace the body of get_current_user.
Everything that needs a user depends on CurrentUser only.
"""

from dataclasses import dataclass
from typing import Annotated

from fastapi import Header, Request, status

from app.core.config import Environment
from app.core.exceptions import AppError


@dataclass(frozen=True)
class CurrentUser:
    user_id: str
    display_name: str
    avatar_url: str | None = None


def _unauthenticated(message: str) -> AppError:
    return AppError(status.HTTP_401_UNAUTHORIZED, "unauthenticated", message)


async def get_current_user(
    request: Request,
    x_dev_user_id: Annotated[str | None, Header(pattern=r"^[A-Za-z0-9_-]{1,64}$")] = None,
) -> CurrentUser:
    """Resolve the caller. The development header is never honoured in production."""
    if request.app.state.settings.environment is Environment.PRODUCTION:
        raise _unauthenticated("Authentication is not configured")
    if x_dev_user_id is None:
        raise _unauthenticated("X-Dev-User-Id header is required in development")
    return CurrentUser(user_id=x_dev_user_id, display_name=x_dev_user_id)
