from datetime import date

import pytest

from resumematch.resume.structure.dates import parse_experience_dates


@pytest.mark.parametrize(
    "text",
    [
        "Jan 2023 – Present",
        "2021-2022",
        "06/2020 to 08/2020",
        "January 2020 - March 2021",
        "Feb 2019–Apr 2020",
        "2018 to 2019",
        "03/2018 - 04/2018",
        "May 2017 - Present",
        "2020–Present",
        "September 2021 to December 2021",
        "07/2022 - Present",
        "2016 - 2017",
    ],
)
def test_recognized_date_ranges_parse_deterministically(text: str) -> None:
    parsed = parse_experience_dates(text, date(2026, 1, 1))
    assert parsed.start_date is not None
    assert parsed.duration_months is not None and parsed.duration_months >= 1


def test_inverted_range_is_recorded_without_raising() -> None:
    parsed = parse_experience_dates("Dec 2023 - Jan 2023", date(2026, 1, 1))
    assert parsed.date_conflict is True
    assert parsed.duration_months is None
