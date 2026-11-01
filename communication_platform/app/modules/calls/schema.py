from pydantic import BaseModel, Field


class CallTokenRequest(BaseModel):
    room_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,64}$")


class CallTokenResponse(BaseModel):
    url: str
    token: str
    room_id: str
    identity: str
