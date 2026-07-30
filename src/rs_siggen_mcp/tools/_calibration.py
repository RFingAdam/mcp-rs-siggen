"""Calibration tool handlers."""

import logging
from typing import Any

from mcp.types import CallToolResult, Tool
from scpi_core import Idempotency

from . import _common

logger = logging.getLogger("rs_siggen_mcp.tools")


async def handle_run_calibration(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Run internal calibration."""
    sg = await _common._get_siggen(host, port)
    result = await sg.run_calibration()
    return _common._format_result({
        "status": "calibration_complete",
        "result": result,
    })


async def handle_get_calibration_status(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Get calibration status."""
    sg = await _common._get_siggen(host, port)
    try:
        cal_date = await sg.scpi_query(
            "CALibration:DATE?", idempotency=Idempotency.QUERY
        )
    except (_common.CommunicationError, _common.TimeoutError) as e:
        logger.debug("Could not query calibration date: %s", e)
        cal_date = "unknown"
    return _common._format_result({
        "last_calibration_date": cal_date.strip(),
    })


def get_tools() -> list[Tool]:
    """Get calibration tool definitions."""
    return [
        Tool(
            name="siggen_run_calibration",
            description="Run internal calibration (may take several minutes)",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
            },
        ),
        Tool(
            name="siggen_get_calibration_status",
            description="Get calibration status and last calibration date",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
            },
        ),
    ]


CALIBRATION_HANDLERS = {
    "siggen_run_calibration": handle_run_calibration,
    "siggen_get_calibration_status": handle_get_calibration_status,
}
