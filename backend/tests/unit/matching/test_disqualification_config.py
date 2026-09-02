from pathlib import Path

import yaml


def test_disqualification_and_relevance_configs_are_complete() -> None:
    root = Path(__file__).resolve().parents[4] / "config"
    disqualification = yaml.safe_load((root / "disqualification.yaml").read_text(encoding="utf-8"))
    relevance = yaml.safe_load((root / "relevance_rule.yaml").read_text(encoding="utf-8"))
    assert 1 <= disqualification["unmet_required_threshold"] <= 10
    assert 0 <= disqualification["seniority_tolerance_years"] <= 10
    assert len(disqualification["excluded_requirement_categories"]) == 4
    assert relevance["version"] == "relevance_rule@all_dated_v1"
