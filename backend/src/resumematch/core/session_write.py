from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from .schemas.sanitized import SanitizedResume
from .session import Session


class SanitizationRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    content_hash: str
    profile_revision: int
    produced_at: datetime
    pii_policy_version: str
    detector_versions: tuple[str, ...]
    placeholder_set_version: str
    removed_categories: tuple[str, ...]
    fail_safe_redaction_count: int


def write_sanitization_record(
    session: Session, resume: SanitizedResume, record: SanitizationRecord
) -> None:
    session._sanitized_resume = resume
    session._sanitization_record = record
