"""Gateway-only protocol for configured LLM providers."""

from typing import Literal, Protocol

from resumematch.core.session import PendingCloudLLMRequest, ProviderLocality


class LLMProvider(Protocol):
    """A provider may receive only a gateway-admitted pending projection."""

    identity: str
    locality: ProviderLocality

    def transmit(self, request: PendingCloudLLMRequest) -> Literal["transmitted", "unavailable"]:
        """Transmit the exact admitted projection without returning or retaining a response."""


class UnconfiguredLLMProvider:
    """Safe default: no configured provider means no egress and no transmission."""

    identity = "unconfigured"
    locality: ProviderLocality = "unavailable"

    def transmit(self, request: PendingCloudLLMRequest) -> Literal["unavailable"]:
        del request
        return "unavailable"
