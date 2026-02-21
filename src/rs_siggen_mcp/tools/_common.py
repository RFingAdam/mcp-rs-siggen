"""Shared state, locks, and helpers for tool handlers."""

import asyncio
import json
import logging
from typing import Any

from mcp.types import CallToolResult, TextContent

from ..config import get_settings as get_settings
from ..driver import RSSignalGeneratorDriver
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
_connection_lock = asyncio.Lock()
_template_lock = asyncio.Lock()
_state_lock = asyncio.Lock()
_limit_lock = asyncio.Lock()

# Global connection manager
_siggen_connections: dict[str, RSSignalGeneratorDriver] = {}

# Global template storage
_current_template: SignalTemplate | None = None

# Global limit manager
_limit_manager = LimitManager()

# Global state manager
_state_manager = StateManager()


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

    async with _connection_lock:
        if key in _siggen_connections:
            sg = _siggen_connections[key]
            if sg.is_connected:
                return sg

        # Create new connection
        sg = RSSignalGeneratorDriver(
            host=host,
            port=port,
            timeout=settings.connection_timeout,
            command_timeout=settings.command_timeout,
            safety_limits=settings.get_safety_limits(),
        )
        await sg.connect()
        _siggen_connections[key] = sg
        return sg


async def _close_siggen(host: str, port: int) -> bool:
    """Close signal generator connection."""
    key = _get_connection_key(host, port)
    async with _connection_lock:
        if key in _siggen_connections:
            sg = _siggen_connections.pop(key)
            await sg.disconnect()
            return True
        return False


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
