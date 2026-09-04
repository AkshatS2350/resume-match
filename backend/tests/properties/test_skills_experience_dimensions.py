"""Properties for normalized deterministic Skills and Experience scorers."""

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from resumematch.core.schemas.candidate import (
    CandidateProfile,
    ExperienceItem,
    Provenance,
    StructuredResume,
    TargetConstraints,
    YearMonth,
)
from resumematch.core.schemas.job import ExtractedRequirement, JobPosting
from resumematch.matching.config import load_match_config
from resumematch.matching.contracts import (
    DimensionId,
    DimensionScore,
    EvidenceIndex,
    EvidenceLevel,
    EvidenceRef,
)
from resumematch.matching.dimensions.experience import ExperienceDimensionScorer
from resumematch.matching.dimensions.skills import SkillsDimensionScorer
from resumematch.matching.reporting import reported_dimension_score
from resumematch.rubric.multipliers import MultiplierConfigError, load_multipliers

_ROOT = Path(__file__).parents[3]
_CONFIG = load_match_config(
    _ROOT / "config" / "matching_contract.yaml", _ROOT / "config" / "match_weights.yaml"
)
_MULTIPLIERS = load_multipliers(_ROOT / "config" / "evidence_multipliers.yaml")


def _profile(*, months: int = 24) -> CandidateProfile:
    experience = ExperienceItem(
        item_id="experience-1",
        origin="extracted",
        extraction_confidence=Decimal("1.00"),
        confidence_inputs=(),
        provenance=Provenance(
            section_id="experience", block_ids=("block-1",), start_offset=0, end_offset=1
        ),
        source_text="experience",
        employer="Example Organization",
        title="Engineer",
        start_date=YearMonth(year=2024, month=1),
        end_date=YearMonth(year=2024 + months // 12, month=(months % 12) + 1),
        is_present=False,
        duration_months=months,
        description="",
        date_conflict=False,
    )
    return CandidateProfile(
        schema_version="candidate_profile/1",
        profile_revision=1,
        session_start_date=date(2026, 1, 1),
        resume=StructuredResume(
            schema_version="structured_resume/1",
            summary=None,
            skills=(),
            experience=(experience,),
            education=(),
            projects=(),
            certifications=(),
            achievements=(),
            unclassified=(),
        ),
        target=TargetConstraints(
            domain_id="unknown",
            role_id="unknown",
            seniority_id="unknown",
            locations=(),
            work_modes=(),
        ),
        confirmed=True,
    )


def _posting(requirement_ids: tuple[str, ...], *, minimum: Decimal = Decimal("2")) -> JobPosting:
    requirements = tuple(
        ExtractedRequirement(
            requirement_id=identifier,
            classification="required",
            low_confidence=False,
            canonical_skill_id=identifier,
            unit_text=identifier,
            start_offset=0,
            end_offset=1,
            unit_id=f"unit-{identifier}",
            excluded_category=None,
            pattern_set_version="patterns@1",
            delimitation_version="delimitation@1",
        )
        for identifier in requirement_ids
    )
    return JobPosting(
        schema_version="job_posting/1",
        internal_id="posting-1",
        source_id="fixture",
        source_external_id="posting-1",
        company="Example Organization",
        raw_title="Engineer",
        raw_description="",
        apply_url="https://example.invalid/jobs/posting-1",
        min_experience_years=minimum,
        requirements=requirements,
        ingested_at=datetime(2026, 1, 1),
    )


def _evidence(levels: dict[str, EvidenceLevel]) -> EvidenceIndex:
    return EvidenceIndex(
        by_requirement_id={
            requirement_id: (
                EvidenceRef(
                    item_id=f"item-{requirement_id}",
                    item_type="experience",
                    evidence_level=level,
                    dimension_id=DimensionId.SKILLS,
                ),
            )
            for requirement_id, level in levels.items()
        },
        evidence_index_version="evidence_index@1",
    )


# Feature: resumematch, Property 1 and Property 27.
@given(st.permutations(("python", "sql", "docker")))
def test_skills_score_is_normalized_and_permutation_invariant(
    requirement_ids: tuple[str, ...],
) -> None:
    scorer = SkillsDimensionScorer(_MULTIPLIERS)
    profile = _profile()
    evidence = _evidence(
        {
            "python": EvidenceLevel.LEVEL_3,
            "sql": EvidenceLevel.LEVEL_2,
            "docker": EvidenceLevel.LEVEL_1,
        }
    )

    score = scorer.score(profile, _posting(requirement_ids), evidence, _CONFIG)

    assert score.score is not None
    assert Decimal("0") <= score.score <= Decimal("1")
    assert score.score == Decimal("0.70")


def test_level_three_skill_scores_strictly_above_level_one() -> None:
    scorer = SkillsDimensionScorer(_MULTIPLIERS)
    profile = _profile()
    posting = _posting(("python",))

    level_one = scorer.score(
        profile, posting, _evidence({"python": EvidenceLevel.LEVEL_1}), _CONFIG
    )
    level_three = scorer.score(
        profile, posting, _evidence({"python": EvidenceLevel.LEVEL_3}), _CONFIG
    )

    assert level_one.score is not None and level_three.score is not None
    assert level_three.score > level_one.score


@given(st.decimals(min_value=Decimal("0.1"), max_value=Decimal("20"), places=1))
def test_experience_score_is_normalized_and_capped(minimum: Decimal) -> None:
    score = ExperienceDimensionScorer().score(
        _profile(),
        _posting(("python",), minimum=minimum),
        EvidenceIndex(evidence_index_version="evidence_index@1"),
        _CONFIG,
    )

    assert score.score is not None
    assert Decimal("0") <= score.score <= Decimal("1")


def test_reporting_conversion_is_half_up_and_disabled_scores_remain_null() -> None:
    assert reported_dimension_score(Decimal("0.845")) == 85
    disabled = DimensionScore(
        dimension_id=DimensionId.SKILLS,
        enabled=False,
        weight=Decimal("0.30"),
        evidence_level=None,
        reason="insufficient_job_data",
    )

    assert disabled.score is None
    assert reported_dimension_score(disabled.score) is None


def test_multiplier_loader_rejects_a_missing_level_two(tmp_path: Path) -> None:
    path = tmp_path / "multipliers.yaml"
    path.write_text(
        'version: evidence_multipliers@1\nmultipliers: {0: "0.00", 1: "0.40", 3: "1.00"}\n'
    )

    with pytest.raises(MultiplierConfigError, match="levels"):
        load_multipliers(path)
