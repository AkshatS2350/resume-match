"""Deterministic extraction-confidence calculation."""

from dataclasses import dataclass
from decimal import Decimal

_BASE = Decimal("0.50")
_CONTRIBUTIONS = (
    ("heading_matched", Decimal("0.20")),
    ("layout_clean", Decimal("0.10")),
    ("pattern_complete", Decimal("0.15")),
    ("date_parsed", Decimal("0.05")),
    ("unclassified_section", Decimal("-0.25")),
    ("encoding_anomaly", Decimal("-0.15")),
    ("table_spliced", Decimal("-0.10")),
)


@dataclass(frozen=True)
class ExtractionConfidence:
    value: Decimal
    inputs: tuple[str, ...]


def extraction_confidence(
    *,
    heading_matched: bool,
    layout_clean: bool,
    pattern_complete: bool,
    date_parsed: bool,
    unclassified_section: bool,
    encoding_anomaly: bool,
    table_spliced: bool,
    user_provided: bool = False,
) -> ExtractionConfidence:
    """Calculate the documented confidence components without inference."""
    if user_provided:
        return ExtractionConfidence(Decimal("1.00"), ("user_provided",))
    values = {
        "heading_matched": heading_matched,
        "layout_clean": layout_clean,
        "pattern_complete": pattern_complete,
        "date_parsed": date_parsed,
        "unclassified_section": unclassified_section,
        "encoding_anomaly": encoding_anomaly,
        "table_spliced": table_spliced,
    }
    value = _BASE
    inputs = ["base"]
    for name, contribution in _CONTRIBUTIONS:
        if values[name]:
            value += contribution
            inputs.append(name)
    return ExtractionConfidence(max(Decimal("0.00"), min(Decimal("1.00"), value)), tuple(inputs))
