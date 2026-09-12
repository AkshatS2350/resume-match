"""In-memory session state with temporary nominal references for later schemas."""

from __future__ import annotations

import hashlib
import secrets
from collections import OrderedDict, deque
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from threading import RLock
from typing import Literal

from pydantic import BaseModel, ConfigDict, JsonValue

from .clock import Clock
from .schemas.candidate import CandidateProfile
from .schemas.sanitized import SanitizedResume


class _ExtractedTextRef:
    pass


class _StructuredResumeRef:
    pass


class _SanitizedResumeRef:
    pass


ManifestVersion = Literal["cloud_llm_request_manifest@1"]
ProviderLocality = Literal["cloud", "local", "unavailable"]
ConsentDecision = Literal["pending", "granted", "declined", "unavailable", "transmitted"]
ManifestOmissionReason = Literal["omitted_for_budget"]


@dataclass(frozen=True)
class CloudLLMOmissionRecord:
    """A value-free, deterministic admission-time omission record."""

    path: str
    reason: ManifestOmissionReason


@dataclass(frozen=True)
class CloudLLMRequestManifestEntry:
    """Session-only metadata for an admitted cloud request; it contains no values."""

    manifest_version: ManifestVersion
    operation: str
    field_paths: tuple[str, ...]
    omitted_paths: tuple[str, ...]
    payload_hash: str
    transmitted_at: datetime
    omissions: tuple[CloudLLMOmissionRecord, ...] = ()


class ProjectedField(BaseModel):
    """One exact, admitted sanitized value visible only while consent is pending."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str
    value: JsonValue


class PendingCloudLLMRequest(BaseModel):
    """Session-only, already-admitted projection awaiting an explicit decision."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str
    operation: str
    fields: tuple[ProjectedField, ...]
    payload_hash: str
    provider_identity: str
    provider_locality: ProviderLocality
    admitted_at: datetime
    budget_omitted_paths: tuple[str, ...] = ()


class LLMConsentState(BaseModel):
    """The current request's explicit, session-bound transmission decision."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str
    decision: ConsentDecision
    decided_at: datetime | None


class _ReadinessResultRef:
    pass


class _MatchResultSetRef:
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
        self.candidate_profile: CandidateProfile | None = None
        self._sanitized_resume: SanitizedResume | None = None
        self._sanitization_record: object | None = None
        self.llm_manifest: deque[CloudLLMRequestManifestEntry] = deque(maxlen=200)
        self.pending_llm_request: PendingCloudLLMRequest | None = None
        self.readiness_result: _ReadinessResultRef | None = None
        self.match_result_set: _MatchResultSetRef | None = None
        self.consent: LLMConsentState | None = None

    @property
    def sanitized_resume(self) -> SanitizedResume | None:
        return self._sanitized_resume

    @property
    def sanitization_record(self) -> object | None:
        return self._sanitization_record

    def append_llm_manifest(self, entry: CloudLLMRequestManifestEntry) -> None:
        """Append one value-free request record, discarding the oldest after 200."""

        self.llm_manifest.append(entry)

    def set_pending_llm_request(self, request: PendingCloudLLMRequest) -> None:
        """Retain one gateway-admitted projection within this session only."""

        self.pending_llm_request = request
        self.consent = LLMConsentState(
            request_id=request.request_id,
            decision="pending",
            decided_at=None,
        )

    def clear_candidate_data(self) -> None:
        """Discard every session-only candidate artifact and its request metadata."""

        self.extracted_text = None
        self.structured_resume = None
        self.candidate_profile = None
        self._sanitized_resume = None
        self._sanitization_record = None
        self.llm_manifest.clear()
        self.pending_llm_request = None
        self.consent = None
        self.readiness_result = None
        self.match_result_set = None


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
            session = self._sessions.pop(token, None)
            if session is not None:
                session.clear_candidate_data()

    def _sweep(self, now: datetime) -> None:
        for token in tuple(self._sessions):
            if now - self._sessions[token].last_access_at > self._ttl:
                session = self._sessions.pop(token)
                session.clear_candidate_data()
