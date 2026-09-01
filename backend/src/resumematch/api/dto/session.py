"""Session lifecycle API contracts."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class SessionCreated(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    token: str
    expires_at: datetime
    session_start_date: date


class SessionDeleted(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    discarded: bool
