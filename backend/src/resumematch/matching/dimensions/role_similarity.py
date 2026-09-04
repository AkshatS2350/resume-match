"""Normalized role-similarity scoring from configured role-family pairs."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from resumematch.core.schemas.candidate import CandidateProfile
from resumematch.core.schemas.job import JobPosting
from resumematch.matching.candidate_context import (
    CandidateContextResolver,
    resolve_candidate_context,
    resolve_title_role_family,
)
from resumematch.matching.contracts import DimensionId, DimensionScore, EvidenceIndex, MatchConfig

_UNKNOWN = "unknown"


class RoleSimilarityDimensionScorer:
    """Choose the strongest configured candidate-role-family pair score."""

    dimension_id = DimensionId.ROLE_SIMILARITY

    def __init__(
        self, role_family_table: Mapping[str, object], resolver: CandidateContextResolver
    ) -> None:
        self._pairs = role_family_table.get("pairs")
        self._resolver = resolver

    def score(
        self,
        profile: CandidateProfile,
        posting: JobPosting,
        evidence: EvidenceIndex,
        config: MatchConfig,
    ) -> DimensionScore:
        del evidence
        context = resolve_candidate_context(profile, self._resolver)
        posting_family = posting.role_family or _UNKNOWN
        if posting_family == _UNKNOWN and posting.normalized_title is not None:
            posting_family = resolve_title_role_family(posting.normalized_title, self._resolver)
        candidate_families = (context.target_role_family, *context.prior_role_families)
        raw_score = max(
            (
                _pair_score(self._pairs, candidate_family, posting_family)
                for candidate_family in sorted(set(candidate_families))
            ),
            default=Decimal("0"),
        )
        score = raw_score / Decimal("100")
        weight = config.dimension_weights[self.dimension_id]
        return DimensionScore(
            dimension_id=self.dimension_id,
            enabled=True,
            score=score,
            weight=weight,
            weighted_score=score * weight,
            evidence_level=None,
            reason="configured_role_family_pair" if raw_score else "unresolved_role_family",
        )


def _pair_score(pairs: object, candidate_family: str, posting_family: str) -> Decimal:
    if not isinstance(pairs, dict):
        return Decimal("0")
    row = pairs.get(candidate_family)
    if not isinstance(row, dict):
        return Decimal("0")
    score = row.get(posting_family)
    return Decimal(score) if isinstance(score, int) else Decimal("0")
