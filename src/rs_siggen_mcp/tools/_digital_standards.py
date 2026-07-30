"""Digital standard tool handlers (LTE, 5G NR, WLAN, Bluetooth)."""

from typing import Any

from mcp.types import CallToolResult, Tool
from scpi_core import Idempotency

from . import _common


async def handle_configure_lte(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Configure LTE signal generation."""
    sg = await _common._get_siggen(host, port)
    bw = arguments["bandwidth_mhz"]
    duplex = _common.sanitize_scpi_param(arguments.get("duplex_mode", "FDD"))
    # A subsystem PRESet discards the whole baseband configuration, so a retry
    # after a hiccup would wipe the settings sent below it. ACTION.
    await sg.scpi_send("SOURce1:BB:EUTRa:PRESet", idempotency=Idempotency.ACTION)
    await sg.scpi_send(
        f"SOURce1:BB:EUTRa:DL:BW BW{bw:.0f}_00" if bw != 1.4
        else "SOURce1:BB:EUTRa:DL:BW BW1_40",
        idempotency=Idempotency.SETTING,
    )
    await sg.scpi_send(
        f"SOURce1:BB:EUTRa:DUPLex {duplex}", idempotency=Idempotency.SETTING
    )
    await sg.scpi_send("SOURce1:BB:EUTRa:STATe ON", idempotency=Idempotency.SETTING)
    return _common._format_result({
        "status": "configured",
        "standard": "LTE",
        "bandwidth_mhz": bw,
        "duplex_mode": duplex,
    })


async def handle_configure_5gnr(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Configure 5G NR signal generation."""
    sg = await _common._get_siggen(host, port)
    bw = arguments["bandwidth_mhz"]
    scs = arguments.get("subcarrier_spacing_khz", 30)
    await sg.scpi_send("SOURce1:BB:NR5G:PRESet", idempotency=Idempotency.ACTION)
    await sg.scpi_send(
        f"SOURce1:BB:NR5G:SCHed:CELL1:SUBF0:BWP0:RBNUmber {bw}",
        idempotency=Idempotency.SETTING,
    )
    await sg.scpi_send(
        f"SOURce1:BB:NR5G:SCHed:CELL1:SUBF0:BWP0:SCSPacing SCS{scs}",
        idempotency=Idempotency.SETTING,
    )
    await sg.scpi_send("SOURce1:BB:NR5G:STATe ON", idempotency=Idempotency.SETTING)
    return _common._format_result({
        "status": "configured",
        "standard": "5G NR",
        "bandwidth_mhz": bw,
        "subcarrier_spacing_khz": scs,
    })


async def handle_configure_wlan(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Configure WLAN signal generation."""
    sg = await _common._get_siggen(host, port)
    standard = _common.sanitize_scpi_param(arguments["standard"])
    bw = arguments.get("bandwidth_mhz", 20)
    await sg.scpi_send("SOURce1:BB:WLNN:PRESet", idempotency=Idempotency.ACTION)
    std_map = {
        "802.11a": "A", "802.11b": "B", "802.11g": "G",
        "802.11n": "N", "802.11ac": "AC", "802.11ax": "AX",
    }
    std_val = std_map.get(standard, "AX")
    await sg.scpi_send(
        f"SOURce1:BB:WLNN:FBLock1:STANdard {std_val}", idempotency=Idempotency.SETTING
    )
    await sg.scpi_send(
        f"SOURce1:BB:WLNN:FBLock1:BW BW{bw}", idempotency=Idempotency.SETTING
    )
    await sg.scpi_send("SOURce1:BB:WLNN:STATe ON", idempotency=Idempotency.SETTING)
    return _common._format_result({
        "status": "configured",
        "standard": f"WLAN {standard}",
        "bandwidth_mhz": bw,
    })


async def handle_configure_bluetooth(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Configure Bluetooth signal generation."""
    sg = await _common._get_siggen(host, port)
    mode = _common.sanitize_scpi_param(arguments.get("mode", "LE"))
    await sg.scpi_send("SOURce1:BB:BTOoth:PRESet", idempotency=Idempotency.ACTION)
    await sg.scpi_send(
        f"SOURce1:BB:BTOoth:PACKet:TYPE {mode}", idempotency=Idempotency.SETTING
    )
    await sg.scpi_send("SOURce1:BB:BTOoth:STATe ON", idempotency=Idempotency.SETTING)
    return _common._format_result({
        "status": "configured",
        "standard": "Bluetooth",
        "mode": mode,
    })


async def handle_generate_waveform(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Generate and calculate digital standard waveform."""
    sg = await _common._get_siggen(host, port)
    # A trigger execute starts a waveform calculation. Duplicating it is exactly
    # the class of retry ACTION exists to forbid.
    await sg.scpi_send(
        "SOURce1:BB:ARBitrary:TRIGger:EXECute", idempotency=Idempotency.ACTION
    )
    await sg.wait_opc(timeout=120.0)
    return _common._format_result({"status": "waveform_generated"})


def get_tools() -> list[Tool]:
    """Get digital standard tool definitions."""
    return [
        Tool(
            name="siggen_configure_lte",
            description="Configure LTE signal generation (requires digital standard option)",
            inputSchema={
                "type": "object",
                "properties": {
                    "bandwidth_mhz": {
                        "type": "number",
                        "description": "Channel bandwidth in MHz (1.4, 3, 5, 10, 15, 20)",
                        "enum": [1.4, 3, 5, 10, 15, 20],
                    },
                    "duplex_mode": {
                        "type": "string",
                        "description": "Duplex mode (FDD or TDD)",
                        "enum": ["FDD", "TDD"],
                        "default": "FDD",
                    },
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
                "required": ["bandwidth_mhz"],
            },
        ),
        Tool(
            name="siggen_configure_5gnr",
            description="Configure 5G NR signal generation (requires digital standard option)",
            inputSchema={
                "type": "object",
                "properties": {
                    "bandwidth_mhz": {
                        "type": "number",
                        "description": (
                            "Channel bandwidth in MHz "
                            "(5, 10, 15, 20, 25, 30, 40, 50, 60, 80, 100, 200, 400)"
                        ),
                    },
                    "subcarrier_spacing_khz": {
                        "type": "integer",
                        "description": "Subcarrier spacing in kHz (15, 30, 60, 120, 240)",
                        "default": 30,
                    },
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
                "required": ["bandwidth_mhz"],
            },
        ),
        Tool(
            name="siggen_configure_wlan",
            description="Configure WLAN/WiFi signal generation (requires digital standard option)",
            inputSchema={
                "type": "object",
                "properties": {
                    "standard": {
                        "type": "string",
                        "description": "WLAN standard",
                        "enum": [
                            "802.11a", "802.11b", "802.11g",
                            "802.11n", "802.11ac", "802.11ax",
                        ],
                    },
                    "bandwidth_mhz": {
                        "type": "number",
                        "description": "Channel bandwidth in MHz (20, 40, 80, 160)",
                        "default": 20,
                    },
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
                "required": ["standard"],
            },
        ),
        Tool(
            name="siggen_configure_bluetooth",
            description="Configure Bluetooth signal generation (requires digital standard option)",
            inputSchema={
                "type": "object",
                "properties": {
                    "mode": {
                        "type": "string",
                        "description": "Bluetooth mode",
                        "enum": ["BR", "EDR", "LE"],
                        "default": "LE",
                    },
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
            },
        ),
        Tool(
            name="siggen_generate_waveform",
            description="Generate and calculate digital standard waveform",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
            },
        ),
    ]


DIGITAL_STANDARDS_HANDLERS = {
    "siggen_configure_lte": handle_configure_lte,
    "siggen_configure_5gnr": handle_configure_5gnr,
    "siggen_configure_wlan": handle_configure_wlan,
    "siggen_configure_bluetooth": handle_configure_bluetooth,
    "siggen_generate_waveform": handle_generate_waveform,
}
