"""Closed registry of deterministic signal resolvers."""

from resumematch.rubric.resolvers.certification import CertificationResolver
from resumematch.rubric.resolvers.contracts import (
    Determinability,
    ResolvedSignal,
    SignalResolver,
    SignalType,
)
from resumematch.rubric.resolvers.education import EducationResolver
from resumematch.rubric.resolvers.experience_band import ExperienceBandResolver
from resumematch.rubric.resolvers.flag import FlagResolver
from resumematch.rubric.resolvers.skill import SkillSignalResolver

RESOLVERS = {
    "skill": SkillSignalResolver(),
    "experience_band": ExperienceBandResolver(),
    "education": EducationResolver(),
    "certification": CertificationResolver(),
    "flag": FlagResolver(),
}

__all__ = ["Determinability", "RESOLVERS", "ResolvedSignal", "SignalResolver", "SignalType"]
