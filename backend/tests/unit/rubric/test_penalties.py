import pytest
from pydantic import ValidationError

from resumematch.rubric.penalties import (
    PenaltyApplicabilityContext,
    SectionItemCount,
    no_item_in_section,
    total_experience_below,
)


def _context(months: int | None = 11) -> PenaltyApplicabilityContext:
    return PenaltyApplicabilityContext(
        section_item_counts=tuple(
            SectionItemCount(section_id=section, count=0 if section == "experience" else 1)
            for section in (
                "skills",
                "experience",
                "education",
                "projects",
                "certifications",
                "achievements",
                "unclassified",
            )
        ),
        total_relevant_experience_months=months,
        context_version="penalty_applicability@1",
    )


def test_penalty_applicability_uses_only_closed_structured_facts() -> None:
    context = _context()
    assert no_item_in_section(context, "experience")
    assert not no_item_in_section(context, "skills")
    assert total_experience_below(context, 12)
    assert not total_experience_below(context, 11)
    assert not total_experience_below(_context(None), 12)


def test_penalty_context_rejects_unknown_or_negative_values() -> None:
    with pytest.raises(ValidationError):
        SectionItemCount(section_id="summary", count=0)
    with pytest.raises(ValidationError):
        SectionItemCount(section_id="skills", count=-1)
    with pytest.raises(ValueError):
        total_experience_below(_context(), -1)
