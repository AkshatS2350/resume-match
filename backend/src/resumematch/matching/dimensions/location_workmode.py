"""Configured normalized location and work-mode dimension scorer."""

from decimal import Decimal

from resumematch.core.schemas.candidate import CandidateProfile, WorkMode
from resumematch.core.schemas.job import JobPosting
from resumematch.job.normalizer import location_fold
from resumematch.matching.contracts import DimensionId, DimensionScore, EvidenceIndex, MatchConfig
from resumematch.matching.dimension_scoring import DimensionMatchScoring


class LocationWorkModeDimensionScorer:
    dimension_id = DimensionId.LOCATION_WORKMODE

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
        target = profile.target
        modes = target.work_modes if target is not None else ()
        locations = target.locations if target is not None else ()
        mode_score = self._mode(modes, posting.work_mode)
        location_score = max(
            (
                _location(location, posting.normalized_location, self._scoring)
                for location in sorted(locations)
            ),
            default=Decimal("0"),
        )
        score = (
            mode_score * self._scoring.location_weights["work_mode"]
            + location_score * self._scoring.location_weights["location"]
        )
        weight = config.dimension_weights[self.dimension_id]
        return DimensionScore(
            dimension_id=self.dimension_id,
            enabled=True,
            score=score,
            weight=weight,
            weighted_score=score * weight,
            evidence_level=None,
            reason="configured_location_work_mode",
        )

    def _mode(self, modes: tuple[WorkMode, ...], job: WorkMode | None) -> Decimal:
        if not modes or job is None or job is WorkMode.UNKNOWN:
            return self._scoring.work_mode["unknown_or_absent"]
        if job in modes:
            return self._scoring.work_mode["exact_match"]
        if WorkMode.REMOTE in modes and job is WorkMode.HYBRID:
            return self._scoring.work_mode["remote_candidate_for_hybrid_job"]
        if WorkMode.HYBRID in modes and job is WorkMode.ONSITE:
            return self._scoring.work_mode["hybrid_candidate_for_onsite_job"]
        if WorkMode.REMOTE in modes and job is WorkMode.ONSITE:
            return self._scoring.work_mode["remote_candidate_for_onsite_job"]
        return self._scoring.work_mode["incompatible"]


def _location(candidate: str, job: str | None, scoring: DimensionMatchScoring) -> Decimal:
    if job is None:
        return scoring.location["unknown_or_absent"]
    normalized_candidate = location_fold(candidate)
    normalized_job = location_fold(job)
    if normalized_candidate == normalized_job:
        return scoring.location["exact_city_match"]
    candidate_parts, job_parts = _location_parts(candidate), _location_parts(job)
    if len(candidate_parts) >= 3 and len(job_parts) >= 3 and candidate_parts[-2:] == job_parts[-2:]:
        return scoring.location["same_region_match"]
    if candidate_parts and job_parts and candidate_parts[-1] == job_parts[-1]:
        return scoring.location["same_country_match"]
    return scoring.location["no_match"]


def _location_parts(value: str) -> tuple[str, ...]:
    """Read explicitly structured city, region, country fields without inference."""
    return tuple(part.strip().casefold() for part in value.split(",") if part.strip())
