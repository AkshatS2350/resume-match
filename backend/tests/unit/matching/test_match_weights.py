from decimal import Decimal
from pathlib import Path

from resumematch.matching.config import load_match_weights


def test_match_weights_have_all_dimensions_and_sum_to_100() -> None:
    config = Path(__file__).resolve().parents[4] / "config" / "match_weights.yaml"
    weights = load_match_weights(config)
    assert len(weights) == 7
    assert sum(weights.values(), Decimal("0")) == Decimal("100")
