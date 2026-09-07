from decimal import Decimal
from pathlib import Path

from resumematch.privacy.detectors.rules import Detection
from resumematch.privacy.placeholders import load_placeholders
from resumematch.privacy.policy import load_pii_policy
from resumematch.privacy.sanitizer import Sanitizer

_ROOT = Path(__file__).parents[4]


def _sanitizer() -> Sanitizer:
    policy = load_pii_policy(_ROOT / "config" / "pii_policy.yaml")
    return Sanitizer(policy, load_placeholders(_ROOT / "config" / "pii_placeholders.yaml", policy))


def test_low_confidence_removal_is_counted_as_fail_safe_redaction() -> None:
    result = _sanitizer().sanitize_value(
        path="/resume/summary",
        value="Ada Lovelace",
        detections=(Detection("person_name", 0, 12, Decimal("0.79")),),
    )

    assert result.value == "[[PERSON_NAME]]"
    assert result.fail_safe_redaction_count == 1


def test_at_or_above_confidence_floor_is_not_a_fail_safe_redaction() -> None:
    result = _sanitizer().sanitize_value(
        path="/resume/summary",
        value="Ada Lovelace",
        detections=(Detection("person_name", 0, 12, Decimal("0.80")),),
    )

    assert result.fail_safe_redaction_count == 0


def test_low_confidence_span_in_a_retained_field_is_not_removed() -> None:
    result = _sanitizer().sanitize_value(
        path="/resume/experience/0/employer",
        value="Ada Lovelace",
        detections=(Detection("person_name", 0, 12, Decimal("0.79")),),
    )

    assert result.value == "Ada Lovelace"
    assert result.fail_safe_redaction_count == 0
