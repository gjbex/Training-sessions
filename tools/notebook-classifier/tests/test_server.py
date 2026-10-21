from __future__ import annotations

import socket

import pytest

from notebook_classifier.server import LOOPBACK_HOST, available_port


def test_available_port_is_loopback_bindable() -> None:
    port = available_port(0)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind((LOOPBACK_HOST, port))


@pytest.mark.parametrize("value", [-1, 65_536])
def test_invalid_port_is_rejected(value: int) -> None:
    with pytest.raises(ValueError, match="between 0 and 65535"):
        available_port(value)
