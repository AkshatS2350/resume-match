from pathlib import Path

from fastapi.testclient import TestClient

from resumematch.api.app import app


def test_upload_returns_stage_data_without_extracted_text() -> None:
    client = TestClient(app)
    token = client.post("/api/v1/sessions").json()["token"]
    path = Path(__file__).resolve().parents[3] / "fixtures" / "resumes" / "01-single-column.pdf"
    with path.open("rb") as upload:
        response = client.post(
            "/api/v1/sessions/resume",
            headers={"X-Session-Token": token},
            files={"file": ("private-name.pdf", upload, "application/pdf")},
        )
    assert response.status_code == 200
    assert response.json()["page_count"] == 1
    assert "Avery Rowan" not in response.text


def test_all_text_bearing_fixtures_upload_successfully() -> None:
    client = TestClient(app)
    root = Path(__file__).resolve().parents[3] / "fixtures" / "resumes"
    for path in sorted(root.glob("*")):
        if path.suffix not in {".pdf", ".docx"} or path.name == "10-image-only.pdf":
            continue
        token = client.post("/api/v1/sessions").json()["token"]
        with path.open("rb") as upload:
            response = client.post(
                "/api/v1/sessions/resume",
                headers={"X-Session-Token": token},
                files={"file": ("ignored-name", upload, "application/octet-stream")},
            )
        assert response.status_code == 200, path.name
