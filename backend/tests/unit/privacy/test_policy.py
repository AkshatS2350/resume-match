from decimal import Decimal
from pathlib import Path

import pytest

from resumematch.privacy.policy import PII_CATEGORIES, PiiPolicyError, load_pii_policy

ROOT = Path(__file__).resolve().parents[4]


def test_policy_loads_the_closed_taxonomy_and_retention_paths() -> None:
    policy = load_pii_policy(ROOT / "config" / "pii_policy.yaml")
    assert set(policy.category_defaults) == PII_CATEGORIES
    assert policy.default_for("person_name") == "Remove"
    assert policy.minimum_classification_confidence == Decimal("0.80")
    assert "/resume/experience/*/employer" in policy.retain_field_paths


def test_policy_rejects_a_missing_required_category(tmp_path: Path) -> None:
    path = tmp_path / "policy.yaml"
    path.write_text(
        "version: pii_policy@1\ncategories: {}\nretain_field_paths: []\n",
        encoding="utf-8",
    )
    with pytest.raises(PiiPolicyError, match="categories"):
        load_pii_policy(path)
