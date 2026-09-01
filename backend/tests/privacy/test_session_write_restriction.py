from datetime import UTC, datetime

from resumematch.core.clock import FixedClock
from resumematch.core.session import SessionStore, _SanitizedResumeRef
from resumematch.core.session_write import SanitizationRecord, write_sanitization_record


def test_writer_sets_both_sanitization_fields() -> None:
    store = SessionStore(FixedClock(datetime(2026, 9, 1, tzinfo=UTC)))
    session = store.get(store.create())
    assert session is not None
    resume = _SanitizedResumeRef()
    record = SanitizationRecord(
        content_hash="sha256:" + "0" * 64,
        profile_revision=0,
        produced_at=datetime(2026, 9, 1, tzinfo=UTC),
        pii_policy_version="p",
        detector_versions=(),
        placeholder_set_version="v",
        removed_categories=(),
        fail_safe_redaction_count=0,
    )
    write_sanitization_record(session, resume, record)
    assert session.sanitized_resume is resume
    assert session.sanitization_record is record
