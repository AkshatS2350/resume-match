"""The sole HTTP transport implementation, guarded by an injected host grant."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal, Protocol

import httpx

EgressEnclave = Literal["llm_provider", "job_source"]
_GRANT_ISSUER = object()


class EgressHostNotAllowed(Exception):
    """Raised before transport creation when a host is not in an enclave grant."""


@dataclass(frozen=True, init=False)
class EgressGrant:
    enclave: EgressEnclave
    allowed_hosts: frozenset[str]
    timeout_s: float

    def __init__(
        self,
        enclave: EgressEnclave,
        allowed_hosts: frozenset[str],
        timeout_s: float,
        *,
        _issuer: object | None = None,
    ) -> None:
        if _issuer is not _GRANT_ISSUER:
            raise TypeError("EgressGrant instances must be issued by issue_grant")
        object.__setattr__(self, "enclave", enclave)
        object.__setattr__(self, "allowed_hosts", allowed_hosts)
        object.__setattr__(self, "timeout_s", timeout_s)


@dataclass(frozen=True)
class OutboundRequest:
    method: str
    url: str
    headers: Mapping[str, str]
    content: bytes | None


@dataclass(frozen=True)
class OutboundResponse:
    status_code: int
    headers: Mapping[str, str]
    content: bytes


class HttpEgress(Protocol):
    def send(self, request: OutboundRequest) -> OutboundResponse: ...


class EgressSettings(Protocol):
    @property
    def egress_timeout_s(self) -> float: ...

    def allowed_hosts_for(self, enclave: EgressEnclave) -> frozenset[str]: ...


class HttpxEgress:
    def __init__(self, grant: EgressGrant, transport: httpx.BaseTransport | None = None) -> None:
        self._grant = grant
        self._transport = transport

    def send(self, request: OutboundRequest) -> OutboundResponse:
        host = httpx.URL(request.url).host
        if host is None or host.lower() not in self._grant.allowed_hosts:
            raise EgressHostNotAllowed(f"host is not allowed for {self._grant.enclave}: {host}")
        with httpx.Client(transport=self._transport, timeout=self._grant.timeout_s) as client:
            response = client.request(
                method=request.method,
                url=request.url,
                headers=request.headers,
                content=request.content,
            )
        return OutboundResponse(response.status_code, dict(response.headers), response.content)


def issue_grant(settings: EgressSettings, enclave: EgressEnclave) -> EgressGrant:
    """Issue the enclave-specific capability from composition-owned settings."""

    return EgressGrant(
        enclave,
        settings.allowed_hosts_for(enclave),
        settings.egress_timeout_s,
        _issuer=_GRANT_ISSUER,
    )
