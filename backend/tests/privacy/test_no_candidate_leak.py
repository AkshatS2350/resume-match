"""Runtime privacy gate for candidate-derived marker containment."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from fastapi.testclient import TestClient
from hypothesis import given, settings
from sqlalchemy import create_engine

from resumematch.core.clock import FixedClock
from resumematch.core.schemas.candidate import CandidateProfile
from resumematch.core.session import SessionStore
from resumematch.core.telemetry import emit_log, emit_metric, sanitize_exception
from resumematch.job.store.schema import metadata
from resumematch.privacy.detectors.rules import Detection
from resumematch.privacy.sanitizer import Sanitizer, sanitize_profile
from tests.privacy._leak_assertions import assert_markers_absent, marker_profiles


@given(marker_profile=marker_profiles())
@settings(max_examples=100)
def test_candidate_markers_do_not_escape_runtime_boundaries(
    marker_profile: tuple[CandidateProfile, frozenset[str]],
) -> None:
    profile, markers = marker_profile
    assert all(marker in profile.model_dump_json() for marker in markers)
    store = SessionStore(FixedClock(datetime(2026, 9, 10, tzinfo=UTC)))
    token = store.create()
    session = store.get(token)
    assert session is not None

    sanitized, record = sanitize_profile(
        profile,
        _NoPiiDetector(),
        session,
        FixedClock(datetime(2026, 9, 10, tzinfo=UTC)),
        _sanitizer(),
    )
    second_store = SessionStore(FixedClock(datetime(2026, 9, 10, tzinfo=UTC)))
    second_session = second_store.get(second_store.create())
    assert second_session is not None
    repeated_sanitized, repeated_record = sanitize_profile(
        profile,
        _NoPiiDetector(),
        second_session,
        FixedClock(datetime(2026, 9, 10, tzinfo=UTC)),
        _sanitizer(),
    )
    telemetry = (
        emit_log(event="candidate_sanitized", stage="privacy"),
        emit_metric("extraction_success_total", labels="none"),
        sanitize_exception(ValueError(next(iter(markers))), "privacy"),
        token,
        session.token_hash,
        record.content_hash,
    )

    with TemporaryDirectory() as directory:
        database = Path(directory) / "public-jobs.sqlite3"
        metadata.create_all(create_engine(f"sqlite:///{database}"))
        persisted = database.read_text(encoding="latin-1")

    assert_markers_absent(markers, telemetry + (persisted,))
    assert sanitized.source_profile_revision == profile.profile_revision
    assert (sanitized, record) == (repeated_sanitized, repeated_record)

    store.delete(token)
    assert store.get(token) is None


def test_candidate_derived_log_fields_fail_before_marker_assertion() -> None:
    marker = "candidate-marker-81e0bb2bc9214f5aa809df2617b51a44"

    with pytest.raises(ValueError, match="note"):
        emit_log(event="candidate", note=marker)


def test_raw_exception_marker_is_rejected_by_the_privacy_assertion() -> None:
    marker = "candidate-marker-026854b49ea44b0b9502ce01b8ad7bc4"

    with pytest.raises(AssertionError):
        assert_markers_absent(frozenset({marker}), (str(ValueError(marker)),))


def test_upload_exception_removes_raw_marker_bytes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from resumematch.api.app import app
    from resumematch.api.routers import resume

    marker = b"candidate-marker-1b4cd7a887174a4da47e305db6f07f33"
    monkeypatch.setattr(resume.tempfile, "gettempdir", lambda: str(tmp_path))
    client = TestClient(app)
    token = client.post("/api/v1/sessions").json()["token"]

    response = client.post(
        "/api/v1/sessions/resume",
        headers={"X-Session-Token": token},
        files={"file": ("resume.bin", marker, "application/octet-stream")},
    )

    assert response.status_code == 422
    assert marker.decode() not in response.text
    assert tuple(tmp_path.iterdir()) == ()


class _NoPiiDetector:
    @property
    def version(self) -> str:
        return "test-no-pii@1"

    def detect(self, text: str) -> tuple[Detection, ...]:
        del text
        return ()


def _sanitizer() -> Sanitizer:
    from resumematch.privacy.placeholders import load_placeholders
    from resumematch.privacy.policy import load_pii_policy

    root = Path(__file__).resolve().parents[3]
    policy = load_pii_policy(root / "config" / "pii_policy.yaml")
    return Sanitizer(
        policy,
        load_placeholders(root / "config" / "pii_placeholders.yaml", policy),
    )
