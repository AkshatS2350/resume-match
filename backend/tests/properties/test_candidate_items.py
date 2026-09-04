from decimal import Decimal

from resumematch.core.schemas.candidate import (
    AchievementItem,
    CertificationItem,
    DegreeLevel,
    EducationItem,
    ExperienceItem,
    ProjectItem,
    SkillItem,
    UnclassifiedItem,
    YearMonth,
)


def _base() -> dict[str, object]:
    return {
        "item_id": "item-1", "origin": "user_provided",
        "extraction_confidence": Decimal("1.00"), "confidence_inputs": (),
        "provenance": None, "source_text": "source",
    }


def test_each_candidate_item_round_trips_and_experience_keeps_date_fields() -> None:
    start = YearMonth(year=2020, month=1)
    items = (
        SkillItem(**_base(), surface="Python", canonical_skill_id="python"),
        ExperienceItem(
            **_base(), employer="Example", title="Engineer", start_date=start,
            end_date=None, is_present=True, duration_months=12, description="Built systems",
            date_conflict=False,
        ),
        EducationItem(
            **_base(), institution="Example", degree_level=DegreeLevel.BACHELORS,
            field_of_study="CS",
            start_date=start, end_date=start, coursework=("Algorithms",),
        ),
        ProjectItem(**_base(), name="Project", description="Built it"),
        CertificationItem(**_base(), name="Certificate", issuer="Issuer", issued=start),
        AchievementItem(**_base(), text="Achievement"),
        UnclassifiedItem(**_base(), text="Unclassified"),
    )
    assert all(type(item).model_validate_json(item.model_dump_json()) == item for item in items)
    experience = items[1]
    assert isinstance(experience, ExperienceItem)
    assert experience.duration_months == 12 and experience.date_conflict is False
