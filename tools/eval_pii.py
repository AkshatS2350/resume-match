"""Evaluate deterministic PII-detection recall and precision on checked-in fixtures."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend" / "src"))

from resumematch.privacy.detectors.rules import Detection, load_rule_detector  # noqa: E402

_CATEGORIES = (
    "person_name", "email", "telephone", "postal_address", "profile_url",
    "personal_website", "social_handle", "government_identifier",
    "student_employee_identifier", "date_of_birth", "named_reference",
)


def _labels() -> list[tuple[str, str, int, int]]:
    root = ROOT / "fixtures" / "pii"
    labels: list[tuple[str, str, int, int]] = []
    for line in (root / "LABELS.md").read_text(encoding="utf-8").splitlines():
        if line.startswith("| ") and not line.startswith("| carrier ") and "---" not in line:
            parts = [part.strip() for part in line.strip("|").split("|")]
            if len(parts) == 5:
                labels.append((parts[0], parts[1], int(parts[2]), int(parts[3])))
    for category in _CATEGORIES:
        if category in {"person_name", "postal_address"}:
            continue
        carrier = f"{category}/carrier.txt"
        offset = 0
        for index, line in enumerate((root / carrier).read_text(encoding="utf-8").splitlines(True)):
            value = line.rstrip("\n")
            if 0 < index < 21:
                labels.append((carrier, category, offset, offset + len(value)))
            offset += len(line)
    return labels


def main() -> int:
    fixture_root = ROOT / "fixtures" / "pii"
    baseline = json.loads((fixture_root / "previous_release_figures.json").read_text(encoding="utf-8"))
    detector = load_rule_detector(ROOT / "config" / "pii_rules.yaml")
    labels = _labels()
    failures: list[str] = []
    for category in _CATEGORIES:
        category_labels = [item for item in labels if item[1] == category]
        if len(category_labels) < 20:
            failures.append(f"{category} labels={len(category_labels)}")
            continue
        carrier = category_labels[0][0]
        text = (fixture_root / carrier).read_text(encoding="utf-8")
        findings = [item for item in detector.detect(text) if item.category == category]
        recalled = sum(
            any(f.start_offset <= start and end <= f.end_offset for f in findings)
            for _, _, start, end in category_labels
        )
        true_positive = sum(
            any(start <= finding.start_offset and finding.end_offset <= end for _, _, start, end in category_labels)
            for finding in findings
        )
        recall = recalled / len(category_labels)
        precision = true_positive / len(findings) if findings else 0.0
        print(f"{category} recall={recall:.2f} precision={precision:.2f}")
        if recall < 0.95 or precision < float(baseline[category]) - 0.05:
            failures.append(f"{category} recall={recall:.2f} precision={precision:.2f}")
    if failures:
        print("PII gate failed: " + "; ".join(failures), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
