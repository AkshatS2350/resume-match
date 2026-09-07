from decimal import Decimal

import pytest

from resumematch.resume.structure.confidence import extraction_confidence


def test_confidence_records_configured_positive_contributions() -> None:
    result = extraction_confidence(
        heading_matched=True,
        layout_clean=True,
        pattern_complete=True,
        date_parsed=True,
        unclassified_section=False,
        encoding_anomaly=False,
        table_spliced=False,
    )

    assert result.value == Decimal("1.00")
    assert result.inputs == (
        "base",
        "heading_matched",
        "layout_clean",
        "pattern_complete",
        "date_parsed",
    )


def test_confidence_applies_negative_contributions_and_clamps() -> None:
    result = extraction_confidence(
        heading_matched=False,
        layout_clean=False,
        pattern_complete=False,
        date_parsed=False,
        unclassified_section=True,
        encoding_anomaly=True,
        table_spliced=True,
    )

    assert result.value == Decimal("0.00")
    assert result.inputs == ("base", "unclassified_section", "encoding_anomaly", "table_spliced")


def test_user_provided_confidence_is_one_with_no_extraction_inputs() -> None:
    result = extraction_confidence(
        heading_matched=False,
        layout_clean=False,
        pattern_complete=False,
        date_parsed=False,
        unclassified_section=True,
        encoding_anomaly=True,
        table_spliced=True,
        user_provided=True,
    )

    assert result.value == Decimal("1.00")
    assert result.inputs == ("user_provided",)


@pytest.mark.parametrize(
    ("flag", "expected"),
    [
        ("heading_matched", Decimal("0.70")),
        ("layout_clean", Decimal("0.60")),
        ("pattern_complete", Decimal("0.65")),
        ("date_parsed", Decimal("0.55")),
        ("unclassified_section", Decimal("0.25")),
        ("encoding_anomaly", Decimal("0.35")),
        ("table_spliced", Decimal("0.40")),
    ],
)
def test_each_extraction_confidence_contribution_has_its_documented_value(
    flag: str, expected: Decimal
) -> None:
    values = {
        "heading_matched": False,
        "layout_clean": False,
        "pattern_complete": False,
        "date_parsed": False,
        "unclassified_section": False,
        "encoding_anomaly": False,
        "table_spliced": False,
    }
    values[flag] = True

    result = extraction_confidence(**values)

    assert result.value == expected
    assert result.inputs == ("base", flag)
