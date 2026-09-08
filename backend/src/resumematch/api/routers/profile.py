"""Session-scoped deterministic profile drafting."""

from typing import Annotated, cast

from fastapi import APIRouter, Depends, Header

from resumematch.api.composition import ApplicationComponents, components_dependency
from resumematch.core.errors import SessionNotFoundError
from resumematch.core.schemas.candidate import StructuredResume
from resumematch.core.schemas.extracted_text import ExtractedText
from resumematch.resume.structure import structure

router = APIRouter(prefix="/sessions/profile")


@router.post("/draft", response_model=StructuredResume)
def draft_profile(
    token: Annotated[str | None, Header(alias="X-Session-Token")],
    components: Annotated[ApplicationComponents, Depends(components_dependency)],
) -> StructuredResume:
    if token is None or (session := components.session_store.get(token)) is None:
        raise SessionNotFoundError("Session not found")
    if session.extracted_text is None:
        raise SessionNotFoundError("Session has no extracted resume")
    extracted = cast(ExtractedText, session.extracted_text)
    drafted = structure(
        extracted,
        session.session_start_date,
        components.section_headings,
        components.skill_normalizer,
    )
    session.structured_resume = drafted  # type: ignore[assignment]
    return drafted
