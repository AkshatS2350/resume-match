from datetime import UTC, date, datetime

from resumematch.core.clock import FixedClock


def test_fixed_clock_repeats_configured_instant() -> None:
    instant = datetime(2026, 9, 1, 12, tzinfo=UTC)
    clock = FixedClock(instant)
    assert clock.now() == instant
    assert clock.now() == instant
    assert clock.today() == date(2026, 9, 1)
