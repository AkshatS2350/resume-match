from __future__ import annotations

from collections import Counter
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
LABELS = REPOSITORY_ROOT / "fixtures" / "pii" / "LABELS.md"
ALL_CATEGORIES = frozenset(
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


def _labels() -> list[tuple[str, str, int, int, str]]:
    rows: list[tuple[str, str, int, int, str]] = []
    for line in LABELS.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| ") or line.startswith("| carrier ") or "---" in line:
            continue
        columns = [part.strip() for part in line.strip("|").split("|")]
        if len(columns) == 5:
            rows.append((columns[0], columns[1], int(columns[2]), int(columns[3]), columns[4]))
    return rows


def _line_labels(category: str) -> list[tuple[str, str, int, int, str]]:
    carrier = f"{category}/carrier.txt"
    text = (LABELS.parent / carrier).read_text(encoding="utf-8")
    labels: list[tuple[str, str, int, int, str]] = []
    offset = 0
    for index, line in enumerate(text.splitlines(keepends=True)):
        value = line.rstrip("\n")
        if 0 < index < 21:
            labels.append((carrier, category, offset, offset + len(value), value))
        offset += len(line)
    return labels


def test_pii_fixture_labels_match_their_zero_based_exclusive_spans() -> None:
    labels = _labels() + [
        label
        for category in sorted(ALL_CATEGORIES - {"person_name", "postal_address"})
        for label in _line_labels(category)
    ]
    assert Counter(category for _, category, *_ in labels) == {
        category: 20 for category in ALL_CATEGORIES
    }
    for carrier, _, start, end, value in labels:
        text = (LABELS.parent / carrier).read_text(encoding="utf-8")
        assert text[start:end] == value


def test_pii_fixture_corpus_contains_required_adversarial_cases() -> None:
    names = (LABELS.parent / "person_name" / "carrier.txt").read_text(encoding="utf-8")
    assert all(value in names for value in ("Morgan Stanley", "Ernst & Young", "Johns Hopkins"))
    assert "Project: Collaborated with Alice Carter" in names
    assert "Alice123" in names
    telephone = (LABELS.parent / "telephone" / "carrier.txt").read_text(encoding="utf-8")
    assert "+44 7700 900001" in telephone
    assert "+44 is an incomplete international number" in telephone


def test_previous_release_has_one_precision_baseline_per_category() -> None:
    import json

    baseline = json.loads(
        (LABELS.parent / "previous_release_figures.json").read_text(encoding="utf-8")
    )
    assert set(baseline) == ALL_CATEGORIES
    assert all(isinstance(value, float) and 0 <= value <= 1 for value in baseline.values())
