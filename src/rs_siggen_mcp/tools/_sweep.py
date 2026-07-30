"""Sweep tool handlers (frequency sweep, power sweep, list mode)."""

from typing import Any

from mcp.types import CallToolResult, Tool
from scpi_core import Idempotency

from . import _common


async def handle_configure_freq_sweep(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Configure frequency sweep mode."""
    sg = await _common._get_siggen(host, port)
    start = arguments["start_freq_hz"]
    stop = arguments["stop_freq_hz"]
    sg.validate_frequency_range(start, stop)
    await sg.scpi_send(
        f"SOURce1:FREQuency:STARt {start}", idempotency=Idempotency.SETTING
    )
    await sg.scpi_send(
        f"SOURce1:FREQuency:STOP {stop}", idempotency=Idempotency.SETTING
    )
    if "step_hz" in arguments:
        await sg.scpi_send(
            f"SOURce1:SWEep:FREQuency:STEP:LINear {arguments['step_hz']}",
            idempotency=Idempotency.SETTING,
        )
    dwell = arguments.get("dwell_time_s", 0.01)
    await sg.scpi_send(
        f"SOURce1:SWEep:FREQuency:DWELl {dwell}", idempotency=Idempotency.SETTING
    )
    # Switching FREQuency:MODE to SWEep starts the sweep running -- a state
    # transition, not a value assignment, so it must never be re-sent.
    await sg.scpi_send("SOURce1:FREQuency:MODE SWEep", idempotency=Idempotency.ACTION)
    return _common._format_result({
        "status": "configured",
        "mode": "frequency_sweep",
        "start_freq_hz": start,
        "stop_freq_hz": stop,
    })


async def handle_configure_power_sweep(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Configure power sweep mode."""
    sg = await _common._get_siggen(host, port)
    start = arguments["start_power_dbm"]
    stop = arguments["stop_power_dbm"]
    sg.validate_power(start)
    sg.validate_power(stop)
    await sg.scpi_send(f"SOURce1:POWer:STARt {start}", idempotency=Idempotency.SETTING)
    await sg.scpi_send(f"SOURce1:POWer:STOP {stop}", idempotency=Idempotency.SETTING)
    if "step_db" in arguments:
        await sg.scpi_send(
            f"SOURce1:SWEep:POWer:STEP {arguments['step_db']}",
            idempotency=Idempotency.SETTING,
        )
    dwell = arguments.get("dwell_time_s", 0.01)
    await sg.scpi_send(
        f"SOURce1:SWEep:POWer:DWELl {dwell}", idempotency=Idempotency.SETTING
    )
    await sg.scpi_send("SOURce1:POWer:MODE SWEep", idempotency=Idempotency.ACTION)
    return _common._format_result({
        "status": "configured",
        "mode": "power_sweep",
        "start_power_dbm": start,
        "stop_power_dbm": stop,
    })


async def handle_configure_list_mode(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Configure list mode with frequency/power pairs."""
    sg = await _common._get_siggen(host, port)
    freqs = arguments["frequencies_hz"]
    powers = arguments["powers_dbm"]
    if len(freqs) != len(powers):
        return _common._format_error(
            ValueError("frequencies_hz and powers_dbm must have same length")
        )
    for f in freqs:
        sg.validate_frequency(f)
    for p in powers:
        sg.validate_power(p)
    freq_str = ",".join(str(f) for f in freqs)
    pow_str = ",".join(str(p) for p in powers)
    await sg.scpi_send(
        f"SOURce1:LIST:FREQuency {freq_str}", idempotency=Idempotency.SETTING
    )
    await sg.scpi_send(f"SOURce1:LIST:POWer {pow_str}", idempotency=Idempotency.SETTING)
    dwell = arguments.get("dwell_time_s", 0.01)
    dwell_str = ",".join([str(dwell)] * len(freqs))
    await sg.scpi_send(
        f"SOURce1:LIST:DWELl {dwell_str}", idempotency=Idempotency.SETTING
    )
    await sg.scpi_send("SOURce1:FREQuency:MODE LIST", idempotency=Idempotency.ACTION)
    return _common._format_result({
        "status": "configured",
        "mode": "list",
        "points": len(freqs),
    })


def get_tools() -> list[Tool]:
    """Get sweep tool definitions."""
    return [
        Tool(
            name="siggen_configure_freq_sweep",
            description="Configure frequency sweep mode",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_freq_hz": {
                        "type": "number",
                        "description": "Start frequency in Hz",
                    },
                    "stop_freq_hz": {
                        "type": "number",
                        "description": "Stop frequency in Hz",
                    },
                    "step_hz": {
                        "type": "number",
                        "description": "Step size in Hz",
                    },
                    "dwell_time_s": {
                        "type": "number",
                        "description": "Dwell time per step in seconds",
                        "default": 0.01,
                    },
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
                "required": ["start_freq_hz", "stop_freq_hz"],
            },
        ),
        Tool(
            name="siggen_configure_power_sweep",
            description="Configure power sweep/level sweep mode",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_power_dbm": {
                        "type": "number",
                        "description": "Start power in dBm",
                    },
                    "stop_power_dbm": {
                        "type": "number",
                        "description": "Stop power in dBm",
                    },
                    "step_db": {
                        "type": "number",
                        "description": "Step size in dB",
                        "default": 1.0,
                    },
                    "dwell_time_s": {
                        "type": "number",
                        "description": "Dwell time per step in seconds",
                        "default": 0.01,
                    },
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
                "required": ["start_power_dbm", "stop_power_dbm"],
            },
        ),
        Tool(
            name="siggen_configure_list_mode",
            description="Configure list mode with frequency/power pairs",
            inputSchema={
                "type": "object",
                "properties": {
                    "frequencies_hz": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "List of frequencies in Hz",
                    },
                    "powers_dbm": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "List of power levels in dBm",
                    },
                    "dwell_time_s": {
                        "type": "number",
                        "description": "Dwell time per step",
                        "default": 0.01,
                    },
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
                "required": ["frequencies_hz", "powers_dbm"],
            },
        ),
    ]


SWEEP_HANDLERS = {
    "siggen_configure_freq_sweep": handle_configure_freq_sweep,
    "siggen_configure_power_sweep": handle_configure_power_sweep,
    "siggen_configure_list_mode": handle_configure_list_mode,
}
