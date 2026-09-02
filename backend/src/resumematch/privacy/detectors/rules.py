"""Configuration-driven deterministic PII patterns."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

import yaml

from resumematch.privacy.policy import PII_CATEGORIES


@dataclass(frozen=True)
class Detection:
    category: str
    start_offset: int
    end_offset: int
    confidence: Decimal

    def __post_init__(self) -> None:
        if self.category not in PII_CATEGORIES:
            raise ValueError("category is not in the closed PII taxonomy")
        if self.end_offset <= self.start_offset:
            raise ValueError("offsets must form a nonempty range")
        if not Decimal("0") <= self.confidence <= Decimal("1"):
            raise ValueError("confidence must be in [0, 1]")


@dataclass(frozen=True)
class RuleDetector:
    version: str
    rules: tuple[tuple[str, re.Pattern[str], Decimal], ...]

    def detect(self, text: str) -> tuple[Detection, ...]:
        findings = [
            Detection(category, match.start(), match.end(), confidence)
            for category, pattern, confidence in self.rules
            for match in pattern.finditer(text)
        ]
        return tuple(
            sorted(findings, key=lambda item: (item.start_offset, item.end_offset, item.category))
        )


def load_rule_detector(path: Path) -> RuleDetector:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("version") != "pii_rules@1":
        raise ValueError(f"{path}: version")
    rules = raw.get("rules")
    if not isinstance(rules, dict) or set(rules) != PII_CATEGORIES:
        raise ValueError(f"{path}: rules must equal the closed PII taxonomy")
    loaded: list[tuple[str, re.Pattern[str], Decimal]] = []
    for category, value in sorted(rules.items()):
        if not isinstance(category, str) or not isinstance(value, dict):
            raise ValueError(f"{path}: rule")
        pattern = value.get("pattern")
        try:
            confidence = Decimal(str(value["confidence"]))
        except (InvalidOperation, KeyError) as error:
            raise ValueError(f"{path}: {category}.confidence") from error
        if not isinstance(pattern, str):
            raise ValueError(f"{path}: {category}.pattern")
        loaded.append((category, re.compile(pattern), confidence))
    return RuleDetector("pii_rules@1", tuple(loaded))
