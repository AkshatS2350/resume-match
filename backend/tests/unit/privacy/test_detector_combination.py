from dataclasses import dataclass
from decimal import Decimal

from resumematch.privacy.detectors.rules import Detection


@dataclass(frozen=True)
class AnalyzerResult:
    entity_type: str
    start: int
    end: int
    score: float


class Analyzer:
    def analyze(self, *, text: str, language: str) -> list[AnalyzerResult]:
        assert language == "en"
        assert text == "Ada Lovelace"
        return [AnalyzerResult("PERSON", 0, 12, 0.91)]


class InstrumentedMechanism:
    def __init__(self, version: str, findings: tuple[Detection, ...]) -> None:
        self.version = version
        self.findings = findings
        self.calls = 0

    def detect(self, text: str) -> tuple[Detection, ...]:
        self.calls += 1
        return self.findings


def test_combined_detector_retains_the_highest_confidence_for_a_shared_span() -> None:
    from resumematch.privacy.detector import PIIDetector

    rule = InstrumentedMechanism(
        "rules@1",
        (Detection("email", 0, 4, Decimal("0.70")),),
    )
    ner = InstrumentedMechanism(
        "ner@1",
        (Detection("email", 0, 4, Decimal("0.91")),),
    )

    findings = PIIDetector((rule, ner)).detect("test")

    assert findings == (Detection("email", 0, 4, Decimal("0.91")),)


def test_combined_detector_calls_every_mechanism_after_an_initial_match() -> None:
    from resumematch.privacy.detector import PIIDetector

    first = InstrumentedMechanism(
        "rules@1",
        (Detection("email", 0, 4, Decimal("0.70")),),
    )
    second = InstrumentedMechanism("ner@1", ())

    PIIDetector((first, second)).detect("test")

    assert first.calls == 1
    assert second.calls == 1


def test_combined_detector_reports_the_versions_of_its_mechanisms() -> None:
    from resumematch.privacy.detector import PIIDetector

    detector = PIIDetector(
        (InstrumentedMechanism("rules@1", ()), InstrumentedMechanism("ner@1", ()))
    )

    assert detector.detector_versions == ("rules@1", "ner@1")


def test_presidio_adapter_converts_person_results_to_the_closed_taxonomy() -> None:
    from resumematch.privacy.detectors.ner import PresidioNerDetector

    findings = PresidioNerDetector(Analyzer()).detect("Ada Lovelace")

    assert findings == (Detection("person_name", 0, 12, Decimal("0.91")),)
