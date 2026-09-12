"""Privacy-inspector contracts with value-bearing and value-free views kept separate."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from resumematch.core.session import ProjectedField, ProviderLocality


class OmissionRecord(BaseModel):
    """One resume-root path absent from the pending projection."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str
    reason: Literal["not_required_by_operation", "omitted_for_budget"]


class PendingRequestProjection(BaseModel):
    """Exact admitted values only, for the current session before consent."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str
    operation: str
    fields: tuple[ProjectedField, ...]
    payload_hash: str
    provider_identity: str
    provider_locality: ProviderLocality
    admitted_at: datetime
    omissions: tuple[OmissionRecord, ...]


class ManifestEntry(BaseModel):
    """Value-free history of admitted cloud requests."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    manifest_version: str
    operation: str
    field_paths: tuple[str, ...]
    omitted_paths: tuple[str, ...]
    omissions: tuple[OmissionRecord, ...]
    payload_hash: str
    transmitted_at: datetime


class RequestManifest(BaseModel):
    """The session's bounded, value-free LLM request manifest."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    entries: tuple[ManifestEntry, ...]


class ConsentSubmission(BaseModel):
    """The user must explicitly approve or decline the pending transmission."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    approved: bool


class ConsentResult(BaseModel):
    """Value-free outcome of an explicit decision."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str
    decision: Literal["declined", "unavailable", "transmitted"]
    decided_at: datetime
