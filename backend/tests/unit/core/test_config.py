from decimal import Decimal
from pathlib import Path

import pytest

from resumematch.core.config import ConfigInvalid, load_config


def test_missing_version_names_file(tmp_path: Path) -> None:
    path = tmp_path / "missing.yaml"
    path.write_text("weight: '0.40'\n")
    with pytest.raises(ConfigInvalid, match="missing.yaml"):
        load_config(path, decimal_keys=frozenset({"weight"}))


def test_declared_decimal_is_not_float(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("version: v1\nweight: '0.40'\n")
    assert load_config(path, decimal_keys=frozenset({"weight"}))["weight"] == Decimal("0.40")
