"""Configured normalized seniority dimension scorer."""

from decimal import Decimal

from resumematch.core.schemas.candidate import CandidateProfile, SeniorityId
from resumematch.core.schemas.job import JobPosting
from resumematch.job.requirements.seniority import SeniorityMapping
from resumematch.matching.contracts import DimensionId, DimensionScore, EvidenceIndex, MatchConfig
from resumematch.matching.dimension_scoring import DimensionMatchScoring


class SeniorityDimensionScorer:
    dimension_id = DimensionId.SENIORITY

    def __init__(self, scoring: DimensionMatchScoring, mapping: SeniorityMapping) -> None:
        self._scoring, self._mapping = scoring, mapping

    def score(
        self,
        profile: CandidateProfile,
        posting: JobPosting,
        evidence: EvidenceIndex,
        config: MatchConfig,
    ) -> DimensionScore:
        del evidence
        candidate = (
            profile.target.seniority_id if profile.target is not None else SeniorityId.UNKNOWN
        )
        job = posting.seniority or SeniorityId.UNKNOWN
        score = self._value(candidate, job)
        weight = config.dimension_weights[self.dimension_id]
        return DimensionScore(
            dimension_id=self.dimension_id,
            enabled=True,
            score=score,
            weight=weight,
            weighted_score=score * weight,
            evidence_level=None,
            reason="configured_seniority_distance",
        )

    def _value(self, candidate: SeniorityId, job: SeniorityId) -> Decimal:
        if candidate is SeniorityId.UNKNOWN or job is SeniorityId.UNKNOWN:
            return self._scoring.seniority["unknown_or_absent"]
        levels = {
            value: index
            for index, name in enumerate(self._mapping.order)
            if (value := self._mapping.enum_values[name]) not in {SeniorityId.UNKNOWN}
        }
        if candidate not in levels or job not in levels:
            return self._scoring.seniority["unknown_or_absent"]
        distance = abs(levels[candidate] - levels[job])
        return self._scoring.seniority[
            "exact_match"
            if distance == 0
            else "adjacent_level"
            if distance == 1
            else "two_levels_apart"
            if distance == 2
            else "more_than_two_levels_apart"
        ]
