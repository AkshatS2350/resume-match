"""Deterministically combine independent PII detector mechanisms."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from resumematch.core.errors import PiiDetectionUnavailableError
from resumematch.privacy.detectors.rules import Detection


class PiiDetectionMechanism(Protocol):
    """An independent, versioned PII detector."""

    @property
    def version(self) -> str: ...

    def detect(self, text: str) -> tuple[Detection, ...]: ...


@dataclass(frozen=True)
class PIIDetector:
    """Run every mechanism and retain the strongest duplicate finding."""

    mechanisms: tuple[PiiDetectionMechanism, ...]

    @property
    def detector_versions(self) -> tuple[str, ...]:
        return tuple(mechanism.version for mechanism in self.mechanisms)

    def detect(self, text: str) -> tuple[Detection, ...]:
        by_span: dict[tuple[str, int, int], Detection] = {}
        for mechanism in self.mechanisms:
            try:
                findings = mechanism.detect(text)
            except Exception as error:
                raise PiiDetectionUnavailableError(
                    "PII detection is temporarily unavailable"
                ) from error
            for finding in findings:
                key = (finding.category, finding.start_offset, finding.end_offset)
                existing = by_span.get(key)
                if existing is None or finding.confidence > existing.confidence:
                    by_span[key] = finding
        return tuple(
            sorted(
                by_span.values(),
                key=lambda finding: (
                    finding.start_offset,
                    finding.end_offset,
                    finding.category,
                ),
            )
        )
