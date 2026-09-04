from decimal import Decimal
from pathlib import Path

from resumematch.privacy.detectors.rules import Detection
from resumematch.privacy.placeholders import load_placeholders
from resumematch.privacy.policy import load_pii_policy
from resumematch.privacy.sanitizer import Sanitizer

ROOT = Path(__file__).resolve().parents[4]


def _sanitizer() -> Sanitizer:
    policy = load_pii_policy(ROOT / "config" / "pii_policy.yaml")
    placeholders = load_placeholders(ROOT / "config" / "pii_placeholders.yaml", policy)
    return Sanitizer(policy, placeholders)


def test_retain_default_employer_value_wins_over_a_person_name_detection() -> None:
    result = _sanitizer().sanitize_value(
        path="/resume/experience/0/employer",
        value="Morgan Stanley",
        detections=(Detection("person_name", 0, 13, Decimal("0.91")),),
    )

    assert result.value == "Morgan Stanley"


def test_pii_inside_a_retained_project_description_is_replaced_only_at_its_span() -> None:
    value = "Built dashboard with Ada Lovelace for weekly analysis."
    result = _sanitizer().sanitize_value(
        path="/resume/projects/0/description",
        value=value,
        detections=(Detection("person_name", 21, 33, Decimal("0.91")),),
    )

    assert result.value == "Built dashboard with [[PERSON_NAME]] for weekly analysis."
