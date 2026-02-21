"""Limit line tool handlers for pass/fail testing."""

from typing import Any

from mcp.types import CallToolResult, Tool

from ..limits import LimitLine, LimitSegment
from . import _common


async def handle_limit_create(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Create a limit line (flat or segmented)."""
    name = arguments["name"]
    segments_data = arguments.get("segments")

    if segments_data:
        segments = [
            LimitSegment(
                start_freq_hz=s["start_freq_hz"],
                stop_freq_hz=s["stop_freq_hz"],
                max_db=s.get("max_db"),
                min_db=s.get("min_db"),
                name=s.get("name"),
            )
            for s in segments_data
        ]
        limit = LimitLine(
            name=name,
            segments=segments,
            description=arguments.get("description", ""),
        )
    else:
        limit = LimitLine.create_flat_limit(
            name=name,
            start_freq_hz=arguments["start_freq_hz"],
            stop_freq_hz=arguments["stop_freq_hz"],
            max_db=arguments.get("max_db"),
            min_db=arguments.get("min_db"),
        )
        if arguments.get("description"):
            limit.description = arguments["description"]

    async with _common._limit_lock:
        _common._limit_manager.add_limit(limit)

    return _common._format_result({
        "status": "limit_created",
        "name": name,
        "segments": len(limit.segments),
    })


async def handle_limit_list(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """List all active limit lines."""
    async with _common._limit_lock:
        names = _common._limit_manager.list_limits()
        limits = []
        for name in names:
            limit = _common._limit_manager.get_limit(name)
            if limit:
                limits.append(limit.to_dict())

    return _common._format_result({
        "count": len(limits),
        "limits": limits,
    })


async def handle_limit_remove(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Remove a limit line by name."""
    name = arguments["name"]
    async with _common._limit_lock:
        removed = _common._limit_manager.remove_limit(name)

    return _common._format_result({
        "status": "removed" if removed else "not_found",
        "name": name,
    })


async def handle_limit_check(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Check measurements against a named limit."""
    name = arguments["name"]
    frequencies = arguments["frequencies"]
    values_db = arguments["values_db"]

    async with _common._limit_lock:
        limit = _common._limit_manager.get_limit(name)

    if limit is None:
        return _common._format_error(ValueError(f"Limit not found: {name}"))

    result = limit.check_points(frequencies, values_db)
    return _common._format_result({
        "limit_name": name,
        **result.to_dict(),
    })


async def handle_limit_get_status(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Get overall pass/fail across all limits."""
    frequencies = arguments["frequencies"]
    values_db = arguments["values_db"]

    async with _common._limit_lock:
        status = _common._limit_manager.get_overall_status(frequencies, values_db)

    return _common._format_result(status)


async def handle_limit_save(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Save a limit line to JSON file."""
    name = arguments["name"]
    filepath = arguments["filepath"]

    safe_path = _common.validate_safe_path(
        filepath, _common._state_manager.state_directory
    )

    async with _common._limit_lock:
        limit = _common._limit_manager.get_limit(name)

    if limit is None:
        return _common._format_error(ValueError(f"Limit not found: {name}"))

    limit.save(safe_path)
    return _common._format_result({
        "status": "saved",
        "name": name,
        "filepath": str(safe_path),
    })


async def handle_limit_load(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Load a limit line from JSON file."""
    filepath = arguments["filepath"]

    safe_path = _common.validate_safe_path(
        filepath, _common._state_manager.state_directory
    )

    limit = LimitLine.load(safe_path)

    async with _common._limit_lock:
        _common._limit_manager.add_limit(limit)

    return _common._format_result({
        "status": "loaded",
        "name": limit.name,
        "segments": len(limit.segments),
    })


def get_tools() -> list[Tool]:
    """Get limit line tool definitions."""
    return [
        Tool(
            name="siggen_limit_create",
            description="Create a limit line (flat or segmented) for pass/fail testing",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Limit line name",
                    },
                    "segments": {
                        "type": "array",
                        "description": "Limit segments (for segmented limits)",
                        "items": {
                            "type": "object",
                            "properties": {
                                "start_freq_hz": {"type": "number"},
                                "stop_freq_hz": {"type": "number"},
                                "max_db": {"type": "number"},
                                "min_db": {"type": "number"},
                                "name": {"type": "string"},
                            },
                            "required": ["start_freq_hz", "stop_freq_hz"],
                        },
                    },
                    "start_freq_hz": {
                        "type": "number",
                        "description": "Start frequency for flat limit",
                    },
                    "stop_freq_hz": {
                        "type": "number",
                        "description": "Stop frequency for flat limit",
                    },
                    "max_db": {
                        "type": "number",
                        "description": "Upper limit in dB (for flat limit)",
                    },
                    "min_db": {
                        "type": "number",
                        "description": "Lower limit in dB (for flat limit)",
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional description",
                    },
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="siggen_limit_list",
            description="List all active limit lines",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="siggen_limit_remove",
            description="Remove a limit line by name",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of limit to remove",
                    },
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="siggen_limit_check",
            description="Check measurements against a named limit line",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of limit to check against",
                    },
                    "frequencies": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Measurement frequencies in Hz",
                    },
                    "values_db": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Measured values in dB",
                    },
                },
                "required": ["name", "frequencies", "values_db"],
            },
        ),
        Tool(
            name="siggen_limit_get_status",
            description="Get overall pass/fail status across all defined limits",
            inputSchema={
                "type": "object",
                "properties": {
                    "frequencies": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Measurement frequencies in Hz",
                    },
                    "values_db": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Measured values in dB",
                    },
                },
                "required": ["frequencies", "values_db"],
            },
        ),
        Tool(
            name="siggen_limit_save",
            description="Save a limit line to JSON file",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of limit to save",
                    },
                    "filepath": {
                        "type": "string",
                        "description": "Path to save limit file",
                    },
                },
                "required": ["name", "filepath"],
            },
        ),
        Tool(
            name="siggen_limit_load",
            description="Load a limit line from JSON file",
            inputSchema={
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to limit file",
                    },
                },
                "required": ["filepath"],
            },
        ),
    ]


LIMIT_HANDLERS = {
    "siggen_limit_create": handle_limit_create,
    "siggen_limit_list": handle_limit_list,
    "siggen_limit_remove": handle_limit_remove,
    "siggen_limit_check": handle_limit_check,
    "siggen_limit_get_status": handle_limit_get_status,
    "siggen_limit_save": handle_limit_save,
    "siggen_limit_load": handle_limit_load,
}
