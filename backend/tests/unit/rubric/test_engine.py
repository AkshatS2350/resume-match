from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

import resumematch.rubric.engine as engine_module
from resumematch.core.errors import ErrorCode, PipelineError
from resumematch.core.schemas.candidate import (
    CandidateProfile,
    SkillItem,
    StructuredResume,
    TargetConstraints,
)
from resumematch.core.schemas.rubric import RoleRubric, RubricPenalty
from resumematch.core.schemas.version_stamp import VersionStamp
from resumematch.rubric.engine import RubricEngine
from resumematch.rubric.penalties import PenaltyApplicabilityContext, SectionItemCount
from resumematch.rubric.resolver_config import load_signal_resolver_config
from resumematch.rubric.resolvers import RESOLVERS, ResolvedSignal
from resumematch.rubric.resolvers.context import scoring_context_from_profile

ROOT = Path(__file__).resolve().parents[4]


def _rubric(weight: str = "100") -> RoleRubric:
    return RoleRubric.model_validate(
        {
            "schema_version": "role_rubric/1",
            "rubric_id": "r",
            "role_id": "role",
            "role_family": "family",
            "domain_id": "domain",
            "seniority_id": "entry",
            "rubric_version": "1",
            "status": "draft",
            "weight_basis": "test",
            "weight_basis_note": "test",
            "experience_bands": [],
            "education_expectations": {
                "min_degree_level": "bachelors",
                "preferred_fields": [],
                "required": False,
            },
            "certification_expectations": [],
            "categories": [{"category_id": "empty", "weight": weight, "signals": []}],
            "penalties": [],
        }
    )


def _penalties() -> PenaltyApplicabilityContext:
    return PenaltyApplicabilityContext(
        section_item_counts=tuple(
            SectionItemCount(section_id=identifier, count=0)
            for identifier in (
                "skills",
                "experience",
                "education",
                "projects",
                "certifications",
                "achievements",
                "unclassified",
            )
        ),
        total_relevant_experience_months=None,
        context_version="penalty_applicability@1",
    )


def _stamp() -> VersionStamp:
    return VersionStamp(
        schema_version="version_stamp/1",
        engine_version="test",
        rubric_id="r",
        rubric_version="1",
        rubric_status="draft",
        alias_file_version="skills@1",
        evidence_multiplier_version="evidence_multipliers@1",
        match_weight_version=None,
        threshold_version=None,
        confidence_weight_version=None,
        pattern_set_version=None,
        delimitation_version=None,
        relevance_rule_version=None,
    )


def _profile() -> CandidateProfile:
    return CandidateProfile(
        schema_version="candidate_profile/1",
        profile_revision=1,
        session_start_date=date(2026, 1, 1),
        resume=StructuredResume(
            schema_version="structured_resume/1",
            summary=None,
            skills=(
                SkillItem(
                    item_id="skill-python",
                    origin="user_provided",
                    extraction_confidence=Decimal("1.00"),
                    confidence_inputs=(),
                    provenance=None,
                    source_text="candidate-derived marker",
                    surface="Python",
                    canonical_skill_id="python",
                ),
            ),
            experience=(),
            education=(),
            projects=(),
            certifications=(),
            achievements=(),
            unclassified=(),
        ),
        target=TargetConstraints(
            domain_id="domain", role_id="role", seniority_id="entry", locations=(), work_modes=()
        ),
        confirmed=True,
    )


def test_scoring_context_boundary_uses_only_structured_non_text_facts() -> None:
    context = scoring_context_from_profile(
        _profile(),
        _scoring_rubric(["python"]),
        load_signal_resolver_config(ROOT / "config" / "signal_resolvers.yaml"),
        _stamp(),
    )
    assert context.skills[0].canonical_skill_id == "python"
    assert "candidate-derived marker" not in context.model_dump_json()


