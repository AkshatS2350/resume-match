import socket

import pytest
from conftest import CountingStubProvider


def test_no_network_fixture_blocks_socket_connections(no_network: None) -> None:
    with pytest.raises(RuntimeError, match="network access is blocked"):
        socket.socket().connect(("example.com", 443))


def test_counting_stub_provider_records_invocations() -> None:
    provider = CountingStubProvider()

    assert provider.invocations == 0
    provider.invoke()
    assert provider.invocations == 1
