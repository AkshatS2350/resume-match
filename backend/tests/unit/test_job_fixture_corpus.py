from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3] / "fixtures" / "jobs" / "default"


def test_fixture_job_manifest_has_an_explicit_order_and_literal_timestamps() -> None:
    manifest = yaml.safe_load((ROOT / "manifest.yaml").read_text(encoding="utf-8"))
    assert manifest["set_version"] == "fixture_jobs@1"
    files = [entry["file"] for entry in manifest["postings"]]
    assert files == [
        "complete.json",
        "no-requirements.json",
        "conflicting-experience.json",
        "duplicate-complete.json",
        "missing-fields.json",
        "malformed.json",
    ]
    for filename in files[:-1]:
        posting = json.loads((ROOT / "postings" / filename).read_text(encoding="utf-8"))
        for field in ("retrieved_at", "posted_at"):
            assert isinstance(posting[field], str)
            datetime.fromisoformat(posting[field].replace("Z", "+00:00"))


def test_malformed_fixture_is_not_a_valid_posting_draft() -> None:
    posting = json.loads((ROOT / "postings" / "malformed.json").read_text(encoding="utf-8"))
    assert posting["external_id"] is None
    assert posting["retrieved_at"] == "not-a-timestamp"
