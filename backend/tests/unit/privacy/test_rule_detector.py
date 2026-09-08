from decimal import Decimal
from pathlib import Path

import pytest

from resumematch.privacy.detectors.rules import Detection, load_rule_detector

ROOT = Path(__file__).resolve().parents[4]


def test_rule_detector_reports_configured_spans_with_exact_slices() -> None:
    detector = load_rule_detector(ROOT / "config" / "pii_rules.yaml")
    text = "Contact alice@example.test, +44 7700 900001, and @candidate_01."
    findings = detector.detect(text)
    actual = [
        (finding.category, text[finding.start_offset : finding.end_offset]) for finding in findings
    ]
    assert actual == [
        ("email", "alice@example.test"),
        ("telephone", "+44 7700 900001"),
        ("social_handle", "@candidate_01"),
    ]


def test_rule_detector_rejects_confidence_outside_the_closed_interval() -> None:
    with pytest.raises(ValueError, match="confidence"):
        Detection(category="email", start_offset=0, end_offset=1, confidence=Decimal("1.01"))


def test_rule_detector_records_fixture_category_recall() -> None:
    detector = load_rule_detector(ROOT / "config" / "pii_rules.yaml")
    categories = (
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
    )
    for category in categories:
        text = (ROOT / "fixtures" / "pii" / category / "carrier.txt").read_text(encoding="utf-8")
        assert len([item for item in detector.detect(text) if item.category == category]) >= 20
