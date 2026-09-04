"""Policy-driven deterministic sanitization of individual candidate fields."""

from __future__ import annotations

from dataclasses import dataclass

from resumematch.privacy.detectors.rules import Detection
from resumematch.privacy.placeholders import Placeholders
from resumematch.privacy.policy import PiiPolicy
from resumematch.privacy.spans import resolve_spans


@dataclass(frozen=True)
class SanitizedValue:
    value: str


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
        spans = resolve_spans(detections)
        redacted = value
        for span in reversed(spans):
            token = self.placeholders.tokens[span.category]
            redacted = redacted[:span.start_offset] + token + redacted[span.end_offset:]
        return SanitizedValue(redacted)

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
