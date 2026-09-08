"""Immutable, evidence-grounded readiness result contracts."""

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from resumematch.core.schemas.version_stamp import VersionStamp


class MatchedSignal(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    signal_id: str
    evidence_level: int = Field(ge=1, le=3)
    supporting_item_ids: tuple[str, ...] = Field(min_length=1)


class MissingSignal(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    signal_id: str
    kind: Literal["absent", "below_required_level"]


class AppliedPenalty(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    penalty_id: str
    points: Decimal = Field(ge=Decimal("0"))


class MissingRequired(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    signal_id: str
    kind: Literal["absent", "below_required_level"]


class FactorContribution(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    category_id: str
    value: Decimal


class ConfidenceResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    value: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))
    band: Literal["low", "medium", "high"]
    terms: dict[str, Decimal]
    weakest_term: str
    zero_denominator_reasons: tuple[str, ...]
    band_capped: bool


class CategoryResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    category_id: str
    weight: int = Field(ge=0, le=100)
    score: int = Field(ge=0, le=100)
    matched_signals: tuple[MatchedSignal, ...]
    missing_signals: tuple[MissingSignal, ...]
    applied_penalties: tuple[AppliedPenalty, ...]


class ReadinessResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    readiness_score: int = Field(ge=0, le=100)
    reason: Literal["scored", "no_evidence", "below_reportable_or_penalized"]
    matched_signal_count: int = Field(ge=0)
    categories: tuple[CategoryResult, ...]
    missing_required: tuple[MissingRequired, ...]
    factor_decomposition: tuple[FactorContribution, ...]
    confidence: ConfidenceResult | None
    versions: VersionStamp
