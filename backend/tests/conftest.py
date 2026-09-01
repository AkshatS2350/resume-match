import socket

import pytest
from hypothesis import settings

settings.register_profile("ci", derandomize=True, max_examples=100, deadline=None)
settings.load_profile("ci")


@pytest.fixture
def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def blocked(*_: object, **__: object) -> None:
        raise RuntimeError("network access is blocked in this test")

    monkeypatch.setattr(socket.socket, "connect", blocked)


class CountingStubProvider:
    def __init__(self) -> None:
        self.invocations = 0

    def invoke(self) -> None:
        self.invocations += 1


@pytest.fixture
def counting_stub_provider() -> CountingStubProvider:
    return CountingStubProvider()


class CapturingTelemetry:
    def __init__(self) -> None:
        self.records: list[dict[str, object]] = []

    def emit(self, **record: object) -> None:
        self.records.append(record)


@pytest.fixture
def capturing_telemetry() -> CapturingTelemetry:
    return CapturingTelemetry()
