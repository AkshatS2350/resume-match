from pathlib import Path

from resumematch.privacy.placeholders import load_placeholders, redact
from resumematch.privacy.policy import load_pii_policy

ROOT = Path(__file__).resolve().parents[4]


def test_every_policy_category_has_one_content_independent_placeholder() -> None:
    policy = load_pii_policy(ROOT / "config" / "pii_policy.yaml")
    placeholders = load_placeholders(ROOT / "config" / "pii_placeholders.yaml", policy)
    assert set(placeholders.tokens) == set(policy.category_defaults)
    assert redact("A", "email", placeholders) == redact(
        "a much longer address",
        "email",
        placeholders,
    )


def test_placeholders_are_excluded_from_subsequent_detection_input() -> None:
    policy = load_pii_policy(ROOT / "config" / "pii_policy.yaml")
    placeholders = load_placeholders(ROOT / "config" / "pii_placeholders.yaml", policy)
    assert placeholders.exclude_from_detection("[[EMAIL]] [[PERSON_NAME]]") == ()
