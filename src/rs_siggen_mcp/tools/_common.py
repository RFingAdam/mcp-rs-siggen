"""Shared state, locks, and helpers for tool handlers."""

import asyncio
import json
import logging
from typing import Any, cast

from mcp.types import CallToolResult, TextContent
from scpi_core import ConnectionRegistry, SCPITransport

from ..config import get_settings as get_settings
from ..driver import RSSignalGeneratorDriver as RSSignalGeneratorDriver
from ..exceptions import (
    CommunicationError as CommunicationError,
)
from ..exceptions import (
    TimeoutError as TimeoutError,
)
from ..limits import LimitManager
from ..safety.validators import (
    sanitize_scpi_param as sanitize_scpi_param,
)
from ..safety.validators import (
    validate_safe_path as validate_safe_path,
)
from ..state import InstrumentState as InstrumentState
from ..state import StateManager
from ..templates import SignalTemplate

logger = logging.getLogger("rs_siggen_mcp.tools")

# Locks for protecting shared mutable state (Issue #4)
_template_lock = asyncio.Lock()
_state_lock = asyncio.Lock()
_limit_lock = asyncio.Lock()

# Global template storage
_current_template: SignalTemplate | None = None

# Global limit manager
_limit_manager = LimitManager()

# Global state manager
_state_manager = StateManager()


async def _force_output_off(key: str, transport: SCPITransport) -> None:
    """Drive the generator to its safe state before its handle is dropped.

    A signal generator differs from a measuring instrument here: forgetting a
    connection does not stop the carrier. Without this hook an idle eviction
    leaves the output radiating with nothing left holding a handle to switch it
    off, so the safe state has to be forced while the connection is still open.

    Runs for every drop -- idle expiry, explicit disconnect, shutdown -- and its
    failures are logged and swallowed by the registry, which is correct: an
    instrument that has already gone away must not block the eviction.
    """
    driver = cast(RSSignalGeneratorDriver, transport)
    logger.info("Forcing RF output off before releasing %s", key)
    await driver.output_off()


# Live connections, keyed "host:port".
#
# Replaces a module-global dict plus a bare asyncio.Lock. The dict had no expiry,
# so a connection opened by one tool call lived until the process died -- and with
# it whatever RF state the last caller left. `ConnectionRegistry` adds the idle TTL
# and, more importantly, the eviction hook above, so a forgotten generator is
# switched off rather than merely forgotten.
#
# The registry is typed over `SCPITransport`; what it actually holds here is the
# driver. That is deliberate: the registry only ever calls `is_connected`,
# `connect()` and `disconnect()`, all of which the driver provides, and caching the
# driver rather than its socket is what preserves per-connection state (identity,
# last-set frequency and power) across tool calls. The evict hook needs the driver
# anyway, since `output_off()` is a driver-level operation.
_siggen_registry = ConnectionRegistry(on_evict=_force_output_off)


def _get_connection_key(host: str, port: int) -> str:
    """Generate unique key for connection."""
    return f"{host}:{port}"


async def _get_siggen(
    host: str | None = None, port: int | None = None
) -> RSSignalGeneratorDriver:
    """Get or create signal generator connection."""
    settings = get_settings()
    host = host or settings.default_host
    port = port or settings.default_port
    key = _get_connection_key(host, port)

    async def connect() -> SCPITransport:
        sg = RSSignalGeneratorDriver(
            host=host,
            port=port,
            timeout=settings.connection_timeout,
            command_timeout=settings.command_timeout,
            safety_limits=settings.get_safety_limits(),
        )
        await sg.connect()
        return cast(SCPITransport, sg)

    transport = await _siggen_registry.acquire(key, connect)
    return cast(RSSignalGeneratorDriver, transport)


async def _close_siggen(host: str, port: int) -> bool:
    """Close signal generator connection."""
    key = _get_connection_key(host, port)
    if key not in _siggen_registry.keys():
        return False
    # release() runs the evict hook, so the RF output goes off here too rather
    # than relying on the driver's own disconnect path.
    await _siggen_registry.release(key)
    return True


def _format_result(result: Any) -> CallToolResult:
    """Format result as MCP CallToolResult with isError=False."""
    if isinstance(result, dict):
        text = json.dumps(result, indent=2, default=str)
    elif isinstance(result, list):
        text = json.dumps(result, indent=2, default=str)
    else:
        text = str(result)
    return CallToolResult(
        content=[TextContent(type="text", text=text)],
        isError=False,
    )


def _format_error(error: Exception) -> CallToolResult:
    """Format error as MCP CallToolResult with isError=True."""
    return CallToolResult(
        content=[TextContent(type="text", text=f"Error: {error}")],
        isError=True,
    )
