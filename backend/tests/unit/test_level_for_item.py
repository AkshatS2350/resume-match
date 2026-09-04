from datetime import date
from decimal import Decimal

from resumematch.core.schemas.candidate import (
    ExperienceItem,
    ProjectItem,
    Provenance,
    SkillItem,
    YearMonth,
)


def _item(**changes: object) -> ExperienceItem:
    item = ExperienceItem(
        item_id="experience-1",
        origin="extracted",
        extraction_confidence=Decimal("1.00"),
        confidence_inputs=(),
        provenance=Provenance(
            section_id="experience", block_ids=("b",), start_offset=0, end_offset=1
        ),
        source_text="Python",
        employer="Acme",
        title="Python Engineer",
        start_date=YearMonth(year=2024, month=1),
        end_date=YearMonth(year=2024, month=2),
        is_present=False,
        duration_months=1,
        description="Built Python services.",
        date_conflict=False,
    )
    return item.model_copy(update=changes)


def test_level_for_experience_requires_all_level_three_conditions() -> None:
    from resumematch.rubric.evidence import level_for_item

    result = level_for_item(_item(employer=" "), "python", date(2026, 9, 2), 1)

    assert result.level == 2
    assert result.unmet_level3_condition == "employer"


def test_level_for_experience_is_three_when_the_skill_is_in_title_or_description() -> None:
    from resumematch.rubric.evidence import level_for_item

    result = level_for_item(_item(), "python", date(2026, 9, 2), 1)

    assert result.level == 3


def test_level_for_experience_requires_resolvable_dates() -> None:
    from resumematch.rubric.evidence import level_for_item

    result = level_for_item(_item(start_date=None), "python", date(2026, 9, 2), 1)

    assert result.level == 2
    assert result.unmet_level3_condition == "dates"


def test_level_for_present_experience_uses_the_session_date() -> None:
    from resumematch.rubric.evidence import level_for_item

    result = level_for_item(
        _item(end_date=None, is_present=True, start_date=YearMonth(year=2027, month=1)),
        "python",
        date(2026, 9, 2),
        1,
    )

    assert result.level == 2
    assert result.unmet_level3_condition == "duration"


def test_level_for_experience_requires_a_month_of_duration() -> None:
    from resumematch.rubric.evidence import level_for_item

    result = level_for_item(_item(duration_months=0), "python", date(2026, 9, 2), 1)

    assert result.level == 2
    assert result.unmet_level3_condition == "duration"


def test_level_for_experience_requires_a_title_or_description_mention() -> None:
    from resumematch.rubric.evidence import level_for_item

    result = level_for_item(
        _item(title="Engineer", description="Built services"), "python", date(2026, 9, 2), 1
    )

    assert result.level == 2
    assert result.unmet_level3_condition == "mention"


def test_level_for_experience_demotes_an_item_with_more_than_twenty_skills() -> None:
    from resumematch.rubric.evidence import level_for_item

    result = level_for_item(_item(), "python", date(2026, 9, 2), 21)

    assert result.level == 2
    assert result.demotion_reason == "too_many_skills"


def test_employer_text_cannot_supply_a_skill_mention() -> None:
    from resumematch.rubric.evidence import level_for_item

    result = level_for_item(
        _item(employer="Oracle", title="Engineer", description="Built services"),
        "oracle",
        date(2026, 9, 2),
        1,
    )

    assert result.level == 2
    assert result.unmet_level3_condition == "mention"


def test_proficiency_word_removal_does_not_change_the_level() -> None:
    from resumematch.rubric.evidence import level_for_item

    expert = level_for_item(
        _item(description="Built expert Python services."), "python", date(2026, 9, 2), 1
    )
    plain = level_for_item(
        _item(description="Built Python services."), "python", date(2026, 9, 2), 1
    )

    assert expert.level == plain.level == 3


def test_level_for_project_is_two() -> None:
    from resumematch.rubric.evidence import level_for_item

    item = ProjectItem(
        item_id="project-1",
        origin="user_provided",
        extraction_confidence=Decimal("1.00"),
        confidence_inputs=(),
        provenance=None,
        source_text="Python",
        name="Project",
        description="Python",
    )

    assert level_for_item(item, "python", date(2026, 9, 2), 1).level == 2


def test_level_for_skill_item_is_one() -> None:
    from resumematch.rubric.evidence import level_for_item

    item = SkillItem(
        item_id="skill-1",
        origin="user_provided",
        extraction_confidence=Decimal("1.00"),
        confidence_inputs=(),
        provenance=None,
        source_text="Python",
        surface="Python",
        canonical_skill_id="python",
    )

    assert level_for_item(item, "python", date(2026, 9, 2), 1).level == 1
