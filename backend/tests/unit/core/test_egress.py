"""Tests for the injected outbound-transport capability."""

from __future__ import annotations

import socket

import httpx
import pytest

from resumematch.core.egress import (
    EgressGrant,
    EgressHostNotAllowed,
    HttpxEgress,
    OutboundRequest,
    issue_grant,
)


class StubEgressSettings:
    egress_timeout_s = 5.0

    def allowed_hosts_for(self, enclave: str) -> frozenset[str]:
        return frozenset({"allowed.example" if enclave == "llm_provider" else "jobs.example"})


def _grant(enclave: str) -> EgressGrant:
    return issue_grant(StubEgressSettings(), enclave)  # type: ignore[arg-type]


def test_allow_listed_request_is_attempted() -> None:
    observed: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        observed.append(request)
        return httpx.Response(204, content=b"", request=request)

    grant = _grant("llm_provider")
    response = HttpxEgress(grant, httpx.MockTransport(handle)).send(
        OutboundRequest("GET", "https://allowed.example/v1", {}, None)
    )

    assert response.status_code == 204
    assert len(observed) == 1


def test_disallowed_host_fails_before_opening_a_socket(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_connect(self: socket.socket, address: object) -> None:
        raise AssertionError(f"socket opened for {address!r}")

    monkeypatch.setattr(socket.socket, "connect", fail_connect)
    grant = _grant("job_source")
    transport = httpx.MockTransport(lambda request: httpx.Response(200, request=request))
    egress = HttpxEgress(grant, transport)

    with pytest.raises(EgressHostNotAllowed, match="blocked.example"):
        egress.send(OutboundRequest("GET", "https://blocked.example/jobs", {}, None))


def test_grants_are_issued_only_by_issue_grant() -> None:
    with pytest.raises(TypeError, match="issue_grant"):
        EgressGrant("llm_provider", frozenset({"allowed.example"}), 5.0)
