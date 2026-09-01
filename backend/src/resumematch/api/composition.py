"""The sole construction point for application collaborators."""

from dataclasses import dataclass

from fastapi import Request

from resumematch.core.clock import Clock, SystemClock
from resumematch.core.config import Settings
from resumematch.core.session import SessionStore


@dataclass(frozen=True)
class ApplicationComponents:
    """Explicit dependencies supplied to API routers by FastAPI."""

    clock: Clock
    session_store: SessionStore
    settings: Settings


def build_components() -> ApplicationComponents:
    """Construct process-local collaborators without ambient global state."""

    clock = SystemClock()
    return ApplicationComponents(
        clock=clock,
        session_store=SessionStore(clock),
        settings=Settings(()),
    )


def session_store_dependency(request: Request) -> SessionStore:
    """Provide the composition-owned session store to a route handler."""

    components = request.app.state.components
    if not isinstance(components, ApplicationComponents):
        raise RuntimeError("application components are not installed")
    return components.session_store
