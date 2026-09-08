from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

from resumematch.core.canonical_json import canonical_sha256
from resumematch.core.clock import FixedClock
from resumematch.core.schemas.candidate import CandidateProfile, StructuredResume
from resumematch.core.session import SessionStore
from resumematch.privacy.detector import PIIDetector
from resumematch.privacy.detectors.rules import Detection, load_rule_detector
from resumematch.privacy.placeholders import load_placeholders
from resumematch.privacy.policy import load_pii_policy
from resumematch.privacy.sanitizer import Sanitizer, sanitize_profile


class _Detector:
    version = "detector@1"

    def detect(self, text: str) -> tuple[Detection, ...]:
        return (Detection("email", 0, len(text), Decimal("0.91")),) if "@" in text else ()


def test_sanitize_profile_writes_a_revision_bound_canonical_record() -> None:
    profile = CandidateProfile(
        schema_version="candidate_profile/1",
        profile_revision=3,
        session_start_date=date(2026, 9, 7),
        resume=StructuredResume(
            schema_version="structured_resume/1",
            summary="ada@example.test",
            skills=(),
            experience=(),
            education=(),
            projects=(),
            certifications=(),
            achievements=(),
            unclassified=(),
        ),
        target=None,
        confirmed=True,
    )
    clock = FixedClock(datetime(2026, 9, 7, tzinfo=UTC))
    store = SessionStore(clock)
    session = store.get(store.create())
    assert session is not None

    policy = load_pii_policy(Path(__file__).parents[3] / "config" / "pii_policy.yaml")
    sanitizer = Sanitizer(
        policy,
        load_placeholders(Path(__file__).parents[3] / "config" / "pii_placeholders.yaml", policy),
    )
    sanitized, record = sanitize_profile(profile, _Detector(), session, clock, sanitizer)

    assert sanitized.resume.summary == "[[EMAIL]]"
    assert record.content_hash == canonical_sha256(sanitized.model_dump(mode="json"))
    assert record.profile_revision == 3
    assert session.sanitized_resume is sanitized


def test_record_retains_each_combined_detector_version() -> None:
    profile = CandidateProfile(
        schema_version="candidate_profile/1",
        profile_revision=0,
        session_start_date=date(2026, 9, 7),
        resume=StructuredResume(
            schema_version="structured_resume/1",
            summary="ada@example.test",
            skills=(),
            experience=(),
            education=(),
            projects=(),
            certifications=(),
            achievements=(),
            unclassified=(),
        ),
        target=None,
        confirmed=True,
    )
    clock = FixedClock(datetime(2026, 9, 7, tzinfo=UTC))
    store = SessionStore(clock)
    session = store.get(store.create())
    assert session is not None
    root = Path(__file__).parents[3]
    policy = load_pii_policy(root / "config" / "pii_policy.yaml")

    _, record = sanitize_profile(
        profile,
        PIIDetector((_Detector(), _Detector())),
        session,
        clock,
        Sanitizer(policy, load_placeholders(root / "config" / "pii_placeholders.yaml", policy)),
    )

    assert record.detector_versions == ("detector@1", "detector@1")


def test_every_privacy_corpus_carrier_has_no_rule_findings_after_sanitization() -> None:
    root = Path(__file__).parents[3]
    policy = load_pii_policy(root / "config" / "pii_policy.yaml")
    sanitizer = Sanitizer(
        policy, load_placeholders(root / "config" / "pii_placeholders.yaml", policy)
    )
    detector = load_rule_detector(root / "config" / "pii_rules.yaml")

    for carrier in sorted((root / "fixtures" / "pii").glob("*/carrier.txt")):
        source = carrier.read_text(encoding="utf-8")
        sanitized = sanitizer.sanitize_value(
            path="/resume/summary", value=source, detections=detector.detect(source)
        ).value
        assert detector.detect(sanitized) == ()


def test_sanitization_is_idempotent_for_every_privacy_corpus_carrier() -> None:
    root = Path(__file__).parents[3]
    policy = load_pii_policy(root / "config" / "pii_policy.yaml")
    sanitizer = Sanitizer(
        policy, load_placeholders(root / "config" / "pii_placeholders.yaml", policy)
    )
    detector = load_rule_detector(root / "config" / "pii_rules.yaml")

    for carrier in sorted((root / "fixtures" / "pii").glob("*/carrier.txt")):
        source = carrier.read_text(encoding="utf-8")
        first = sanitizer.sanitize_value(
            path="/resume/summary", value=source, detections=detector.detect(source)
        ).value
        second = sanitizer.sanitize_value(
            path="/resume/summary", value=first, detections=detector.detect(first)
        ).value
        assert second == first
