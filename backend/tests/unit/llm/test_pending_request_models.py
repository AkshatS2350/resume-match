from datetime import UTC, datetime
from typing import Literal

import pytest
from pydantic import ValidationError

from resumematch.core.clock import FixedClock
from resumematch.core.session import LLMConsentState, Session
from resumematch.llm.gateway import PendingCloudLLMRequest, ProjectedField, record_consent


class _NoCallProvider:
    identity: str = "no-call"
    locality: Literal["cloud"] = "cloud"
    invocations = 0

    def transmit(self, _: PendingCloudLLMRequest) -> Literal["transmitted"]:
        self.invocations += 1
        return "transmitted"


def test_pending_request_is_frozen_and_forbids_unknown_fields() -> None:
    pending = PendingCloudLLMRequest(
        request_id="request-1",
        operation="bounded_extract",
        fields=(ProjectedField(path="/unclassified/0/text", value="sanitized value"),),
        payload_hash="sha256:" + "a" * 64,
        provider_identity="unconfigured",
        provider_locality="unavailable",
        admitted_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    with pytest.raises(ValidationError):
        PendingCloudLLMRequest.model_validate(
            {**pending.model_dump(mode="json"), "raw_prompt": "must not be accepted"}
        )
    with pytest.raises(ValidationError):
        pending.request_id = "other"


def test_consent_is_frozen_and_cannot_transmit_without_a_gateway_pending_request() -> None:
    consent = LLMConsentState(request_id="request-1", decision="pending", decided_at=None)
    with pytest.raises(ValidationError):
        LLMConsentState.model_validate({**consent.model_dump(), "value": "not permitted"})

    provider = _NoCallProvider()
    session = Session("token", datetime(2026, 1, 1, tzinfo=UTC))
    assert record_consent(
        session,
        "request-1",
        True,
        provider,
        clock=FixedClock(datetime(2026, 1, 1, tzinfo=UTC)),
    ) is None
    assert provider.invocations == 0


def test_clearing_candidate_data_discards_pending_request_and_consent() -> None:
    pending = PendingCloudLLMRequest(
        request_id="request-1",
        operation="bounded_extract",
        fields=(ProjectedField(path="/unclassified/0/text", value="sanitized value"),),
        payload_hash="sha256:" + "a" * 64,
        provider_identity="unconfigured",
        provider_locality="unavailable",
        admitted_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    session = Session("token", datetime(2026, 1, 1, tzinfo=UTC))
    session.set_pending_llm_request(pending)

    session.clear_candidate_data()

    assert session.pending_llm_request is None
    assert session.consent is None