def test_engine_scores_a_profile_through_the_raw_text_free_context_boundary() -> None:
    result = RubricEngine().score_profile(
        _profile(),
        _scoring_rubric(["python"]),
        load_signal_resolver_config(ROOT / "config" / "signal_resolvers.yaml"),
        _stamp(),
        {0: Decimal("0"), 1: Decimal("0.4"), 2: Decimal("0.7"), 3: Decimal("1")},
        total_relevant_experience_months=None,
    )
    assert result.score == 70
    assert result.reason == "scored"
    assert result.versions.engine_version == "rubric_engine@1"
    assert result.versions.rubric_id == "r"
    assert result.versions.rubric_version == "1"


def test_zero_attainable_category_scores_zero_without_division() -> None:
    result = RubricEngine().score(
        _rubric(),
        _Context({}),
        {0: Decimal("0"), 1: Decimal("0.4"), 2: Decimal("0.7"), 3: Decimal("1")},
        _penalties(),
    )
    assert result.score == 0
    assert result.reason == "no_evidence"
    assert result.matched_signal_count == 0
    assert result.categories[0].score == 0


class _Resolver:
    signal_type = "skill"

    def resolve(self, signal: object, context: object) -> ResolvedSignal:
        identifier = getattr(signal, "signal_id")
        levels = getattr(context, "levels")
        return ResolvedSignal(levels[identifier], "determinable", (identifier,))


class _RaisingResolver:
    signal_type = "skill"

    def resolve(self, signal: object, context: object) -> ResolvedSignal:
        raise RuntimeError("candidate-derived marker must not escape")


class _Context:
    def __init__(self, levels: dict[str, int]) -> None:
        self.levels = levels
        self.config_versions = _stamp()


def _scoring_rubric(signals: list[str], *, group: bool = False) -> RoleRubric:
    return RoleRubric.model_validate(
        {
            "schema_version": "role_rubric/1",
            "rubric_id": "r",
            "role_id": "role",
            "role_family": "family",
            "domain_id": "domain",
            "seniority_id": "entry",
            "rubric_version": "1",
            "status": "draft",
            "weight_basis": "test",
            "weight_basis_note": "test",
            "experience_bands": [],
            "education_expectations": {
                "min_degree_level": "bachelors",
                "preferred_fields": [],
                "required": False,
            },
            "certification_expectations": [],
            "categories": [
                {
                    "category_id": "core",
                    "weight": "100",
                    "signals": [
                        {
                            "signal_id": identifier,
                            "type": "skill",
                            "target": {"target_type": "canonical_skill", "target_id": "python"},
                            "weight": "10",
                            "min_evidence_level": 1,
                            "required": False,
                        }
                        for identifier in signals
                    ],
                    "alternative_groups": [
                        {
                            "group_id": "choice",
                            "display": "choice",
                            "weight": "10",
                            "min_evidence_level": 1,
                            "members": signals,
                        }
                    ]
                    if group
                    else [],
                }
            ],
            "penalties": [],
        }
    )


@given(st.permutations(("a", "b", "c")))
def test_engine_is_invariant_to_declared_signal_order(order: tuple[str, ...]) -> None:
    original = RESOLVERS["skill"]
    RESOLVERS["skill"] = _Resolver()
    try:
        scores = RubricEngine().score(
            _scoring_rubric(list(order)),
            _Context({"a": 1, "b": 2, "c": 3}),
            {0: Decimal("0"), 1: Decimal("0.4"), 2: Decimal("0.7"), 3: Decimal("1")},
            _penalties(),
        )
    finally:
        RESOLVERS["skill"] = original
    assert scores.score == 70


