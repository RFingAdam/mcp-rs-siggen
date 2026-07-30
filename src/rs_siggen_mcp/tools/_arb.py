"""ARB waveform tool handlers."""

from typing import Any

from mcp.types import CallToolResult, Tool
from scpi_core import Idempotency

from . import _common


async def handle_load_waveform(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Load ARB waveform file."""
    sg = await _common._get_siggen(host, port)
    await sg.load_waveform(arguments["waveform_path"])
    return _common._format_result({
        "status": "waveform_loaded",
        "path": arguments["waveform_path"],
    })


async def handle_arb_on(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Enable ARB waveform generator."""
    sg = await _common._get_siggen(host, port)
    await sg.arb_on()
    return _common._format_result({"status": "arb_enabled"})


async def handle_arb_off(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Disable ARB waveform generator."""
    sg = await _common._get_siggen(host, port)
    await sg.arb_off()
    return _common._format_result({"status": "arb_disabled"})


async def handle_set_arb_clock(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Set ARB generator clock rate."""
    sg = await _common._get_siggen(host, port)
    await sg.scpi_send(
        f"SOURce1:BB:ARBitrary:CLOCk {arguments['clock_hz']}",
        idempotency=Idempotency.SETTING,
    )
    return _common._format_result({
        "status": "configured",
        "arb_clock_hz": arguments["clock_hz"],
    })


async def handle_list_waveforms(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """List available waveform files."""
    sg = await _common._get_siggen(host, port)
    directory = _common.sanitize_scpi_param(
        arguments.get("directory", "/var/user/waveform")
    )
    response = await sg.scpi_query(
        f"MMEMory:CATalog? '{directory}'", idempotency=Idempotency.QUERY
    )
    return _common._format_result({
        "directory": directory,
        "contents": response,
    })


def get_tools() -> list[Tool]:
    """Get ARB waveform tool definitions."""
    return [
        Tool(
            name="siggen_load_waveform",
            description="Load ARB waveform file from instrument storage",
            inputSchema={
                "type": "object",
                "properties": {
                    "waveform_path": {
                        "type": "string",
                        "description": "Path to waveform file on instrument",
                    },
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
                "required": ["waveform_path"],
            },
        ),
        Tool(
            name="siggen_arb_on",
            description="Enable ARB waveform generator",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
            },
        ),
        Tool(
            name="siggen_arb_off",
            description="Disable ARB waveform generator",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
            },
        ),
        Tool(
            name="siggen_set_arb_clock",
            description="Set ARB generator clock/sample rate",
            inputSchema={
                "type": "object",
                "properties": {
                    "clock_hz": {
                        "type": "number",
                        "description": "ARB clock rate in Hz",
                    },
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
                "required": ["clock_hz"],
            },
        ),
        Tool(
            name="siggen_list_waveforms",
            description="List available waveform files on the instrument",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Directory to list (default: /var/user/waveform)",
                    },
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
            },
        ),
    ]


ARB_HANDLERS = {
    "siggen_load_waveform": handle_load_waveform,
    "siggen_arb_on": handle_arb_on,
    "siggen_arb_off": handle_arb_off,
    "siggen_set_arb_clock": handle_set_arb_clock,
    "siggen_list_waveforms": handle_list_waveforms,
}
