from decimal import Decimal


def test_extract_experience_parses_ranges_and_conflicts() -> None:
    from resumematch.job.requirements.experience import extract_experience

    result = extract_experience("Requires 2-4 years Python and at least 5 years leadership.")

    assert result.minimum_years == Decimal("2")
    assert result.maximum_years == Decimal("4")
    assert result.experience_conflict is True


def test_extract_experience_parses_open_ended_minimum() -> None:
    from resumematch.job.requirements.experience import extract_experience

    result = extract_experience("3+ years of experience required")

    assert result.minimum_years == Decimal("3")
    assert result.maximum_years is None
