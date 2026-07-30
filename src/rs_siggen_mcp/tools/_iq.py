"""IQ modulation tool handlers."""

from typing import Any

from mcp.types import CallToolResult, Tool
from scpi_core import Idempotency

from . import _common


async def handle_iq_on(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Enable IQ modulation."""
    sg = await _common._get_siggen(host, port)
    await sg.iq_on()
    return _common._format_result({"status": "iq_modulation_enabled"})


async def handle_iq_off(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Disable IQ modulation."""
    sg = await _common._get_siggen(host, port)
    await sg.iq_off()
    return _common._format_result({"status": "iq_modulation_disabled"})


async def handle_configure_iq_impairments(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Configure IQ signal impairments."""
    sg = await _common._get_siggen(host, port)
    if "i_offset_percent" in arguments:
        await sg.scpi_send(
            f"SOURce:IQ:IMPairment:LEAKage:I {arguments['i_offset_percent']}",
            idempotency=Idempotency.SETTING,
        )
    if "q_offset_percent" in arguments:
        await sg.scpi_send(
            f"SOURce:IQ:IMPairment:LEAKage:Q {arguments['q_offset_percent']}",
            idempotency=Idempotency.SETTING,
        )
    if "gain_imbalance_db" in arguments:
        await sg.scpi_send(
            f"SOURce:IQ:IMPairment:IQRatio:MAGNitude {arguments['gain_imbalance_db']}",
            idempotency=Idempotency.SETTING,
        )
    if "quadrature_offset_deg" in arguments:
        await sg.scpi_send(
            f"SOURce:IQ:IMPairment:QUADrature:ANGLe {arguments['quadrature_offset_deg']}",
            idempotency=Idempotency.SETTING,
        )
    await sg.scpi_send(
        "SOURce:IQ:IMPairment:STATe ON", idempotency=Idempotency.SETTING
    )
    return _common._format_result({"status": "iq_impairments_configured"})


def get_tools() -> list[Tool]:
    """Get IQ modulation tool definitions."""
    return [
        Tool(
            name="siggen_iq_on",
            description="Enable IQ modulation (requires vector signal generator)",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
            },
        ),
        Tool(
            name="siggen_iq_off",
            description="Disable IQ modulation",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
            },
        ),
        Tool(
            name="siggen_configure_iq_impairments",
            description=(
                "Configure IQ signal impairments "
                "(gain imbalance, quadrature offset, I/Q offset)"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "gain_imbalance_db": {
                        "type": "number",
                        "description": "I/Q gain imbalance in dB",
                    },
                    "quadrature_offset_deg": {
                        "type": "number",
                        "description": "Quadrature offset in degrees",
                    },
                    "i_offset_percent": {
                        "type": "number",
                        "description": "I DC offset in percent",
                    },
                    "q_offset_percent": {
                        "type": "number",
                        "description": "Q DC offset in percent",
                    },
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
            },
        ),
    ]


IQ_HANDLERS = {
    "siggen_iq_on": handle_iq_on,
    "siggen_iq_off": handle_iq_off,
    "siggen_configure_iq_impairments": handle_configure_iq_impairments,
}
