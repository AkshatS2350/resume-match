from decimal import Decimal
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

from resumematch.privacy.detectors.rules import Detection
from resumematch.privacy.placeholders import load_placeholders
from resumematch.privacy.policy import load_pii_policy
from resumematch.privacy.sanitizer import Sanitizer

_ROOT = Path(__file__).parents[3]


def _sanitizer() -> Sanitizer:
    policy = load_pii_policy(_ROOT / "config" / "pii_policy.yaml")
    return Sanitizer(policy, load_placeholders(_ROOT / "config" / "pii_placeholders.yaml", policy))


def test_full_value_removal_retains_the_field_as_its_category_placeholder() -> None:
    result = _sanitizer().sanitize_value(
        path="/resume/summary",
        value="ada@example.test",
        detections=(Detection("email", 0, 16, Decimal("0.91")),),
    )

    assert result.value == "[[EMAIL]]"


def test_distinct_values_of_one_category_produce_identical_sanitized_values() -> None:
    sanitizer = _sanitizer()
    first = sanitizer.sanitize_value(
        path="/resume/summary",
        value="ada@example.test",
        detections=(Detection("email", 0, 16, Decimal("0.91")),),
    )
    second = sanitizer.sanitize_value(
        path="/resume/summary",
        value="bea@example.test",
        detections=(Detection("email", 0, 16, Decimal("0.91")),),
    )

    assert first.value == second.value == "[[EMAIL]]"


def test_sanitizing_path_values_preserves_paths_and_removes_source_substrings() -> None:
    values = {
        "/resume/summary": "Contact ada@example.test",
        "/resume/experience/0/employer": "Northwind Testing",
    }
    detections = {
        "/resume/summary": (Detection("email", 8, 24, Decimal("0.91")),),
        "/resume/experience/0/employer": (),
    }

    sanitized = _sanitizer().sanitize_values(values=values, detections_by_path=detections)

    assert set(sanitized) == set(values)
    assert "ada@example.test" not in sanitized["/resume/summary"]
    assert sanitized["/resume/experience/0/employer"] == "Northwind Testing"


@given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=3, max_size=30))
def test_removed_content_has_no_recoverable_three_character_substring(value: str) -> None:
    sanitized = _sanitizer().sanitize_values(
        values={"/resume/summary": value},
        detections_by_path={
            "/resume/summary": (Detection("email", 0, len(value), Decimal("0.91")),)
        },
    )

    result = sanitized["/resume/summary"]
    assert all(value[index : index + 3] not in result for index in range(len(value) - 2))
