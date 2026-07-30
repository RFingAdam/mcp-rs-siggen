"""MCP tool definitions and handlers for R&S signal generator operations.

This package splits tool handlers into focused submodules while presenting
a unified interface via get_tools() and handle_tool().
"""

import logging
from typing import Any

from mcp.types import CallToolResult, Tool

from ..exceptions import (
    CommunicationError,
    ConfigurationError,
    ConnectionError,
    SafetyError,
    SignalGeneratorError,
    TimeoutError,
)
from . import _common
from ._arb import ARB_HANDLERS
from ._arb import get_tools as _arb_tools
from ._calibration import CALIBRATION_HANDLERS
from ._calibration import get_tools as _calibration_tools
from ._connection import CONNECTION_HANDLERS
from ._digital_standards import DIGITAL_STANDARDS_HANDLERS
from ._digital_standards import get_tools as _digital_standards_tools
from ._iq import IQ_HANDLERS
from ._iq import get_tools as _iq_tools
from ._limits import LIMIT_HANDLERS
from ._limits import get_tools as _limit_tools
from ._modulation import MODULATION_HANDLERS
from ._modulation import get_tools as _modulation_tools
from ._reference import REFERENCE_HANDLERS
from ._reference import get_tools as _reference_tools
from ._rf_output import RF_OUTPUT_HANDLERS
from ._rf_output import get_tools as _rf_output_tools
from ._scpi import SCPI_HANDLERS
from ._scpi import get_tools as _scpi_tools
from ._state import STATE_HANDLERS
from ._state import get_tools as _state_tools
from ._sweep import SWEEP_HANDLERS
from ._sweep import get_tools as _sweep_tools
from ._templates import TEMPLATE_HANDLERS
from ._templates import get_tools as _template_tools

logger = logging.getLogger("rs_siggen_mcp.tools")

# Re-export shared state for backwards compatibility with tests
_template_lock = _common._template_lock
_state_lock = _common._state_lock
_limit_lock = _common._limit_lock
# The dict-plus-asyncio.Lock pair that used to hold live connections is now a
# scpi_core ConnectionRegistry, which owns its own lock and an idle TTL.
_siggen_registry = _common._siggen_registry
_current_template = _common._current_template
_limit_manager = _common._limit_manager
_state_manager = _common._state_manager
_get_siggen = _common._get_siggen
_close_siggen = _common._close_siggen
_format_result = _common._format_result
_format_error = _common._format_error
get_settings = _common.get_settings
RSSignalGeneratorDriver = _common.RSSignalGeneratorDriver
sanitize_scpi_param = _common.sanitize_scpi_param
validate_safe_path = _common.validate_safe_path

# Unified handler dispatch table
_ALL_HANDLERS: dict[str, Any] = {}
_ALL_HANDLERS.update(CONNECTION_HANDLERS)
_ALL_HANDLERS.update(RF_OUTPUT_HANDLERS)
_ALL_HANDLERS.update(MODULATION_HANDLERS)
_ALL_HANDLERS.update(IQ_HANDLERS)
_ALL_HANDLERS.update(ARB_HANDLERS)
_ALL_HANDLERS.update(DIGITAL_STANDARDS_HANDLERS)
_ALL_HANDLERS.update(SWEEP_HANDLERS)
_ALL_HANDLERS.update(REFERENCE_HANDLERS)
_ALL_HANDLERS.update(CALIBRATION_HANDLERS)
_ALL_HANDLERS.update(SCPI_HANDLERS)
_ALL_HANDLERS.update(TEMPLATE_HANDLERS)
_ALL_HANDLERS.update(STATE_HANDLERS)
_ALL_HANDLERS.update(LIMIT_HANDLERS)



def _get_connection_tools() -> list[Tool]:
    """Get connection tool definitions."""
    return [
        Tool(
            name="siggen_discover",
            description="Scan for R&S signal generators on the network (port 5025)",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {
                        "type": "string",
                        "description": "Host to scan (default: from settings)",
                    },
                    "start_port": {
                        "type": "integer",
                        "description": "Start port (default: 5025)",
                        "default": 5025,
                    },
                    "end_port": {
                        "type": "integer",
                        "description": "End port (default: 5035)",
                        "default": 5035,
                    },
                },
            },
        ),
        Tool(
            name="siggen_connect",
            description="Connect to R&S signal generator at specified host:port",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {
                        "type": "string",
                        "description": "Signal generator hostname or IP",
                    },
                    "port": {
                        "type": "integer",
                        "description": "TCP port (default: 5025)",
                    },
                },
            },
        ),
        Tool(
            name="siggen_disconnect",
            description="Disconnect from signal generator (turns off RF output first)",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
            },
        ),
        Tool(
            name="siggen_identify",
            description=(
                "Get signal generator identification (*IDN?): "
                "manufacturer, model, serial, firmware, capabilities"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
            },
        ),
        Tool(
            name="siggen_get_status",
            description="Get signal generator connection and configuration status",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
            },
        ),
        Tool(
            name="siggen_get_model_info",
            description=(
                "Get detailed model capabilities "
                "(max freq, IQ BW, ARB support, digital standards)"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
            },
        ),
    ]


def get_tools() -> list[Tool]:
    """Get all MCP tool definitions."""
    tools: list[Tool] = []
    tools.extend(_get_connection_tools())
    tools.extend(_rf_output_tools())
    tools.extend(_modulation_tools())
    tools.extend(_iq_tools())
    tools.extend(_arb_tools())
    tools.extend(_digital_standards_tools())
    tools.extend(_sweep_tools())
    tools.extend(_reference_tools())
    tools.extend(_calibration_tools())
    tools.extend(_scpi_tools())
    tools.extend(_template_tools())
    tools.extend(_state_tools())
    tools.extend(_limit_tools())
    return tools


async def handle_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
    """Handle tool invocation with centralized error handling.

    Args:
        name: Tool name
        arguments: Tool arguments

    Returns:
        CallToolResult with content and isError flag
    """
    try:
        host = arguments.get("host")
        port = arguments.get("port")

        handler = _ALL_HANDLERS.get(name)
        if handler is None:
            return _common._format_error(ValueError(f"Unknown tool: {name}"))

        # discover handler has a different signature (no host/port params)
        if name == "siggen_discover":
            return await handler(arguments)

        return await handler(arguments, host, port)

    except ConnectionError as e:
        logger.error("Connection error in %s: %s", name, e)
        return _common._format_error(e)
    except TimeoutError as e:
        logger.error("Timeout error in %s: %s", name, e)
        return _common._format_error(e)
    except CommunicationError as e:
        logger.error("Communication error in %s: %s", name, e)
        return _common._format_error(e)
    except ConfigurationError as e:
        logger.error("Configuration error in %s: %s", name, e)
        return _common._format_error(e)
    except SafetyError as e:
        logger.error("Safety error in %s: %s", name, e)
        return _common._format_error(e)
    except SignalGeneratorError as e:
        logger.error("Signal generator error in %s: %s", name, e)
        return _common._format_error(e)
    except ValueError as e:
        logger.warning("Validation error in %s: %s", name, e)
        return _common._format_error(e)
    except (KeyError, TypeError) as e:
        logger.error("Invalid arguments for %s: %s", name, e)
        return _common._format_error(e)
    except OSError as e:
        logger.error("I/O error in %s: %s", name, e)
        return _common._format_error(e)
