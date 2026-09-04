"""Manifest-ordered, no-network adapter for checked-in public job fixtures."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import yaml

from resumematch.job.source_api import (
    FetchRequest,
    FetchResult,
    JobPostingDraft,
    RawPosting,
    SourceCapabilities,
)


@dataclass(frozen=True)
class FixtureJobSource:
    fixture_directory: Path

    def capabilities(self) -> SourceCapabilities:
        return SourceCapabilities(
            source_id="fixture",
            universal_search=False,
            requires_registry_entry=False,
            supports_incremental=False,
            is_network_source=False,
            documentation_url="fixture://checked-in",
            rate_limit_note=None,
        )

    def fetch(self, request: FetchRequest) -> FetchResult:
        del request
        manifest_path = self.fixture_directory / "manifest.yaml"
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        entries = manifest["postings"]
        postings = tuple(
            self._raw_posting(self.fixture_directory / "postings" / entry["file"])
            for entry in entries
        )
        return FetchResult(postings=postings, failures=())

    def map(self, raw: RawPosting) -> JobPostingDraft:
        return JobPostingDraft(
            source_id="fixture",
            source_external_id=raw.source_external_id or "",
            values=raw.payload,
        )

    @staticmethod
    def _raw_posting(path: Path) -> RawPosting:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("fixture posting must be an object")
        external_id = payload.get("external_id")
        return RawPosting(
            source_external_id=external_id if isinstance(external_id, str) else None,
            payload=payload,
        )
