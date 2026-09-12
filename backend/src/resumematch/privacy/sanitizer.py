"""Policy-driven deterministic sanitization of individual candidate fields."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import cast

from resumematch.core.canonical_json import canonical_sha256
from resumematch.core.clock import Clock
from resumematch.core.schemas.candidate import CandidateProfile, StructuredResume, TargetConstraints
from resumematch.core.schemas.sanitized import SanitizedResume
from resumematch.core.session import Session
from resumematch.core.session_write import SanitizationRecord, write_sanitization_record
from resumematch.privacy.detector import PiiDetectionMechanism, PIIDetector
from resumematch.privacy.detectors.rules import Detection
from resumematch.privacy.placeholders import Placeholders
from resumematch.privacy.policy import PiiPolicy
from resumematch.privacy.spans import resolve_spans

type JsonValue = str | int | bool | None | list[JsonValue] | dict[str, JsonValue]


@dataclass(frozen=True)
class SanitizedValue:
    value: str
    fail_safe_redaction_count: int = 0


@dataclass(frozen=True)
class Sanitizer:
    policy: PiiPolicy
    placeholders: Placeholders

    def sanitize_value(
        self,
        *,
        path: str,
        value: str,
        detections: tuple[Detection, ...],
    ) -> SanitizedValue:
        if self._retains_whole_value(path):
            return SanitizedValue(value)
        removable = tuple(
            detection
            for detection in detections
            if self.policy.default_for(detection.category) == "Remove"
        )
        spans = resolve_spans(removable)
        redacted = value
        for span in reversed(spans):
            token = self.placeholders.tokens[span.category]
            redacted = redacted[: span.start_offset] + token + redacted[span.end_offset :]
        fail_safe_count = sum(
            span.confidence < self.policy.minimum_classification_confidence for span in spans
        )
        return SanitizedValue(redacted, fail_safe_count)

    def sanitize_values(
        self,
        *,
        values: Mapping[str, str],
        detections_by_path: Mapping[str, tuple[Detection, ...]],
    ) -> dict[str, str]:
        """Sanitize every supplied path without removing a field path."""
        return {
            path: self.sanitize_value(
                path=path,
                value=values[path],
                detections=detections_by_path.get(path, ()),
            ).value
            for path in sorted(values)
        }

    def _retains_whole_value(self, path: str) -> bool:
        if path.endswith("/description"):
            return False
        path_parts = path.split("/")
        return any(
            len(path_parts) == len(pattern_parts)
            and all(
                pattern == "*" or pattern == value
                for pattern, value in zip(pattern_parts, path_parts)
            )
            for pattern_parts in (
                configured_path.split("/") for configured_path in self.policy.retain_field_paths
            )
        )


def sanitize_profile(
    profile: CandidateProfile,
    detector: PiiDetectionMechanism,
    session: Session,
    clock: Clock,
    sanitizer: Sanitizer,
) -> tuple[SanitizedResume, SanitizationRecord]:
    """Create and record the session-only sanitized artifact deterministically."""
    counts: dict[str, int] = {}
    fail_safe_count = 0

    def visit(value: JsonValue, path: str) -> JsonValue:
        nonlocal fail_safe_count
        if path.endswith("/schema_version"):
            return value
        if isinstance(value, str):
            detections = detector.detect(value)
            result = sanitizer.sanitize_value(path=path, value=value, detections=detections)
            if result.value != value:
                for detection in detections:
                    counts[detection.category] = counts.get(detection.category, 0) + 1
                fail_safe_count += result.fail_safe_redaction_count
            return result.value
        if isinstance(value, list):
            return [visit(item, f"{path}/{index}") for index, item in enumerate(value)]
        if isinstance(value, dict):
            return {key: visit(item, f"{path}/{key}") for key, item in value.items()}
        return value

    data = cast(dict[str, JsonValue], visit(profile.model_dump(mode="json"), ""))
    sanitized = SanitizedResume(
        schema_version="sanitized_resume/1",
        source_profile_revision=profile.profile_revision,
        resume=StructuredResume.model_validate(data["resume"]),
        target=TargetConstraints.model_validate(data["target"]) if data["target"] else None,
        removed_span_counts=counts,
    )
    record = SanitizationRecord(
        content_hash=canonical_sha256(sanitized.model_dump(mode="json")),
        profile_revision=profile.profile_revision,
        produced_at=clock.now(),
        pii_policy_version=sanitizer.policy.version,
        detector_versions=(
            detector.detector_versions if isinstance(detector, PIIDetector) else (detector.version,)
        ),
        placeholder_set_version=sanitizer.placeholders.version,
        removed_categories=tuple(sorted(counts)),
        fail_safe_redaction_count=fail_safe_count,
    )
    write_sanitization_record(session, sanitized, record)
    return sanitized, record
