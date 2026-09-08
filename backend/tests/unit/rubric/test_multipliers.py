from decimal import Decimal
from pathlib import Path

from resumematch.rubric.multipliers import load_multipliers


def test_multipliers_are_exact_decimals() -> None:
    path = Path(__file__).resolve().parents[4] / "config" / "evidence_multipliers.yaml"
    values = load_multipliers(path)
    assert values == {
        0: Decimal("0.00"),
        1: Decimal("0.40"),
        2: Decimal("0.70"),
        3: Decimal("1.00"),
    }
