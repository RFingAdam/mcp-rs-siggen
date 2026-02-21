"""Pytest configuration and fixtures."""

import os
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_scpi_socket():
    """Create mock SCPI socket."""
    socket = AsyncMock()
    socket.is_connected = True
    socket.address = "192.168.1.100:5025"

    # Default responses
    socket.query = AsyncMock(
        return_value="Rohde&Schwarz,SMW200A,1412.0000K02/123456,4.30.047.29"
    )
    socket.send = AsyncMock()
    socket.wait_opc = AsyncMock(return_value=True)
    socket.query_float_list = AsyncMock(return_value=[1e9, 2e9, 3e9])

    return socket


@pytest.fixture
def siggen_test_config():
    """Get signal generator test configuration from environment."""
    return {
        "host": os.environ.get("SIGGEN_TEST_HOST", "192.168.1.100"),
        "port": int(os.environ.get("SIGGEN_TEST_PORT", "5025")),
    }


@pytest.fixture
def skip_without_siggen(siggen_test_config):
    """Skip test if no signal generator available."""
    if not os.environ.get("SIGGEN_TEST_HOST"):
        pytest.skip("SIGGEN_TEST_HOST not set, skipping integration test")


@pytest.fixture
def mock_driver(mock_scpi_socket):
    """Create a mock RSSignalGeneratorDriver."""
    from rs_siggen_mcp.driver.siggen_driver import RSSignalGeneratorDriver
    from rs_siggen_mcp.models.siggen_types import InstrumentInfo, SignalGeneratorFamily

    driver = RSSignalGeneratorDriver.__new__(RSSignalGeneratorDriver)
    driver._scpi = mock_scpi_socket
    driver._safety = MagicMock()
    driver._rf_output_on = False
    driver._frequency_hz = None
    driver._power_dbm = None
    driver._info = InstrumentInfo(
        manufacturer="Rohde&Schwarz",
        model="SMW200A",
        serial="1412.0000K02/123456",
        firmware="4.30.047.29",
        family=SignalGeneratorFamily.SMW200A,
    )

    return driver
