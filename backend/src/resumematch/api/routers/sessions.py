"""Header-scoped in-memory session endpoints."""

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Header

from resumematch.api.composition import session_store_dependency
from resumematch.api.dto.session import SessionCreated, SessionDeleted
from resumematch.core.errors import SessionNotFoundError
from resumematch.core.session import SessionStore

router = APIRouter(prefix="/sessions")


@router.post("", response_model=SessionCreated, status_code=201)
def create_session(
    store: Annotated[SessionStore, Depends(session_store_dependency)],
) -> SessionCreated:
    token = store.create()
    session = store.get(token)
    assert session is not None
    return SessionCreated(
        token=token,
        expires_at=session.last_access_at + timedelta(hours=24),
        session_start_date=session.session_start_date,
    )


@router.delete("", response_model=SessionDeleted)
def delete_session(
    token: Annotated[str | None, Header(alias="X-Session-Token")],
    store: Annotated[SessionStore, Depends(session_store_dependency)],
) -> SessionDeleted:
    if token is None or store.get(token) is None:
        raise SessionNotFoundError("Session not found")
    store.delete(token)
    return SessionDeleted(discarded=True)
