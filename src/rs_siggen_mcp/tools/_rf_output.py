"""RF output tool handlers (frequency, power, output on/off, phase)."""

from typing import Any

from mcp.types import CallToolResult, Tool

from . import _common


async def handle_set_frequency(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Set CW output frequency."""
    sg = await _common._get_siggen(host, port)
    await sg.set_frequency(arguments["frequency_hz"])
    return _common._format_result({
        "status": "configured",
        "frequency_hz": arguments["frequency_hz"],
    })


async def handle_set_power(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Set RF output power level."""
    sg = await _common._get_siggen(host, port)
    await sg.set_power(arguments["power_dbm"])
    return _common._format_result({
        "status": "configured",
        "power_dbm": arguments["power_dbm"],
    })


async def handle_output_on(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Enable RF output."""
    sg = await _common._get_siggen(host, port)
    await sg.output_on()
    return _common._format_result({"status": "rf_output_enabled"})


async def handle_output_off(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Disable RF output."""
    sg = await _common._get_siggen(host, port)
    await sg.output_off()
    return _common._format_result({"status": "rf_output_disabled"})


async def handle_set_phase(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Set RF phase offset."""
    sg = await _common._get_siggen(host, port)
    await sg.set_phase(arguments["phase_deg"])
    return _common._format_result({
        "status": "configured",
        "phase_deg": arguments["phase_deg"],
    })


def get_tools() -> list[Tool]:
    """Get RF output tool definitions."""
    return [
        Tool(
            name="siggen_set_frequency",
            description="Set CW output frequency in Hz",
            inputSchema={
                "type": "object",
                "properties": {
                    "frequency_hz": {
                        "type": "number",
                        "description": "Frequency in Hz (e.g., 1e9 for 1 GHz)",
                    },
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
                "required": ["frequency_hz"],
            },
        ),
        Tool(
            name="siggen_set_power",
            description="Set RF output power level in dBm",
            inputSchema={
                "type": "object",
                "properties": {
                    "power_dbm": {
                        "type": "number",
                        "description": "Power level in dBm (e.g., -10)",
                    },
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
                "required": ["power_dbm"],
            },
        ),
        Tool(
            name="siggen_output_on",
            description="Enable RF output",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
            },
        ),
        Tool(
            name="siggen_output_off",
            description="Disable RF output (safe state)",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
            },
        ),
        Tool(
            name="siggen_set_phase",
            description="Set RF phase offset in degrees",
            inputSchema={
                "type": "object",
                "properties": {
                    "phase_deg": {
                        "type": "number",
                        "description": "Phase offset in degrees",
                    },
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
                "required": ["phase_deg"],
            },
        ),
    ]


RF_OUTPUT_HANDLERS = {
    "siggen_set_frequency": handle_set_frequency,
    "siggen_set_power": handle_set_power,
    "siggen_output_on": handle_output_on,
    "siggen_output_off": handle_output_off,
    "siggen_set_phase": handle_set_phase,
}
