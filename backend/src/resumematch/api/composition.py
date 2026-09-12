"""The sole construction point for application collaborators."""

from dataclasses import dataclass
from pathlib import Path

from fastapi import Request

from resumematch.core.clock import Clock, SystemClock
from resumematch.core.config import Settings
from resumematch.core.egress import EgressEnclave, EgressGrant, issue_grant
from resumematch.core.session import SessionStore
from resumematch.llm.provider_api import LLMProvider, UnconfiguredLLMProvider
from resumematch.privacy.detector import PIIDetector
from resumematch.privacy.detectors.ner import LocalPresidioNerDetector, load_presidio_model_config
from resumematch.privacy.detectors.rules import load_rule_detector
from resumematch.privacy.placeholders import load_placeholders
from resumematch.privacy.policy import load_pii_policy
from resumematch.privacy.sanitizer import Sanitizer
from resumematch.resume.structure.sections import SectionHeadings, load_section_headings
from resumematch.skill.alias_loader import load_aliases
from resumematch.skill.normalizer import SkillNormalizer

_ROOT = Path(__file__).resolve().parents[4]


@dataclass(frozen=True)
class _CompositionEgressSettings:
    """Deny-by-default grants until a configured adapter or provider exists."""

    egress_timeout_s: float = 5.0

    def allowed_hosts_for(self, enclave: EgressEnclave) -> frozenset[str]:
        del enclave
        return frozenset()


@dataclass(frozen=True)
class ApplicationComponents:
    """Explicit dependencies supplied to API routers by FastAPI."""

    clock: Clock
    session_store: SessionStore
    settings: Settings
    llm_grant: EgressGrant
    llm_provider: LLMProvider
    job_source_grant: EgressGrant
    section_headings: SectionHeadings
    skill_normalizer: SkillNormalizer
    pii_detector: PIIDetector
    sanitizer: Sanitizer


def build_components() -> ApplicationComponents:
    """Construct process-local collaborators without ambient global state."""

    clock = SystemClock()
    egress_settings = _CompositionEgressSettings()
    pii_policy = load_pii_policy(_ROOT / "config" / "pii_policy.yaml")
    return ApplicationComponents(
        clock=clock,
        session_store=SessionStore(clock),
        settings=Settings(()),
        llm_grant=issue_grant(egress_settings, "llm_provider"),
        llm_provider=UnconfiguredLLMProvider(),
        job_source_grant=issue_grant(egress_settings, "job_source"),
        section_headings=load_section_headings(_ROOT / "config" / "section_headings.yaml"),
        skill_normalizer=SkillNormalizer(load_aliases(_ROOT / "ontology" / "skills.yaml")),
        pii_detector=PIIDetector(
            (
                load_rule_detector(_ROOT / "config" / "pii_rules.yaml"),
                LocalPresidioNerDetector(
                    load_presidio_model_config(_ROOT / "config" / "pii_ner_model.yaml")
                ),
            )
        ),
        sanitizer=Sanitizer(
            pii_policy,
            load_placeholders(_ROOT / "config" / "pii_placeholders.yaml", pii_policy),
        ),
    )


def session_store_dependency(request: Request) -> SessionStore:
    """Provide the composition-owned session store to a route handler."""

    components = components_dependency(request)
    return components.session_store


def components_dependency(request: Request) -> ApplicationComponents:
    """Provide the composition-owned collaborators to a route handler."""

    components = request.app.state.components
    if not isinstance(components, ApplicationComponents):
        raise RuntimeError("application components are not installed")
    return components
