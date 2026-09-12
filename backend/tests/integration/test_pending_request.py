from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal

from fastapi.testclient import TestClient

from resumematch.api.app import app
from resumematch.core.canonical_json import canonical_sha256
from resumematch.core.clock import FixedClock
from resumematch.core.schemas.candidate import (
    SeniorityId,
    StructuredResume,
    TargetConstraints,
    UnclassifiedItem,
)
from resumematch.core.schemas.sanitized import SanitizedResume
from resumematch.core.session_write import SanitizationRecord, write_sanitization_record
from resumematch.llm.gateway import PendingCloudLLMRequest, stage_pending_request
from resumematch.llm.projection import FieldPath, ProjectionRequest


class _CountingProvider:
    identity: str = "test-provider"
    locality: Literal["cloud"] = "cloud"

    def __init__(self) -> None:
        self.invocations = 0

    def transmit(self, _: PendingCloudLLMRequest) -> Literal["transmitted"]:
        self.invocations += 1
        return "transmitted"


def _sanitized() -> SanitizedResume:
    return SanitizedResume(
        schema_version="sanitized_resume/1",
        source_profile_revision=3,
        resume=StructuredResume(
            schema_version="structured_resume/1",
            summary="sanitized summary",
            skills=(),
            experience=(),
            education=(),
            projects=(),
            certifications=(),
            achievements=(),
            unclassified=(
                UnclassifiedItem(
                    item_id="unclassified-1",
                    origin="user_provided",
                    extraction_confidence=Decimal("1.00"),
                    confidence_inputs=(),
                    provenance=None,
                    source_text="raw source must not be returned",
                    text="sanitized projection value",
                ),
            ),
        ),
        target=TargetConstraints(
            domain_id="domain", role_id="role", seniority_id=SeniorityId.ENTRY,
            locations=(), work_modes=(),
        ),
        removed_span_counts={},
    )


def _pending_request() -> tuple[TestClient, str, _CountingProvider, object]:
    client = TestClient(app)
    token = client.post("/api/v1/sessions").json()["token"]
    session = app.state.components.session_store.get(token)
    assert session is not None
    sanitized = _sanitized()
    session.profile_revision = sanitized.source_profile_revision
    write_sanitization_record(
        session,
        sanitized,
        SanitizationRecord(
            content_hash=canonical_sha256(sanitized.model_dump(mode="json")),
            profile_revision=3,
            produced_at=datetime(2026, 1, 1, tzinfo=UTC),
            pii_policy_version="pii_policy@1",
            detector_versions=("detector@1",),
            placeholder_set_version="placeholders@1",
            removed_categories=(),
            fail_safe_redaction_count=0,
        ),
    )
    provider = _CountingProvider()
    clock = FixedClock(datetime(2026, 1, 1, tzinfo=UTC))
    pending = stage_pending_request(
        session,
        ProjectionRequest(
            operation="bounded_extract",
            sanitization_content_hash=canonical_sha256(sanitized.model_dump(mode="json")),
            paths=(FieldPath("/summary"),),
            evidence_item_ids=(),
            permitted_skill_ids=(),
            non_candidate_context=None,
        ),
        provider,
        clock=clock,
    )
    assert not isinstance(pending, object) or hasattr(pending, "request_id")
    original_provider = app.state.components.llm_provider
    object.__setattr__(app.state.components, "llm_provider", provider)
    return client, token, provider, original_provider


def test_pending_and_manifest_views_are_separate_and_decline_never_transmits() -> None:
    client, token, provider, original_provider = _pending_request()
    headers = {"X-Session-Token": token}

    try:
        pending = client.get("/api/v1/sessions/llm-requests/pending", headers=headers)
        manifest = client.get("/api/v1/sessions/llm-requests", headers=headers)

        assert pending.status_code == manifest.status_code == 200
        assert pending.json()["fields"] == [
            {"path": "/summary", "value": "sanitized summary"},
            {"path": "/unclassified/0/text", "value": "sanitized projection value"},
        ]
        assert "raw source must not be returned" not in str(pending.json())
        assert "fields" not in str(manifest.json())
        assert "sanitized summary" not in str(manifest.json())
        request_id = pending.json()["request_id"]

        declined = client.post(
            f"/api/v1/sessions/llm-requests/{request_id}/consent",
            headers=headers,
            json={"approved": False},
        )

        assert declined.status_code == 200
        assert declined.json()["decision"] == "declined"
        assert provider.invocations == 0
    finally:
        object.__setattr__(app.state.components, "llm_provider", original_provider)


def test_approval_invokes_the_configured_provider_only_through_the_gateway() -> None:
    client, token, provider, original_provider = _pending_request()
    headers = {"X-Session-Token": token}

    try:
        pending = client.get("/api/v1/sessions/llm-requests/pending", headers=headers)
        request_id = pending.json()["request_id"]
        approved = client.post(
            f"/api/v1/sessions/llm-requests/{request_id}/consent",
            headers=headers,
            json={"approved": True},
        )

        assert approved.status_code == 200
        assert approved.json()["decision"] == "transmitted"
        assert provider.invocations == 1
    finally:
        object.__setattr__(app.state.components, "llm_provider", original_provider)
