from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4] / "config"


def test_evidence_configs_are_versioned_and_complete() -> None:
    units = yaml.safe_load((ROOT / "quantity_units.yaml").read_text(encoding="utf-8"))
    exclusions = yaml.safe_load((ROOT / "proficiency_exclusions.yaml").read_text(encoding="utf-8"))
    assert units["version"] == "units@1"
    groups = (
        "percent_tokens",
        "currency_symbols",
        "currency_codes",
        "magnitude",
        "time",
        "throughput",
        "data",
        "electrical",
        "count",
    )
    assert all(units[group] for group in groups)
    assert exclusions["version"] == "proficiency_exclusions@1"
    assert {"expert", "advanced", "extensive"} <= set(exclusions["words"])
