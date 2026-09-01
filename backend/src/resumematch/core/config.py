from __future__ import annotations

import os
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml


class ConfigInvalid(ValueError):
    pass


def load_config(path: Path, *, decimal_keys: frozenset[str] = frozenset()) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ConfigInvalid(f"{path}: root")
    if not isinstance(data.get("version"), str):
        raise ConfigInvalid(f"{path}: version")
    for key in decimal_keys:
        if key in data:
            if not isinstance(data[key], str):
                raise ConfigInvalid(f"{path}: {key}")
            data[key] = Decimal(data[key])
    return data


class Settings:
    def __init__(self, required_keys: tuple[str, ...]) -> None:
        self.values = {key: self._required(key) for key in required_keys}

    @staticmethod
    def _required(key: str) -> str:
        value = os.getenv(key)
        if value is None:
            raise ConfigInvalid(f"missing required environment key: {key}")
        return value
