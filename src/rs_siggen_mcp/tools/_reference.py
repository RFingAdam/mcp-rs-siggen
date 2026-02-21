"""Reference oscillator tool handlers."""

from typing import Any

from mcp.types import CallToolResult, Tool

from . import _common


async def handle_set_reference_source(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Set reference oscillator source."""
    sg = await _common._get_siggen(host, port)
    await sg.set_reference_source(arguments["source"])
    return _common._format_result({
        "status": "configured",
        "reference_source": arguments["source"],
    })


async def handle_get_reference_status(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Get reference oscillator status."""
    sg = await _common._get_siggen(host, port)
    source = await sg.get_reference_source()
    return _common._format_result({
        "reference_source": source.strip(),
    })


def get_tools() -> list[Tool]:
    """Get reference oscillator tool definitions."""
    return [
        Tool(
            name="siggen_set_reference_source",
            description="Set reference oscillator source (INTernal or EXTernal)",
            inputSchema={
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "Reference source",
                        "enum": ["INTernal", "EXTernal"],
                    },
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
                "required": ["source"],
            },
        ),
        Tool(
            name="siggen_get_reference_status",
            description="Get reference oscillator status and lock state",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
            },
        ),
    ]


REFERENCE_HANDLERS = {
    "siggen_set_reference_source": handle_set_reference_source,
    "siggen_get_reference_status": handle_get_reference_status,
}
