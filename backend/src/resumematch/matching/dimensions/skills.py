"""Normalized deterministic Skills dimension scorer."""

from __future__ import annotations

from decimal import Decimal

from resumematch.core.schemas.candidate import CandidateProfile
from resumematch.core.schemas.job import JobPosting
from resumematch.matching.contracts import (
    DimensionId,
    DimensionScore,
    EvidenceIndex,
    EvidenceLevel,
    MatchConfig,
)


class SkillsDimensionScorer:
    """Average the configured evidence multiplier for each scoreable requirement."""

    dimension_id = DimensionId.SKILLS

    def __init__(self, multipliers: dict[int, Decimal]) -> None:
        self._multipliers = multipliers

    def score(
        self,
        profile: CandidateProfile,
        posting: JobPosting,
        evidence: EvidenceIndex,
        config: MatchConfig,
    ) -> DimensionScore:
        del profile
        requirements = tuple(
            sorted(
                (
                    requirement
                    for requirement in posting.requirements
                    if requirement.canonical_skill_id is not None
                    and requirement.classification != "contextual"
                ),
                key=lambda requirement: requirement.requirement_id,
            )
        )
        total = Decimal("0")
        for requirement in requirements:
            references = evidence.by_requirement_id.get(requirement.requirement_id, ())
            level = max(
                (reference.evidence_level for reference in references),
                default=EvidenceLevel.LEVEL_0,
            )
            total += self._multipliers[int(level)]
        score = total / Decimal(len(requirements)) if requirements else Decimal("0")
        weight = config.dimension_weights[self.dimension_id]
        return DimensionScore(
            dimension_id=self.dimension_id,
            enabled=True,
            score=score,
            weight=weight,
            weighted_score=score * weight,
            evidence_level=None,
            reason="scoreable_requirements",
        )
