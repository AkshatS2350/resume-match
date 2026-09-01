from datetime import UTC, datetime, timedelta

import pytest

from resumematch.core import session as session_module
from resumematch.core.clock import FixedClock
from resumematch.core.session import SessionStore


def test_expired_session_is_absent_on_access() -> None:
    clock = FixedClock(datetime(2026, 9, 1, tzinfo=UTC))
    store = SessionStore(clock, ttl=timedelta(seconds=1), capacity=2)
    token = store.create()
    clock._instant += timedelta(seconds=2)
    assert store.get(token) is None


def test_sanitized_resume_has_no_public_setter() -> None:
    store = SessionStore(FixedClock(datetime(2026, 9, 1, tzinfo=UTC)), timedelta(hours=1), 2)
    session = store.get(store.create())
    assert session is not None
    with pytest.raises(AttributeError):
        session.sanitized_resume = object()


def test_delete_removes_session() -> None:
    store = SessionStore(FixedClock(datetime(2026, 9, 1, tzinfo=UTC)), timedelta(hours=1), 2)
    token = store.create()
    store.delete(token)
    assert store.get(token) is None


def test_session_retains_only_a_hash_of_its_opaque_token() -> None:
    store = SessionStore(FixedClock(datetime(2026, 9, 1, tzinfo=UTC)), timedelta(hours=1), 2)
    token = store.create()
    session = store.get(token)

    assert session is not None
    assert token not in vars(session).values()
    assert len(session.token_hash) == 64


def test_future_session_references_are_private_implementation_markers() -> None:
    assert not hasattr(session_module, "ExtractedTextRef")
    assert not hasattr(session_module, "SanitizedResumeRef")
