"""Presidio-backed NER adapter for the closed PII taxonomy."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from resumematch.privacy.detectors.rules import Detection


class PresidioResult(Protocol):
    @property
    def entity_type(self) -> str: ...

    @property
    def start(self) -> int: ...

    @property
    def end(self) -> int: ...

    @property
    def score(self) -> float: ...


class PresidioAnalyzer(Protocol):
    def analyze(self, *, text: str, language: str) -> Sequence[PresidioResult]: ...


_PRESIDIO_CATEGORY_MAP = {
    "PERSON": "person_name",
    "EMAIL_ADDRESS": "email",
    "PHONE_NUMBER": "telephone",
    "LOCATION": "postal_address",
}


@dataclass(frozen=True)
class PresidioNerDetector:
    """Adapt Presidio entities without letting its taxonomy escape this boundary."""

    analyzer: PresidioAnalyzer
    version: str = "presidio@2.2.362+en_core_web_sm@3.8.0"

    def detect(self, text: str) -> tuple[Detection, ...]:
        findings = [
            Detection(
                category=category,
                start_offset=result.start,
                end_offset=result.end,
                confidence=Decimal(str(result.score)),
            )
            for result in self.analyzer.analyze(text=text, language="en")
            if (category := _PRESIDIO_CATEGORY_MAP.get(result.entity_type)) is not None
        ]
        return tuple(
            sorted(
                findings,
                key=lambda item: (item.start_offset, item.end_offset, item.category),
            )
        )
