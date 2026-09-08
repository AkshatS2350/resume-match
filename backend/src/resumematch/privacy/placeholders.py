"""Content-independent category placeholders for deterministic redaction."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from resumematch.privacy.policy import PiiPolicy


class PlaceholderConfigError(ValueError):
    """Raised when placeholder configuration does not match the PII policy."""


@dataclass(frozen=True)
class Placeholders:
    version: str
    tokens: dict[str, str]

    def exclude_from_detection(self, text: str) -> tuple[str, ...]:
        """Return no candidate spans when input consists only of known placeholders."""

        remainder = text
        for token in self.tokens.values():
            remainder = remainder.replace(token, "")
        return () if not remainder.strip() else (remainder,)


def load_placeholders(path: Path, policy: PiiPolicy) -> Placeholders:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("version") != "pii_placeholders@1":
        raise PlaceholderConfigError(f"{path}: version")
    tokens = raw.get("tokens")
    if not isinstance(tokens, dict) or set(tokens) != set(policy.category_defaults):
        raise PlaceholderConfigError(f"{path}: tokens must match policy categories")
    if not all(
        isinstance(category, str) and isinstance(token, str) and token == f"[[{category.upper()}]]"
        for category, token in tokens.items()
    ):
        raise PlaceholderConfigError(f"{path}: category-labelled token")
    return Placeholders("pii_placeholders@1", dict(tokens))


def redact(value: str, category: str, placeholders: Placeholders) -> str:
    """Replace a value without retaining its content, length, or position."""

    del value
    try:
        return placeholders.tokens[category]
    except KeyError as error:
        raise PlaceholderConfigError(f"unknown category: {category}") from error
