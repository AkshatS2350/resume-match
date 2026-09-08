"""Version-controlled PII policy loading with no category defaults in Python."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Final, Literal, cast

import yaml

PII_CATEGORIES: Final = frozenset(
    {
        "person_name",
        "email",
        "telephone",
        "postal_address",
        "profile_url",
        "personal_website",
        "social_handle",
        "government_identifier",
        "student_employee_identifier",
        "date_of_birth",
        "named_reference",
    }
)
PolicyDefault = Literal["Remove", "Retain"]


class PiiPolicyError(ValueError):
    """Raised when the version-controlled privacy policy is invalid."""


@dataclass(frozen=True)
class PiiPolicy:
    version: str
    category_defaults: dict[str, PolicyDefault]
    retain_field_paths: tuple[str, ...]
    minimum_classification_confidence: Decimal

    def default_for(self, category: str) -> PolicyDefault:
        try:
            return self.category_defaults[category]
        except KeyError as error:
            raise PiiPolicyError(f"unknown category: {category}") from error


def load_pii_policy(path: Path) -> PiiPolicy:
    """Load every required category and the measured confidence floor."""

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("version") != "pii_policy@1":
        raise PiiPolicyError(f"{path}: version")
    categories = raw.get("categories")
    if not isinstance(categories, dict) or set(categories) != PII_CATEGORIES:
        raise PiiPolicyError(f"{path}: categories must equal the closed PII taxonomy")
    defaults: dict[str, PolicyDefault] = {}
    for category, entry in sorted(categories.items()):
        if not isinstance(category, str) or not isinstance(entry, dict):
            raise PiiPolicyError(f"{path}: category entry")
        value = entry.get("default")
        if value not in {"Remove", "Retain"}:
            raise PiiPolicyError(f"{path}: {category}.default")
        defaults[category] = cast(PolicyDefault, value)
    fields = raw.get("retain_field_paths")
    if not isinstance(fields, list) or not all(isinstance(field, str) for field in fields):
        raise PiiPolicyError(f"{path}: retain_field_paths")
    try:
        floor = Decimal(str(raw["minimum_classification_confidence"]))
    except (InvalidOperation, KeyError) as error:
        raise PiiPolicyError(f"{path}: minimum_classification_confidence") from error
    if not Decimal("0") <= floor <= Decimal("1"):
        raise PiiPolicyError(f"{path}: minimum_classification_confidence")
    return PiiPolicy("pii_policy@1", defaults, tuple(fields), floor)
