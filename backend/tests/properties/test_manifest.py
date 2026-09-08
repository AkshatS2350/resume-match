"""Properties of the bounded, value-free cloud request manifest."""

from __future__ import annotations

from datetime import UTC, datetime

from resumematch.core.clock import FixedClock
from resumematch.core.session import CloudLLMRequestManifestEntry, Session, SessionStore


def _entry(index: int) -> CloudLLMRequestManifestEntry:
    return CloudLLMRequestManifestEntry(
        manifest_version="cloud_llm_request_manifest@1",
        operation="bounded_extract",
        field_paths=(f"/unclassified/{index}/text",),
        omitted_paths=(f"/summary/{index}",),
        payload_hash=f"sha256:{index:064x}",
        transmitted_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def test_manifest_entry_contains_only_value_free_metadata() -> None:
    assert tuple(CloudLLMRequestManifestEntry.__annotations__) == (
        "manifest_version",
        "operation",
        "field_paths",
        "omitted_paths",
        "payload_hash",
        "transmitted_at",
    )


def test_manifest_is_bounded_and_discards_oldest_entries_first() -> None:
    session = Session("token", datetime(2026, 1, 1, tzinfo=UTC))
    for index in range(201):
        session.append_llm_manifest(_entry(index))

    assert len(session.llm_manifest) == 200
    assert session.llm_manifest[0] == _entry(1)
    assert session.llm_manifest[-1] == _entry(200)


def test_session_deletion_clears_the_manifest() -> None:
    clock = FixedClock(datetime(2026, 1, 1, tzinfo=UTC))
    store = SessionStore(clock)
    token = store.create()
    session = store.get(token)
    assert session is not None
    session.append_llm_manifest(_entry(1))

    store.delete(token)

    assert tuple(session.llm_manifest) == ()
