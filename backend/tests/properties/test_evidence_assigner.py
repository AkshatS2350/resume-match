from datetime import date
from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from resumematch.core.schemas.candidate import (
    CandidateProfile,
    ExperienceItem,
    SkillItem,
    StructuredResume,
    YearMonth,
)


def _profile() -> CandidateProfile:
    resume = StructuredResume(
        schema_version="structured_resume/1",
        summary=None,
        skills=(
            SkillItem(
                item_id="skill",
                source_text="Python",
                surface="Python",
                canonical_skill_id="python",
                origin="user_provided",
                extraction_confidence=Decimal("1.00"),
                confidence_inputs=(),
                provenance=None,
            ),
        ),
        experience=(
            ExperienceItem(
                item_id="experience",
                source_text="Python",
                employer="Acme",
                title="Python Engineer",
                start_date=YearMonth(year=2024, month=1),
                end_date=YearMonth(year=2024, month=2),
                is_present=False,
                duration_months=1,
                description="Python services",
                date_conflict=False,
                origin="user_provided",
                extraction_confidence=Decimal("1.00"),
                confidence_inputs=(),
                provenance=None,
            ),
        ),
        education=(),
        projects=(),
        certifications=(),
        achievements=(),
        unclassified=(),
    )
    return CandidateProfile(
        schema_version="candidate_profile/1",
        profile_revision=1,
        session_start_date=date(2026, 1, 1),
        resume=resume,
        target=None,
        confirmed=True,
    )


def test_assigner_is_total_and_uses_the_highest_supporting_level() -> None:
    from resumematch.rubric.evidence import EvidenceAssigner

    assignments = EvidenceAssigner().assign(
        _profile(), frozenset({"python", "sql"}), date(2026, 9, 2)
    )

    assert [(item.canonical_skill_id, item.level) for item in assignments] == [
        ("python", 3),
        ("sql", 0),
    ]
    assert assignments[0].determining_item_id == "experience"
    assert tuple(item.item_id for item in assignments[0].supporting_items) == (
        "experience",
        "skill",
    )


@given(st.permutations(("experience", "second")))
def test_assigner_is_invariant_under_experience_item_permutation(
    order: tuple[str, str],
) -> None:
    from resumematch.rubric.evidence import EvidenceAssigner

    profile = _profile()
    second = profile.resume.experience[0].model_copy(update={"item_id": "second"})
    items = {"experience": profile.resume.experience[0], "second": second}
    permuted = profile.model_copy(
        update={
            "resume": profile.resume.model_copy(
                update={"experience": tuple(items[key] for key in order)}
            )
        }
    )

    assignments = EvidenceAssigner().assign(permuted, frozenset({"python"}), date(2026, 9, 2))

    assert [
        (item.canonical_skill_id, item.level, item.quantified_impact) for item in assignments
    ] == [("python", 3, False)]
