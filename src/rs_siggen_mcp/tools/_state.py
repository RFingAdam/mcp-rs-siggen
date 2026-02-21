"""State management tool handlers (save, load, get full state)."""

from typing import Any

from mcp.types import CallToolResult, Tool

from . import _common


async def handle_save_state(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Save current signal generator configuration to file."""
    sg = await _common._get_siggen(host, port)
    async with _common._state_lock:
        safe_path = _common.validate_safe_path(
            arguments["filepath"], _common._state_manager.state_directory
        )
        state = await _common._state_manager.capture_state(sg)
        if arguments.get("notes"):
            state.notes = arguments["notes"]
        state.save(safe_path)
    return _common._format_result({
        "status": "state_saved",
        "filepath": str(safe_path),
        "summary": state.get_summary(),
    })


async def handle_load_state(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Load and restore signal generator configuration from file."""
    sg = await _common._get_siggen(host, port)
    async with _common._state_lock:
        safe_path = _common.validate_safe_path(
            arguments["filepath"], _common._state_manager.state_directory
        )
        state = _common.InstrumentState.load(safe_path)
        await _common._state_manager.restore_state(sg, state)
    return _common._format_result({
        "status": "state_restored",
        "filepath": str(safe_path),
        "summary": state.get_summary(),
    })


async def handle_get_full_state(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Get complete signal generator configuration state."""
    sg = await _common._get_siggen(host, port)
    state = await _common._state_manager.capture_state(sg)
    return _common._format_result(state.to_dict())


def get_tools() -> list[Tool]:
    """Get state management tool definitions."""
    return [
        Tool(
            name="siggen_save_state",
            description="Save current signal generator configuration to file",
            inputSchema={
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to save state file",
                    },
                    "notes": {
                        "type": "string",
                        "description": "Optional notes about this state",
                    },
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
                "required": ["filepath"],
            },
        ),
        Tool(
            name="siggen_load_state",
            description="Load and restore signal generator configuration from file",
            inputSchema={
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to state file",
                    },
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
                "required": ["filepath"],
            },
        ),
        Tool(
            name="siggen_get_full_state",
            description="Get complete signal generator configuration state as JSON",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
            },
        ),
    ]


STATE_HANDLERS = {
    "siggen_save_state": handle_save_state,
    "siggen_load_state": handle_load_state,
    "siggen_get_full_state": handle_get_full_state,
}
