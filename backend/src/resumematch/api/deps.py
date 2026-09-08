"""Reusable API admission dependencies for session-bound pipeline stages."""

from typing import Annotated

from fastapi import Depends, Header

from resumematch.api.composition import ApplicationComponents, components_dependency
from resumematch.core.errors import ProfileNotConfirmedError, SessionNotFoundError
from resumematch.core.schemas.candidate import CandidateProfile


def require_confirmed_profile(
    token: Annotated[str | None, Header(alias="X-Session-Token")],
    components: Annotated[ApplicationComponents, Depends(components_dependency)],
) -> CandidateProfile:
    """Resolve only a current, user-confirmed profile before engine construction."""

    if token is None or (session := components.session_store.get(token)) is None:
        raise SessionNotFoundError("Session not found")
    profile = session.candidate_profile
    if profile is None or not profile.confirmed:
        raise ProfileNotConfirmedError()
    return profile
