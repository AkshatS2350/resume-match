import json
from datetime import date
from pathlib import Path

from resumematch.core.schemas.candidate import (
    CandidateProfile,
    SeniorityId,
    StructuredResume,
    TargetConstraints,
    WorkMode,
)


def test_profile_and_structured_resume_round_trip() -> None:
    resume = StructuredResume(
        schema_version="structured_resume/1", summary=None, skills=(), experience=(), education=(),
        projects=(), certifications=(), achievements=(), unclassified=(),
    )
    target = TargetConstraints(
        domain_id="finance", role_id="financial_analyst", seniority_id=SeniorityId.ENTRY,
        locations=("London",), work_modes=(WorkMode.HYBRID,),
    )
    profile = CandidateProfile(
        schema_version="candidate_profile/1", profile_revision=1,
        session_start_date=date(2026, 1, 1),
        resume=resume, target=target, confirmed=False,
    )
    assert CandidateProfile.model_validate_json(profile.model_dump_json()) == profile


def test_candidate_schemas_are_published() -> None:
    root = Path(__file__).resolve().parents[3]
    for filename, title in (
        ("candidate_profile.schema.json", "CandidateProfile"),
        ("structured_resume.schema.json", "StructuredResume"),
    ):
        schema = json.loads((root / "docs" / "schemas" / filename).read_text(encoding="utf-8"))
        assert schema["title"] == title
