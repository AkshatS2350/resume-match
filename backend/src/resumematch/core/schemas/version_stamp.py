from typing import Literal

from pydantic import BaseModel, ConfigDict


class VersionStamp(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    schema_version: str
    engine_version: str
    rubric_id: str | None
    rubric_version: str | None
    rubric_status: Literal["draft", "reviewed", "stable"] | None
    alias_file_version: str
    evidence_multiplier_version: str
    match_weight_version: str | None
    threshold_version: str | None
    confidence_weight_version: str | None
    pattern_set_version: str | None
    delimitation_version: str | None
    relevance_rule_version: str | None


def version_stamp(**values: str | None) -> VersionStamp:
    return VersionStamp.model_validate(values)
