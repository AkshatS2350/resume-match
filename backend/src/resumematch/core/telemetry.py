"""Candidate-safe structured telemetry emission."""

import json
from typing import Any

from resumematch.core.errors import PipelineError

METRIC_ALLOWLIST = frozenset(
    {
        "extraction_success_total",
        "extraction_failure_total",
        "extraction_duration_seconds",
        "structuring_duration_seconds",
        "job_source_latency_seconds",
        "job_source_error_total",
        "postings_fetched_total",
        "postings_normalized_total",
        "postings_rejected_total",
        "scoring_duration_seconds",
        "scoring_exception_total",
        "llm_latency_seconds",
        "llm_error_total",
        "ungrounded_statement_total",
        "fabrication_attempt_total",
        "unmapped_skill_total",
    }
)
LOG_FIELD_ALLOWLIST = frozenset(
    {
        "timestamp",
        "level",
        "event",
        "stage",
        "error_code",
        "session_token_hash",
        "duration_ms",
        "rubric_id",
        "rubric_version",
        "engine_version",
        "source_id",
        "source_external_id",
        "job_internal_id",
        "field_paths",
        "content_hash",
        "provider_id",
        "provider_locality",
        "omitted_field_paths",
        "check_name",
        "item_id",
        "requirement_id",
        "page_numbers",
        "count",
        "reason_code",
    }
)


def emit_metric(name: str, value: int | float = 1, **labels: str | int) -> str:
    if name not in METRIC_ALLOWLIST:
        raise ValueError(f"metric not allowed: {name}")
    return json.dumps({"name": name, "value": value, "labels": labels}, sort_keys=True)


def emit_log(**fields: Any) -> str:
    unknown = set(fields).difference(LOG_FIELD_ALLOWLIST)
    if unknown:
        raise ValueError(f"log field not allowed: {sorted(unknown)[0]}")
    return json.dumps(fields, sort_keys=True)


def sanitize_exception(exc: Exception, stage: str) -> str:
    if isinstance(exc, PipelineError):
        return str(exc)
    return f"{type(exc).__name__} at {stage} [redacted]"
