from decimal import Decimal
from pathlib import Path

from resumematch.core.schemas.candidate import DegreeLevel, SeniorityId, WorkMode
from resumematch.core.schemas.job import EducationRequirement
from resumematch.job.requirements.seniority import load_seniority_mapping
from resumematch.matching.dimension_scoring import load_dimension_match_scoring
from resumematch.matching.dimensions.education import EducationDimensionScorer
from resumematch.matching.dimensions.location_workmode import (
    LocationWorkModeDimensionScorer,
    _location,
)
from resumematch.matching.dimensions.seniority import SeniorityDimensionScorer

_ROOT = Path(__file__).parents[4]
_SCORING = load_dimension_match_scoring(_ROOT / "config" / "dimension_match_scoring.yaml")


def test_seniority_exact_adjacent_two_and_unknown_scores_are_configured() -> None:
    scorer = SeniorityDimensionScorer(
        _SCORING, load_seniority_mapping(_ROOT / "config" / "seniority_mapping.yaml")
    )

    assert scorer._value(SeniorityId.ENTRY, SeniorityId.ENTRY) == Decimal("1.00")
    assert scorer._value(SeniorityId.ENTRY, SeniorityId.MID) == Decimal("0.70")
    assert scorer._value(SeniorityId.ENTRY, SeniorityId.SENIOR) == Decimal("0.40")
    assert scorer._value(SeniorityId.UNKNOWN, SeniorityId.SENIOR) == Decimal("0.00")


def test_education_exact_related_and_absent_values_are_configured() -> None:
    scorer = EducationDimensionScorer(_SCORING)
    requirement = EducationRequirement(
        degree_level=DegreeLevel.BACHELORS,
        field_of_study="Computer Science",
        requirement_kind="required",
    )

    assert scorer._pair(DegreeLevel.MASTERS, "Computer Science", requirement) == Decimal("1.00")
    assert scorer._pair(DegreeLevel.ASSOCIATE, "Information Technology", requirement) == Decimal(
        "0.60"
    )
    assert scorer._pair(DegreeLevel.ASSOCIATE, "Unrelated Field", requirement) == Decimal("0.4200")
    assert scorer._pair(None, None, requirement) == Decimal("0")


def test_location_work_mode_exact_partial_and_unknown_values_are_configured() -> None:
    scorer = LocationWorkModeDimensionScorer(_SCORING)

    assert scorer._mode((WorkMode.HYBRID,), WorkMode.HYBRID) == Decimal("1.00")
    assert scorer._mode((WorkMode.REMOTE,), WorkMode.HYBRID) == Decimal("0.80")
    assert scorer._mode((WorkMode.REMOTE,), WorkMode.ONSITE) == Decimal("0.30")
    assert scorer._mode((), WorkMode.ONSITE) == Decimal("0.00")
    assert _location("austin, texas, us", "austin, texas, us", _SCORING) == Decimal("1.00")
    assert _location("dallas, texas, us", "austin, texas, us", _SCORING) == Decimal("0.70")
    assert _location("london, england, us", "austin, texas, us", _SCORING) == Decimal("0.40")
