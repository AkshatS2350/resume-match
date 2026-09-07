"""In-memory session state with temporary nominal references for later schemas."""

from __future__ import annotations

import hashlib
import secrets
from collections import OrderedDict, deque
from datetime import date, datetime, timedelta
from threading import RLock

from .clock import Clock
from .schemas.sanitized import SanitizedResume


class _ExtractedTextRef:
    pass


class _StructuredResumeRef:
    pass


class _CandidateProfileRef:
    pass


class _SanitizedResumeRef:
    pass


class _ManifestEntryRef:
    pass


class _PendingRequestRef:
    pass


class _ReadinessResultRef:
    pass


class _MatchResultSetRef:
    pass


class _ConsentStateRef:
    pass


class Session:
    def __init__(self, token_hash: str, now: datetime) -> None:
        self.token_hash = token_hash
        self.created_at = now
        self.last_access_at = now
        self.session_start_date: date = now.date()
        self.profile_revision = 0
        self.extracted_text: _ExtractedTextRef | None = None
        self.structured_resume: _StructuredResumeRef | None = None
        self.candidate_profile: _CandidateProfileRef | None = None
        self._sanitized_resume: SanitizedResume | None = None
        self._sanitization_record: object | None = None
        self.llm_manifest: deque[_ManifestEntryRef] = deque(maxlen=200)
        self.pending_llm_request: _PendingRequestRef | None = None
        self.readiness_result: _ReadinessResultRef | None = None
        self.match_result_set: _MatchResultSetRef | None = None
        self.consent = _ConsentStateRef()

    @property
    def sanitized_resume(self) -> SanitizedResume | None:
        return self._sanitized_resume

    @property
    def sanitization_record(self) -> object | None:
        return self._sanitization_record


class SessionStore:
    def __init__(
        self, clock: Clock, ttl: timedelta = timedelta(hours=24), capacity: int = 1000
    ) -> None:
        self._clock = clock
        self._ttl = ttl
        self._capacity = capacity
        self._sessions: OrderedDict[str, Session] = OrderedDict()
        self._lock = RLock()

    def create(self) -> str:
        token = secrets.token_urlsafe(32)
        now = self._clock.now()
        with self._lock:
            self._sweep(now)
            self._sessions[token] = Session(hashlib.sha256(token.encode()).hexdigest(), now)
            self._sessions.move_to_end(token)
            while len(self._sessions) > self._capacity:
                self._sessions.popitem(last=False)
        return token

    def get(self, token: str) -> Session | None:
        with self._lock:
            now = self._clock.now()
            self._sweep(now)
            session = self._sessions.get(token)
            if session:
                session.last_access_at = now
                self._sessions.move_to_end(token)
            return session

    def delete(self, token: str) -> None:
        with self._lock:
            self._sessions.pop(token, None)

    def _sweep(self, now: datetime) -> None:
        for token in tuple(self._sessions):
            if now - self._sessions[token].last_access_at > self._ttl:
                self._sessions.pop(token)
