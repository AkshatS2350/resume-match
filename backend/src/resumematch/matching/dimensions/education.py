"""Configured normalized education dimension scorer."""

from decimal import Decimal

from resumematch.core.schemas.candidate import CandidateProfile, DegreeLevel
from resumematch.core.schemas.job import EducationRequirement, JobPosting
from resumematch.matching.contracts import DimensionId, DimensionScore, EvidenceIndex, MatchConfig
from resumematch.matching.dimension_scoring import DimensionMatchScoring
from resumematch.skill.fold import fold

_DEGREES = (
    DegreeLevel.NONE,
    DegreeLevel.ASSOCIATE,
    DegreeLevel.BACHELORS,
    DegreeLevel.MASTERS,
    DegreeLevel.DOCTORATE,
)


class EducationDimensionScorer:
    dimension_id = DimensionId.EDUCATION

    def __init__(self, scoring: DimensionMatchScoring) -> None:
        self._scoring = scoring

    def score(
        self,
        profile: CandidateProfile,
        posting: JobPosting,
        evidence: EvidenceIndex,
        config: MatchConfig,
    ) -> DimensionScore:
        del evidence
        values = [
            self._pair(item.degree_level, item.field_of_study, requirement)
            for item in profile.resume.education
            for requirement in posting.education_requirements
        ]
        score = max(values, default=Decimal("0"))
        weight = config.dimension_weights[self.dimension_id]
        return DimensionScore(
            dimension_id=self.dimension_id,
            enabled=True,
            score=score,
            weight=weight,
            weighted_score=score * weight,
            evidence_level=None,
            reason="configured_education_match",
        )

    def _pair(
        self, degree: DegreeLevel | None, field: str | None, requirement: EducationRequirement
    ) -> Decimal:
        if degree is None or requirement.degree_level is None:
            return Decimal("0")
        gap = _DEGREES.index(degree) - _DEGREES.index(requirement.degree_level)
        degree_score = self._scoring.education_degree[
            "exact_or_higher"
            if gap >= 0
            else "one_level_below"
            if gap == -1
            else "more_than_one_level_below"
        ]
        if field is None or requirement.field_of_study is None:
            field_score = self._scoring.education_field["unknown_or_absent"]
        else:
            candidate, required = fold(field), fold(requirement.field_of_study)
            field_score = self._scoring.education_field[
                "exact_field_match"
                if candidate == required
                else "configured_related_field_match"
                if candidate in self._scoring.related_fields.get(required, ())
                else "no_match"
            ]
        return (
            degree_score * self._scoring.education_weights["degree_level"]
            + field_score * self._scoring.education_weights["field"]
        )
