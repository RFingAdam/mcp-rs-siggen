"""Raw SCPI tool handlers (send, query, reset, preset)."""

import logging
from typing import Any

from mcp.types import CallToolResult, Tool
from scpi_core import Idempotency

from . import _common

logger = logging.getLogger("rs_siggen_mcp.tools")


async def handle_scpi_send(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Send raw SCPI command."""
    settings = _common.get_settings()
    if not settings.allow_raw_scpi:
        return _common._format_error(
            ValueError(
                "Raw SCPI access is disabled. Set SIGGEN_ALLOW_RAW_SCPI=true "
                "to enable raw SCPI command execution."
            )
        )
    logger.warning(
        "Raw SCPI send: command=%r (tool=%s)",
        arguments["command"],
        "siggen_scpi_send",
    )
    sg = await _common._get_siggen(host, port)
    # An arbitrary operator-supplied command cannot be classified, so it gets the
    # class that never retries. Anything else would risk duplicating a *RST or an
    # output-on that the caller was told had failed.
    await sg.scpi_send(arguments["command"], idempotency=Idempotency.ACTION)
    return _common._format_result({"status": "sent", "command": arguments["command"]})


async def handle_scpi_query(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Send SCPI query and return response."""
    settings = _common.get_settings()
    if not settings.allow_raw_scpi:
        return _common._format_error(
            ValueError(
                "Raw SCPI access is disabled. Set SIGGEN_ALLOW_RAW_SCPI=true "
                "to enable raw SCPI query execution."
            )
        )
    logger.warning(
        "Raw SCPI query: command=%r (tool=%s)",
        arguments["command"],
        "siggen_scpi_query",
    )
    sg = await _common._get_siggen(host, port)
    # Same reasoning as the raw send: the tool is named "query", but the string is
    # the operator's, and `CALibration:ALL?` is a query that acts. Never retried.
    response = await sg.scpi_query(
        arguments["command"], idempotency=Idempotency.ACTION
    )
    return _common._format_result({"command": arguments["command"], "response": response})


async def handle_reset(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Reset signal generator."""
    sg = await _common._get_siggen(host, port)
    await sg.reset()
    return _common._format_result({"status": "reset"})


async def handle_preset(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Preset signal generator."""
    sg = await _common._get_siggen(host, port)
    await sg.preset()
    return _common._format_result({"status": "preset"})


def get_tools() -> list[Tool]:
    """Get raw SCPI tool definitions."""
    return [
        Tool(
            name="siggen_scpi_send",
            description="Send raw SCPI command (no response expected)",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "SCPI command string",
                    },
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
                "required": ["command"],
            },
        ),
        Tool(
            name="siggen_scpi_query",
            description="Send SCPI query and return response",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "SCPI query (should end with ?)",
                    },
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
                "required": ["command"],
            },
        ),
        Tool(
            name="siggen_reset",
            description="Reset signal generator to default state (*RST)",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
            },
        ),
        Tool(
            name="siggen_preset",
            description="Preset signal generator (SYSTem:PRESet)",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
            },
        ),
    ]


SCPI_HANDLERS = {
    "siggen_scpi_send": handle_scpi_send,
    "siggen_scpi_query": handle_scpi_query,
    "siggen_reset": handle_reset,
    "siggen_preset": handle_preset,
}
