"""Runtime proofs that rejected LLM admission has no network or provider effect."""

from datetime import UTC, datetime

import httpx
import pytest
from conftest import CountingStubProvider

from resumematch.core.clock import FixedClock
from resumematch.core.egress import (
    EgressEnclave,
    EgressHostNotAllowed,
    HttpxEgress,
    OutboundRequest,
    issue_grant,
)
from resumematch.core.session import Session
from resumematch.llm.gateway import AdmissionDenial, AdmissionDenied, admit
from resumematch.llm.projection import ProjectionRequest


class _EgressSettings:
    egress_timeout_s = 5.0

    def allowed_hosts_for(self, enclave: EgressEnclave) -> frozenset[str]:
        if enclave == "job_source":
            return frozenset({"jobs.example"})
        return frozenset({"llm.example"})


def _request() -> ProjectionRequest:
    return ProjectionRequest(
        operation="bounded_extract",
        sanitization_content_hash="sha256:" + "0" * 64,
        paths=(),
        evidence_item_ids=(),
        permitted_skill_ids=(),
        non_candidate_context=None,
    )


@pytest.mark.boundary
def test_no_socket_during_rejected_deterministic_admission(no_network: None) -> None:
    session = Session("token", datetime(2026, 1, 1, tzinfo=UTC))

    result = admit(session, _request(), clock=FixedClock(datetime(2026, 1, 1, tzinfo=UTC)))

    assert result == AdmissionDenied(AdmissionDenial.SANITIZATION_INCOMPLETE)


@pytest.mark.boundary
def test_stub_provider_has_zero_invocations_for_every_admission_rejection() -> None:
    provider = CountingStubProvider()
    session = Session("token", datetime(2026, 1, 1, tzinfo=UTC))

    result = admit(session, _request(), clock=FixedClock(datetime(2026, 1, 1, tzinfo=UTC)))

    assert isinstance(result, AdmissionDenied)
    assert provider.invocations == 0


@pytest.mark.boundary
def test_job_egress_cannot_target_a_model_host() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(200, request=request))
    egress = HttpxEgress(issue_grant(_EgressSettings(), "job_source"), transport)

    with pytest.raises(EgressHostNotAllowed, match="llm.example"):
        egress.send(OutboundRequest("GET", "https://llm.example/v1", {}, None))
