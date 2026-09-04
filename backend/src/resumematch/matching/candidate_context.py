"""Deterministic, configuration-backed candidate context resolution."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import yaml

from resumematch.core.schemas.candidate import CandidateProfile
from resumematch.job.normalizer import company_fold
from resumematch.skill.fold import fold

_UNKNOWN = "unknown"


class CandidateContextConfigError(ValueError):
    """Raised when the versioned candidate-context configuration is invalid."""


@dataclass(frozen=True)
class CandidateContextResolver:
    version: str
    target_role_families: Mapping[str, str]
    target_domain_mappings: Mapping[str, str]
    prior_title_families: Mapping[str, str]
    employer_domain_tokens: Mapping[str, tuple[str, ...]]


@dataclass(frozen=True)
class CandidateContext:
    resolver_version: str
    target_role_family: str
    prior_role_families: tuple[str, ...]
    target_domain: str
    employer_domains: tuple[str, ...]


def load_candidate_context_resolver(path: Path) -> CandidateContextResolver:
    """Load the closed, exact-match mapping used by matching dimensions."""

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("resolver_version") != "candidate_context_resolver@1":
        raise CandidateContextConfigError(f"{path}: resolver_version")
    if raw.get("unknown") != _UNKNOWN:
        raise CandidateContextConfigError(f"{path}: unknown")
    role_families = _string_map(raw.get("target_role_families"), path, "target_role_families")
    domain_mappings = _string_map(raw.get("target_domain_mappings"), path, "target_domain_mappings")
    title_families = _phrase_map(raw.get("prior_title_role_families"), path)
    employer_tokens = _phrase_lists(raw.get("employer_domain_mappings"), path)
    return CandidateContextResolver(
        version="candidate_context_resolver@1",
        target_role_families=role_families,
        target_domain_mappings=domain_mappings,
        prior_title_families=title_families,
        employer_domain_tokens=employer_tokens,
    )


def resolve_candidate_context(
    profile: CandidateProfile, resolver: CandidateContextResolver
) -> CandidateContext:
    """Resolve only configured candidate role-family and domain facts."""

    if profile.target is None:
        return CandidateContext(resolver.version, _UNKNOWN, (), _UNKNOWN, ())
    target_role_family = resolver.target_role_families.get(profile.target.role_id, _UNKNOWN)
    target_domain = resolver.target_domain_mappings.get(profile.target.domain_id, _UNKNOWN)
    prior_families = {
        resolve_title_role_family(item.title, resolver)
        for item in sorted(profile.resume.experience, key=lambda value: value.item_id)
        if item.title is not None
        and resolve_title_role_family(item.title, resolver) != _UNKNOWN
    }
    employer_domains = {
        domain
        for item in sorted(profile.resume.experience, key=lambda value: value.item_id)
        if item.employer is not None
        for domain, tokens in sorted(resolver.employer_domain_tokens.items())
        if any(_contains_folded_phrase(company_fold(item.employer), token) for token in tokens)
    }
    return CandidateContext(
        resolver.version,
        target_role_family,
        tuple(sorted(prior_families)),
        target_domain,
        tuple(sorted(employer_domains)),
    )


def resolve_title_role_family(title: str, resolver: CandidateContextResolver) -> str:
    """Resolve a title only when it exactly matches a configured folded phrase."""

    return resolver.prior_title_families.get(fold(title), _UNKNOWN)


def _contains_folded_phrase(value: str, phrase: str) -> bool:
    return f" {phrase} " in f" {value} "


def _string_map(value: object, path: Path, name: str) -> dict[str, str]:
    if not isinstance(value, dict) or not all(
        isinstance(key, str) and isinstance(value[key], str) for key in sorted(value)
    ):
        raise CandidateContextConfigError(f"{path}: {name}")
    return {key: value[key] for key in sorted(value)}


def _phrase_map(value: object, path: Path) -> dict[str, str]:
    lists = _phrase_lists(value, path)
    resolved: dict[str, str] = {}
    for family, phrases in sorted(lists.items()):
        for phrase in phrases:
            existing = resolved.get(phrase)
            if existing is not None and existing != family:
                raise CandidateContextConfigError(f"{path}: duplicate title phrase {phrase}")
            resolved[phrase] = family
    return resolved


def _phrase_lists(value: object, path: Path) -> dict[str, tuple[str, ...]]:
    if not isinstance(value, dict):
        raise CandidateContextConfigError(f"{path}: phrase mappings")
    result: dict[str, tuple[str, ...]] = {}
    for key, raw_phrases in sorted(value.items()):
        if not isinstance(key, str) or not isinstance(raw_phrases, list):
            raise CandidateContextConfigError(f"{path}: phrase mappings")
        if not all(isinstance(phrase, str) and phrase == fold(phrase) for phrase in raw_phrases):
            raise CandidateContextConfigError(f"{path}: phrases must be folded strings")
        result[key] = tuple(sorted(raw_phrases))
    return result
