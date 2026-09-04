"""Public job-source contract; no candidate-derived types cross this boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class SourceCapabilities:
    source_id: str
    universal_search: bool
    requires_registry_entry: bool
    supports_incremental: bool
    is_network_source: bool
    documentation_url: str
    rate_limit_note: str | None


@dataclass(frozen=True)
class FetchRequest:
    registry_entry_id: str | None


@dataclass(frozen=True)
class RawPosting:
    source_external_id: str | None
    payload: dict[str, object]


@dataclass(frozen=True)
class JobPostingDraft:
    source_id: str
    source_external_id: str
    values: dict[str, object]


@dataclass(frozen=True)
class SourceFailure:
    source_id: str
    reason: str


@dataclass(frozen=True)
class FetchResult:
    postings: tuple[RawPosting, ...]
    failures: tuple[SourceFailure, ...]


class JobSource(Protocol):
    def capabilities(self) -> SourceCapabilities: ...

    def fetch(self, request: FetchRequest) -> FetchResult: ...

    def map(self, raw: RawPosting) -> JobPostingDraft: ...
