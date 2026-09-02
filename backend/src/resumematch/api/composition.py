"""The sole construction point for application collaborators."""

from dataclasses import dataclass

from fastapi import Request

from resumematch.core.clock import Clock, SystemClock
from resumematch.core.config import Settings
from resumematch.core.egress import EgressEnclave, EgressGrant, issue_grant
from resumematch.core.session import SessionStore


@dataclass(frozen=True)
class _CompositionEgressSettings:
    """Deny-by-default grants until a configured adapter or provider exists."""

    egress_timeout_s: float = 5.0

    def allowed_hosts_for(self, enclave: EgressEnclave) -> frozenset[str]:
        del enclave
        return frozenset()


@dataclass(frozen=True)
class ApplicationComponents:
    """Explicit dependencies supplied to API routers by FastAPI."""

    clock: Clock
    session_store: SessionStore
    settings: Settings
    llm_grant: EgressGrant
    job_source_grant: EgressGrant


def build_components() -> ApplicationComponents:
    """Construct process-local collaborators without ambient global state."""

    clock = SystemClock()
    egress_settings = _CompositionEgressSettings()
    return ApplicationComponents(
        clock=clock,
        session_store=SessionStore(clock),
        settings=Settings(()),
        llm_grant=issue_grant(egress_settings, "llm_provider"),
        job_source_grant=issue_grant(egress_settings, "job_source"),
    )


def session_store_dependency(request: Request) -> SessionStore:
    """Provide the composition-owned session store to a route handler."""

    components = request.app.state.components
    if not isinstance(components, ApplicationComponents):
        raise RuntimeError("application components are not installed")
    return components.session_store
