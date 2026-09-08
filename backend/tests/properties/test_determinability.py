from decimal import Decimal
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

from resumematch.core.schemas.candidate import DegreeLevel
from resumematch.core.schemas.rubric import Signal, SignalTargetRef
from resumematch.core.schemas.version_stamp import VersionStamp
from resumematch.rubric.resolver_config import load_signal_resolver_config
from resumematch.rubric.resolvers import RESOLVERS
from resumematch.rubric.resolvers.context import (
    CertificationEvidence,
    ClosedFlagEvidence,
    EducationEvidence,
    ExperienceEvidence,
    ScoringContext,
    SkillEvidence,
)

ROOT = Path(__file__).resolve().parents[3]
CONFIG = load_signal_resolver_config(ROOT / "config" / "signal_resolvers.yaml")


def _stamp() -> VersionStamp:
    return VersionStamp(
        schema_version="version_stamp/1",
        engine_version="test",
        rubric_id="r",
        rubric_version="1",
        rubric_status="draft",
        alias_file_version="skills@1",
        evidence_multiplier_version="evidence@1",
        match_weight_version=None,
        threshold_version=None,
        confidence_weight_version=None,
        pattern_set_version=None,
        delimitation_version=None,
        relevance_rule_version=None,
    )


def _signal(kind: str, target_type: str, target_id: str) -> Signal:
    return Signal.model_validate(
        {
            "signal_id": f"{kind}-{target_id}",
            "type": kind,
            "target": {"target_type": target_type, "target_id": target_id},
            "weight": "1",
            "min_evidence_level": 1,
            "required": False,
        }
    )


def _context(
    target: SignalTargetRef, *, confirmed: bool = False, confidence: Decimal = Decimal("0.90")
) -> ScoringContext:
    return ScoringContext(
        rubric_id="r",
        rubric_version="1",
        target_domain_id="d",
        target_role_id="role",
        expected_targets=(target,),
        config_versions=_stamp(),
        candidate_confirmed=confirmed,
        resolver_config=CONFIG,
        skills=(
            SkillEvidence(
                canonical_skill_id="python", item_id="skill", extraction_confidence=confidence
            ),
        ),
        experience=(
            ExperienceEvidence(
                item_id="experience", extraction_confidence=confidence, total_months=12
            ),
        ),
        education=(
            EducationEvidence(
                item_id="education",
                extraction_confidence=confidence,
                degree_level=DegreeLevel.BACHELORS,
                field_id=None,
            ),
        ),
        certifications=(
            CertificationEvidence(
                item_id="cert",
                extraction_confidence=confidence,
                canonical_certification_id="cfa_level_1",
            ),
        ),
        flags=(
            ClosedFlagEvidence(
                flag_id="quantified_impact",
                item_id="flag",
                value=True,
                extraction_confidence=confidence,
            ),
        ),
    )


def test_each_closed_resolver_uses_configured_evidence_level() -> None:
    cases = (
        ("skill", "canonical_skill", "python", 2),
        ("experience_band", "experience_band", "entry", 3),
        ("education", "education_requirement", "any_degree", 1),
        ("certification", "certification", "cfa_level_1", 3),
        ("flag", "closed_flag", "quantified_impact", 3),
    )
    for kind, target_type, target_id, expected_level in cases:
        signal = _signal(kind, target_type, target_id)
        resolved = RESOLVERS[kind].resolve(signal, _context(signal.target))
        assert resolved.evidence_level == expected_level
        assert resolved.determinability == "determinable"


def test_unknown_target_and_absent_skill_are_truthful() -> None:
    known = _signal("skill", "canonical_skill", "python")
    unknown = _signal("skill", "canonical_skill", "unrecognized")
    assert (
        RESOLVERS["skill"].resolve(unknown, _context(known.target)).determinability
        == "indeterminate"
    )
    empty = _context(known.target).model_copy(update={"skills": ()})
    assert RESOLVERS["skill"].resolve(known, empty).determinability == "determinable"
    assert RESOLVERS["skill"].resolve(known, empty).evidence_level == 0


@given(st.booleans())
def test_sole_low_confidence_item_is_indeterminate_unless_confirmed(confirmed: bool) -> None:
    signal = _signal("skill", "canonical_skill", "python")
    resolved = RESOLVERS["skill"].resolve(
        signal,
        _context(signal.target, confirmed=confirmed, confidence=Decimal("0.59")),
    )
    assert resolved.determinability == ("determinable" if confirmed else "indeterminate")
