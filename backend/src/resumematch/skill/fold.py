"""Deterministic normalization for skill aliases and surfaces."""

from __future__ import annotations

import re
import unicodedata

_NON_SKILL = re.compile(r"[^0-9a-z+#.]+")
_SPACE = re.compile(r" +")
_OPERATOR_SPACE = re.compile(r" *([+#]) *")


def fold(value: str) -> str:
    """Return the design-defined stable representation of a skill surface."""

    normalized = unicodedata.normalize("NFKC", value).casefold()
    normalized = _NON_SKILL.sub(" ", normalized)
    normalized = _SPACE.sub(" ", normalized).strip()
    normalized = _OPERATOR_SPACE.sub(r"\1", normalized)
    return normalized.rstrip(".")
