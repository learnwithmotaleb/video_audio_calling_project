from typing import Literal

from pydantic import BaseModel

CheckStatus = Literal["ok", "unavailable"]


class LivenessResponse(BaseModel):
    status: Literal["ok"] = "ok"


class ReadinessChecks(BaseModel):
    database: CheckStatus
    redis: CheckStatus


class ReadinessResponse(BaseModel):
    status: CheckStatus
    checks: ReadinessChecks
