"""Normalized deterministic Experience dimension scorer."""

from __future__ import annotations

from decimal import Decimal

from resumematch.core.schemas.candidate import CandidateProfile
from resumematch.core.schemas.job import JobPosting
from resumematch.matching.contracts import DimensionId, DimensionScore, EvidenceIndex, MatchConfig
from resumematch.matching.experience import total_relevant_experience
from resumematch.rubric.arithmetic import clamp


class ExperienceDimensionScorer:
    """Score the capped ratio of relevant experience to the stated minimum."""

    dimension_id = DimensionId.EXPERIENCE

    def score(
        self,
        profile: CandidateProfile,
        posting: JobPosting,
        evidence: EvidenceIndex,
        config: MatchConfig,
    ) -> DimensionScore:
        del evidence
        minimum = posting.min_experience_years
        if minimum is None:
            raise ValueError("experience score requires a posting minimum")
        experience = total_relevant_experience(
            profile.resume.experience, profile.session_start_date
        )
        score = (
            Decimal("1")
            if minimum == 0
            else clamp(experience.years / minimum, Decimal("0"), Decimal("1"))
        )
        weight = config.dimension_weights[self.dimension_id]
        return DimensionScore(
            dimension_id=self.dimension_id,
            enabled=True,
            score=score,
            weight=weight,
            weighted_score=score * weight,
            evidence_level=None,
            reason="relevant_experience_ratio",
        )
