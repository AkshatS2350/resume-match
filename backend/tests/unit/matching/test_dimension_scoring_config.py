from decimal import Decimal
from pathlib import Path

import pytest

from resumematch.matching.dimension_scoring import load_dimension_match_scoring


def test_dimension_scoring_configuration_uses_decimal_normalized_weights() -> None:
    config = load_dimension_match_scoring(
        Path(__file__).parents[4] / "config" / "dimension_match_scoring.yaml"
    )

    assert config.seniority["adjacent_level"] == Decimal("0.70")
    assert sum(config.education_weights.values(), Decimal("0")) == Decimal("1.00")
    assert sum(config.location_weights.values(), Decimal("0")) == Decimal("1.00")


def test_dimension_scoring_rejects_out_of_range_decimal(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text(
        "dimension_match_scoring_version: dimension_match_scoring@1\n"
        'seniority: {x: "2.00"}\n'
        "education: {weights: {}, degree_level: {}, field: {}, related_fields: {}}\n"
        "location_work_mode: {weights: {}, work_mode: {}, location: {}}\n"
    )

    with pytest.raises(ValueError, match="seniority"):
        load_dimension_match_scoring(path)
