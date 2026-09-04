"""Deterministic public-job normalization primitives."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import yaml

from resumematch.core.clock import Clock
from resumematch.core.schemas.candidate import SeniorityId
from resumematch.core.schemas.job import JobPosting
from resumematch.job.source_api import RawPosting

_LEGAL_SUFFIX = re.compile(r"\b(?:inc|llc|ltd|plc|gmbh|corp|co|sa|bv|ag|pty|limited)\b", re.I)
_PUNCTUATION = re.compile(r"[^\w\s]")
_SPACE = re.compile(r"\s+")
_SENIORITY = {
    "senior": SeniorityId.SENIOR,
    "junior": SeniorityId.ENTRY,
    "intern": SeniorityId.INTERN,
    "lead": SeniorityId.LEAD,
    "manager": SeniorityId.MANAGER,
}


def _fold(value: str) -> str:
    return _SPACE.sub(" ", _PUNCTUATION.sub(" ", value.casefold())).strip()


def company_fold(value: str) -> str:
    return _SPACE.sub(" ", _LEGAL_SUFFIX.sub(" ", _fold(value))).strip()


def title_fold(value: str) -> tuple[str, SeniorityId | None]:
    folded = _fold(value)
    tokens = folded.split()
    seniority = next((level for token, level in _SENIORITY.items() if token in tokens), None)
    return " ".join(token for token in tokens if token not in _SENIORITY), seniority


def location_fold(value: str) -> str:
    folded = _fold(value).replace(" texas", " tx").replace(" united states", " us")
    aliases = yaml.safe_load(_location_alias_path().read_text(encoding="utf-8"))["aliases"]
    normalized = aliases.get(folded.replace(" ", ", "), aliases.get(folded))
    if isinstance(normalized, str):
        return normalized
    return "remote" if folded == "remote" else folded


def _location_alias_path() -> Path:
    return Path(__file__).resolve().parents[4] / "config" / "location_aliases.yaml"


@dataclass(frozen=True)
class NormalizationResult:
    postings: tuple[JobPosting, ...]
    validation_failures: tuple[tuple[str, str | None], ...]


@dataclass(frozen=True)
class JobNormalizer:
    clock: Clock

    def normalize(self, raw_postings: tuple[RawPosting, ...]) -> NormalizationResult:
        postings: list[JobPosting] = []
        failures: list[tuple[str, str | None]] = []
        for raw in raw_postings:
            try:
                postings.append(self._normalize_one(raw))
            except (KeyError, TypeError, ValueError):
                source_id = raw.payload.get("source_id")
                failures.append(
                    (source_id if isinstance(source_id, str) else "unknown", raw.source_external_id)
                )
        return NormalizationResult(tuple(postings), tuple(failures))

    def _normalize_one(self, raw: RawPosting) -> JobPosting:
        if raw.source_external_id is None:
            raise ValueError("external id")
        values = raw.payload
        source_id = _required(values, "source_id")
        title = _required(values, "title")
        company = _required(values, "organization")
        description = _required(values, "description")
        apply_url = _required(values, "apply_url")
        posted_at = _parse_datetime(values.get("posted_at"))
        return JobPosting(
            schema_version="job_posting/1",
            internal_id=f"{source_id}:{raw.source_external_id}",
            source_id=source_id,
            source_external_id=raw.source_external_id,
            company=company,
            raw_title=title,
            raw_description=description,
            apply_url=apply_url,
            normalized_title=title_fold(title)[0],
            normalized_location=_optional_string(values.get("location")),
            posted_at=posted_at,
            ingested_at=self.clock.now(),
        )


def _required(values: dict[str, object], key: str) -> str:
    value = values.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(key)
    return value


def _optional_string(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _parse_datetime(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
