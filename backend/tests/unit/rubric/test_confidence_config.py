from decimal import Decimal
from pathlib import Path

from resumematch.rubric.confidence_config import load_confidence_config


def test_confidence_config_loads_exact_weights_and_six_sections() -> None:
    path = Path(__file__).resolve().parents[4] / "config" / "confidence_weights.yaml"
    config = load_confidence_config(path)
    assert config["readiness_weights"]["signal_coverage"] == Decimal("0.45")  # type: ignore[index]
    assert len(config["profile_sections"]) == 6  # type: ignore[arg-type]
    assert "summary" not in config["profile_sections"]  # type: ignore[operator]
