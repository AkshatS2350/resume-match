"""Configuration-only PII retention-policy flip properties."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
import yaml

from resumematch.privacy.detectors.rules import Detection, RuleDetector, load_rule_detector
from resumematch.privacy.placeholders import load_placeholders
from resumematch.privacy.policy import PII_CATEGORIES, PiiPolicy, load_pii_policy
from resumematch.privacy.sanitizer import Sanitizer

_ROOT = Path(__file__).parents[3]


@pytest.mark.parametrize("category", sorted(PII_CATEGORIES))
def test_policy_default_flip_changes_only_configuration_driven_sanitization(
    category: str, tmp_path: Path
) -> None:
    source_tree_before = _source_tree_hash(_ROOT / "backend" / "src")
    carrier = (_ROOT / "fixtures" / "pii" / category / "carrier.txt").read_text(encoding="utf-8")
    detector = load_rule_detector(_ROOT / "config" / "pii_rules.yaml")
    detections = detector.detect(carrier)
    category_detection = next(
        detection for detection in detections if detection.category == category
    )
    original_policy = load_pii_policy(_ROOT / "config" / "pii_policy.yaml")
    flipped_policy_path = _flipped_policy(category, tmp_path)
    flipped_policy = load_pii_policy(flipped_policy_path)

    original = _sanitize(carrier, detector, original_policy)
    flipped = _sanitize(carrier, detector, flipped_policy)

    category_text = _category_only_text(carrier, category_detection, detections)
    assert original != flipped
    assert all(value not in original for value in category_text)
    assert any(value in flipped for value in category_text)
    assert original == _sanitize(carrier, detector, original_policy)
    assert flipped == _sanitize(carrier, detector, flipped_policy)
    assert _source_tree_hash(_ROOT / "backend" / "src") == source_tree_before


def _flipped_policy(category: str, tmp_path: Path) -> Path:
    raw = yaml.safe_load((_ROOT / "config" / "pii_policy.yaml").read_text(encoding="utf-8"))
    assert isinstance(raw, dict)
    categories = raw["categories"]
    assert isinstance(categories, dict)
    entry = categories[category]
    assert isinstance(entry, dict)
    entry["default"] = "Retain"
    path = tmp_path / "pii_policy_flipped.yaml"
    path.write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")
    return path


def _sanitize(carrier: str, detector: RuleDetector, policy: PiiPolicy) -> str:
    sanitizer = Sanitizer(
        policy,
        load_placeholders(_ROOT / "config" / "pii_placeholders.yaml", policy),
    )
    return sanitizer.sanitize_value(
        path="/resume/summary",
        value=carrier,
        detections=detector.detect(carrier),
    ).value


def _category_only_text(
    carrier: str, target: Detection, detections: tuple[Detection, ...]
) -> tuple[str, ...]:
    ranges = [(target.start_offset, target.end_offset)]
    for detection in detections:
        if detection.category == target.category:
            continue
        ranges = _subtract(ranges, detection.start_offset, detection.end_offset)
    return tuple(carrier[start:end] for start, end in ranges if end > start)


def _subtract(
    ranges: list[tuple[int, int]], start: int, end: int
) -> list[tuple[int, int]]:
    result: list[tuple[int, int]] = []
    for left, right in ranges:
        if end <= left or start >= right:
            result.append((left, right))
            continue
        if left < start:
            result.append((left, start))
        if end < right:
            result.append((end, right))
    return result


def _source_tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*.py")):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()