def test_alternative_group_credits_only_the_highest_qualifying_member(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(RESOLVERS, "skill", _Resolver())
    result = RubricEngine().score(
        _scoring_rubric(["a", "b"], group=True),
        _Context({"a": 1, "b": 3}),
        {0: Decimal("0"), 1: Decimal("0.4"), 2: Decimal("0.7"), 3: Decimal("1")},
        _penalties(),
    )
    assert result.score == 80


def test_alternative_group_tie_credits_the_lexicographically_first_member(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(RESOLVERS, "skill", _Resolver())
    result = RubricEngine().score(
        _scoring_rubric(["a", "b"], group=True),
        _Context({"a": 3, "b": 3}),
        {0: Decimal("0"), 1: Decimal("0.4"), 2: Decimal("0.7"), 3: Decimal("1")},
        _penalties(),
    )
    assert result.categories[0].alternative_credits == (("choice", "a"),)


def test_penalties_apply_in_stable_identifier_order(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(RESOLVERS, "skill", _Resolver())
    penalties = (
        RubricPenalty.model_validate(
            {
                "penalty_id": "z-last",
                "applies_to_category": "core",
                "points": "10",
                "condition": {"kind": "no_item_in_section", "section": "experience"},
            }
        ),
        RubricPenalty.model_validate(
            {
                "penalty_id": "a-first",
                "applies_to_category": "core",
                "points": "5",
                "condition": {"kind": "total_experience_below", "threshold_months": 12},
            }
        ),
    )
    rubric = _scoring_rubric(["a"]).model_copy(update={"penalties": penalties})
    result = RubricEngine().score(
        rubric,
        _Context({"a": 1}),
        {0: Decimal("0"), 1: Decimal("0.4"), 2: Decimal("0.7"), 3: Decimal("1")},
        _penalties().model_copy(update={"total_relevant_experience_months": 11}),
    )
    assert result.score == 25
    assert result.categories[0].applied_penalty_ids == ("a-first", "z-last")


@pytest.mark.determinism
def test_engine_repeated_runs_are_byte_equivalent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(RESOLVERS, "skill", _Resolver())
    engine = RubricEngine()
    inputs = (
        _scoring_rubric(["a", "b"], group=True),
        _Context({"a": 1, "b": 3}),
        {0: Decimal("0"), 1: Decimal("0.4"), 2: Decimal("0.7"), 3: Decimal("1")},
        _penalties(),
    )
    assert engine.score(*inputs) == engine.score(*inputs)


def test_matched_signal_zeroed_by_penalty_has_distinct_reason(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(RESOLVERS, "skill", _Resolver())
    penalty = RubricPenalty.model_validate(
        {
            "penalty_id": "zero",
            "applies_to_category": "core",
            "points": "100",
            "condition": {"kind": "no_item_in_section", "section": "experience"},
        }
    )
    rubric = _scoring_rubric(["a"]).model_copy(update={"penalties": (penalty,)})
    result = RubricEngine().score(
        rubric,
        _Context({"a": 1}),
        {0: Decimal("0"), 1: Decimal("0.4"), 2: Decimal("0.7"), 3: Decimal("1")},
        _penalties(),
    )
    assert result.score == 0
    assert result.reason == "below_reportable_or_penalized"
    assert result.matched_signal_count == 1


def test_resolver_failure_is_mapped_to_a_safe_scoring_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(RESOLVERS, "skill", _RaisingResolver())
    events: list[tuple[str, dict[str, str | int]]] = []

    def capture(name: str, **labels: str | int) -> str:
        events.append((name, labels))
        return ""

    monkeypatch.setattr(engine_module, "emit_metric", capture)
    with pytest.raises(PipelineError) as raised:
        RubricEngine().score(
            _scoring_rubric(["a"]),
            _Context({"a": 1}),
            {0: Decimal("0"), 1: Decimal("0.4"), 2: Decimal("0.7"), 3: Decimal("1")},
            _penalties(),
        )
    assert raised.value.code is ErrorCode.SCORING_FAILED
    assert "candidate-derived marker" not in str(raised.value)
    assert events == [
        ("scoring_exception_total", {"rubric_id": "r", "engine_version": "rubric_engine@1"})
    ]
