from pathlib import Path

import pytest

from resumematch.privacy.detector import PIIDetector
from resumematch.privacy.detectors.ner import (
    LocalPresidioNerDetector,
    PresidioModelConfig,
    PresidioModelUnavailableError,
    load_local_presidio_analyzer,
    load_presidio_model_config,
)
from resumematch.privacy.detectors.rules import RuleDetector


def test_packaged_approved_model_initializes_with_network_disabled(no_network: None) -> None:
    config = load_presidio_model_config(Path(__file__).parents[4] / "config" / "pii_ner_model.yaml")

    analyzer = load_local_presidio_analyzer(config)

    assert analyzer is not None


def test_missing_or_incompatible_model_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    del monkeypatch
    config = PresidioModelConfig("missing_model", "0")

    with pytest.raises(PresidioModelUnavailableError):
        load_local_presidio_analyzer(config)

    with pytest.raises(PresidioModelUnavailableError):
        load_local_presidio_analyzer(PresidioModelConfig("en_core_web_sm", "0"))


def test_combined_detector_records_rule_and_approved_model_versions() -> None:
    detector = PIIDetector(
        (
            RuleDetector("pii_rules@1", ()),
            LocalPresidioNerDetector(PresidioModelConfig("en_core_web_sm", "3.8.0")),
        )
    )

    assert detector.detector_versions == (
        "pii_rules@1",
        "presidio@2.2.362+en_core_web_sm@3.8.0",
    )
