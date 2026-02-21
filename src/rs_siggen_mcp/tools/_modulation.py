"""Analog modulation tool handlers (AM, FM, PM, pulse, all-off)."""

from typing import Any

from mcp.types import CallToolResult, Tool

from . import _common


async def handle_configure_am(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Configure amplitude modulation."""
    sg = await _common._get_siggen(host, port)
    await sg.configure_am(
        arguments["depth_percent"],
        arguments.get("enable", True),
    )
    return _common._format_result({
        "status": "configured",
        "am_depth_percent": arguments["depth_percent"],
        "enabled": arguments.get("enable", True),
    })


async def handle_configure_fm(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Configure frequency modulation."""
    sg = await _common._get_siggen(host, port)
    await sg.configure_fm(
        arguments["deviation_hz"],
        arguments.get("enable", True),
    )
    return _common._format_result({
        "status": "configured",
        "fm_deviation_hz": arguments["deviation_hz"],
        "enabled": arguments.get("enable", True),
    })


async def handle_configure_pm(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Configure phase modulation."""
    sg = await _common._get_siggen(host, port)
    await sg.configure_pm(
        arguments["deviation_rad"],
        arguments.get("enable", True),
    )
    return _common._format_result({
        "status": "configured",
        "pm_deviation_rad": arguments["deviation_rad"],
        "enabled": arguments.get("enable", True),
    })


async def handle_configure_pulse(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Configure pulse modulation."""
    sg = await _common._get_siggen(host, port)
    await sg.configure_pulse(
        arguments["width_s"],
        arguments.get("period_s"),
        arguments.get("enable", True),
    )
    return _common._format_result({
        "status": "configured",
        "pulse_width_s": arguments["width_s"],
        "pulse_period_s": arguments.get("period_s"),
        "enabled": arguments.get("enable", True),
    })


async def handle_modulation_all_off(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Turn off all modulations."""
    sg = await _common._get_siggen(host, port)
    await sg.modulation_all_off()
    return _common._format_result({"status": "all_modulations_off"})


def get_tools() -> list[Tool]:
    """Get analog modulation tool definitions."""
    return [
        Tool(
            name="siggen_configure_am",
            description="Configure amplitude modulation (AM depth, enable/disable)",
            inputSchema={
                "type": "object",
                "properties": {
                    "depth_percent": {
                        "type": "number",
                        "description": "Modulation depth in percent (0-100)",
                    },
                    "enable": {
                        "type": "boolean",
                        "description": "Enable AM (default: true)",
                        "default": True,
                    },
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
                "required": ["depth_percent"],
            },
        ),
        Tool(
            name="siggen_configure_fm",
            description="Configure frequency modulation (FM deviation, enable/disable)",
            inputSchema={
                "type": "object",
                "properties": {
                    "deviation_hz": {
                        "type": "number",
                        "description": "FM deviation in Hz",
                    },
                    "enable": {
                        "type": "boolean",
                        "description": "Enable FM (default: true)",
                        "default": True,
                    },
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
                "required": ["deviation_hz"],
            },
        ),
        Tool(
            name="siggen_configure_pm",
            description="Configure phase modulation (PM deviation, enable/disable)",
            inputSchema={
                "type": "object",
                "properties": {
                    "deviation_rad": {
                        "type": "number",
                        "description": "PM deviation in radians",
                    },
                    "enable": {
                        "type": "boolean",
                        "description": "Enable PM (default: true)",
                        "default": True,
                    },
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
                "required": ["deviation_rad"],
            },
        ),
        Tool(
            name="siggen_configure_pulse",
            description="Configure pulse modulation (width, period, enable/disable)",
            inputSchema={
                "type": "object",
                "properties": {
                    "width_s": {
                        "type": "number",
                        "description": "Pulse width in seconds",
                    },
                    "period_s": {
                        "type": "number",
                        "description": "Pulse period in seconds (optional)",
                    },
                    "enable": {
                        "type": "boolean",
                        "description": "Enable pulse mod (default: true)",
                        "default": True,
                    },
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
                "required": ["width_s"],
            },
        ),
        Tool(
            name="siggen_modulation_all_off",
            description="Turn off all modulations (AM, FM, PM, pulse, IQ)",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
            },
        ),
    ]


MODULATION_HANDLERS = {
    "siggen_configure_am": handle_configure_am,
    "siggen_configure_fm": handle_configure_fm,
    "siggen_configure_pm": handle_configure_pm,
    "siggen_configure_pulse": handle_configure_pulse,
    "siggen_modulation_all_off": handle_modulation_all_off,
}
