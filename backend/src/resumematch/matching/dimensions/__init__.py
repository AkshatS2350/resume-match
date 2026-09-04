"""Generic scorer protocol and stable v1 dimension registration slots."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Protocol

from resumematch.core.schemas.candidate import CandidateProfile
from resumematch.core.schemas.job import JobPosting
from resumematch.matching.contracts import (
    DimensionId,
    DimensionScore,
    EnablementVerdict,
    EvidenceIndex,
    MatchConfig,
)


class DimensionScorer(Protocol):
    """Common deterministic contract that individual generic dimensions implement."""

    dimension_id: ClassVar[DimensionId]

    def is_enabled(self, profile: CandidateProfile, posting: JobPosting) -> EnablementVerdict: ...

    def score(
        self,
        profile: CandidateProfile,
        posting: JobPosting,
        evidence: EvidenceIndex,
        config: MatchConfig,
    ) -> DimensionScore: ...


@dataclass(frozen=True)
class ScorerSlot:
    """A generic registry entry populated by the owning dimension task."""

    dimension_id: DimensionId


SCORER_REGISTRY = {dimension: ScorerSlot(dimension) for dimension in DimensionId}
