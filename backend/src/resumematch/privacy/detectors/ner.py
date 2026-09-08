"""Presidio-backed NER adapter for the closed PII taxonomy."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Protocol

import spacy
import yaml
from presidio_analyzer import AnalyzerEngine

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
class PresidioModelConfig:
    model_name: str
    model_version: str


class PresidioModelUnavailableError(RuntimeError):
    """The approved local model is missing or does not match configuration."""


def load_presidio_model_config(path: Path) -> PresidioModelConfig:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if (
        not isinstance(raw, dict)
        or raw.get("version") != "pii_ner_model@1"
        or not isinstance(raw.get("model_name"), str)
        or not isinstance(raw.get("model_version"), str)
    ):
        raise PresidioModelUnavailableError("invalid approved Presidio model configuration")
    return PresidioModelConfig(raw["model_name"], raw["model_version"])


def load_local_presidio_analyzer(config: PresidioModelConfig) -> AnalyzerEngine:
    """Load the approved installed model only; this path never downloads artifacts."""

    try:
        model = spacy.load(config.model_name)
    except Exception as error:
        raise PresidioModelUnavailableError("approved Presidio model is unavailable") from error
    if model.meta.get("version") != config.model_version:
        raise PresidioModelUnavailableError("approved Presidio model version is incompatible")
    try:
        return AnalyzerEngine()
    except Exception as error:
        raise PresidioModelUnavailableError("approved Presidio analyzer is unavailable") from error


@dataclass
class LocalPresidioNerDetector:
    """Lazily initialize the approved packaged model without a download fallback."""

    config: PresidioModelConfig
    _detector: PresidioNerDetector | None = field(default=None, init=False, repr=False)

    @property
    def version(self) -> str:
        return f"presidio@2.2.362+{self.config.model_name}@{self.config.model_version}"

    def detect(self, text: str) -> tuple[Detection, ...]:
        detector = self._detector
        if detector is None:
            detector = PresidioNerDetector(load_local_presidio_analyzer(self.config), self.version)
            self._detector = detector
        return detector.detect(text)


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
