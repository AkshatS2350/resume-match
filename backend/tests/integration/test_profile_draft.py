from pathlib import Path

from fastapi.testclient import TestClient

from resumematch.api.app import app
from resumematch.core.schemas.candidate import StructuredResume
from resumematch.core.schemas.extracted_text import ExtractedBlock, ExtractedText


def test_profile_draft_structures_session_extraction() -> None:
    client = TestClient(app)
    token = client.post("/api/v1/sessions").json()["token"]
    session = app.state.components.session_store.get(token)
    assert session is not None
    session.extracted_text = ExtractedText(
        text="Skills\nPython",
        blocks=(
            ExtractedBlock(
                block_id="skills-heading",
                section_id="preamble",
                page=1,
                start_offset=0,
                end_offset=6,
                text="Skills",
                layout_kind="heading",
                column_index=None,
            ),
            ExtractedBlock(
                block_id="python",
                section_id="preamble",
                page=1,
                start_offset=7,
                end_offset=13,
                text="Python",
                layout_kind="list_item",
                column_index=None,
            ),
        ),
        page_count=1,
        pages_with_text_layer=(1,),
        extractor_version="test",
    )  # type: ignore[assignment]

    response = client.post("/api/v1/sessions/profile/draft", headers={"X-Session-Token": token})

    assert response.status_code == 200
    assert response.json()["schema_version"] == "structured_resume/1"
    assert response.json()["skills"][0]["canonical_skill_id"] == "python"
    assert isinstance(session.structured_resume, StructuredResume)


def test_profile_draft_rejects_session_without_an_uploaded_resume() -> None:
    client = TestClient(app)
    token = client.post("/api/v1/sessions").json()["token"]

    response = client.post("/api/v1/sessions/profile/draft", headers={"X-Session-Token": token})

    assert response.status_code == 404
    assert response.json()["code"] == "SESSION_NOT_FOUND"


def test_profile_draft_handles_every_text_bearing_uploaded_fixture() -> None:
    client = TestClient(app)
    root = Path(__file__).resolve().parents[3] / "fixtures" / "resumes"
    for path in sorted(root.glob("*")):
        if path.suffix not in {".pdf", ".docx"} or path.name == "10-image-only.pdf":
            continue
        token = client.post("/api/v1/sessions").json()["token"]
        with path.open("rb") as upload:
            uploaded = client.post(
                "/api/v1/sessions/resume",
                headers={"X-Session-Token": token},
                files={"file": ("fixture", upload, "application/octet-stream")},
            )
        assert uploaded.status_code == 200, path.name

        drafted = client.post("/api/v1/sessions/profile/draft", headers={"X-Session-Token": token})

        assert drafted.status_code == 200, path.name
        assert drafted.json()["schema_version"] == "structured_resume/1"
