"""Frozen sanitized candidate artifact held only in session memory."""

from collections.abc import Mapping
from typing import Literal

from pydantic import BaseModel, ConfigDict

from resumematch.core.schemas.candidate import StructuredResume, TargetConstraints


class SanitizedResume(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["sanitized_resume/1"]
    source_profile_revision: int
    resume: StructuredResume
    target: TargetConstraints | None
    removed_span_counts: Mapping[str, int]
