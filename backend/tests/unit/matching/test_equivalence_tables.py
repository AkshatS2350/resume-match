from pathlib import Path

import yaml


def test_equivalence_tables_preserve_asymmetry_and_fallbacks() -> None:
    root = Path(__file__).resolve().parents[4] / "config"
    roles = yaml.safe_load((root / "role_family_equivalence.yaml").read_text(encoding="utf-8"))
    domains = yaml.safe_load((root / "company_domain_mapping.yaml").read_text(encoding="utf-8"))
    assert roles["pairs"]["embedded_firmware"]["software_engineering"] == 70
    assert roles["pairs"]["software_engineering"]["embedded_firmware"] == 65
    assert domains["by_role_family_fallback"]["finance"] == "financial_services"
    assert domains["by_role_family_fallback"]["unknown"] == "unknown"
