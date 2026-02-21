"""MCP tool definitions and handlers for R&S signal generator operations."""

import asyncio
import logging
from typing import Any

from mcp.types import TextContent, Tool

from .config import get_settings
from .driver import RSSignalGeneratorDriver
from .exceptions import SignalGeneratorError
from .limits import LimitManager
from .models import InstrumentInfo
from .state import InstrumentState, StateManager
from .templates import (
    CWSignalTemplate,
    ImmunityTestTemplate,
    LTEDownlinkTemplate,
    NR5GTemplate,
    SignalTemplate,
    TwoToneTemplate,
    WLANTemplate,
)

logger = logging.getLogger(__name__)

# Global connection manager
_siggen_connections: dict[str, RSSignalGeneratorDriver] = {}

# Global template storage
_current_template: SignalTemplate | None = None

# Global limit manager
_limit_manager = LimitManager()

# Global state manager
_state_manager = StateManager()


def _get_connection_key(host: str, port: int) -> str:
    """Generate unique key for connection."""
    return f"{host}:{port}"


async def _get_siggen(
    host: str | None = None, port: int | None = None
) -> RSSignalGeneratorDriver:
    """Get or create signal generator connection."""
    settings = get_settings()
    host = host or settings.default_host
    port = port or settings.default_port
    key = _get_connection_key(host, port)

    if key in _siggen_connections:
        sg = _siggen_connections[key]
        if sg.is_connected:
            return sg

    # Create new connection
    sg = RSSignalGeneratorDriver(
        host=host,
        port=port,
        timeout=settings.connection_timeout,
        command_timeout=settings.command_timeout,
        safety_limits=settings.get_safety_limits(),
    )
    await sg.connect()
    _siggen_connections[key] = sg
    return sg


async def _close_siggen(host: str, port: int) -> bool:
    """Close signal generator connection."""
    key = _get_connection_key(host, port)
    if key in _siggen_connections:
        sg = _siggen_connections.pop(key)
        await sg.disconnect()
        return True
    return False


def _format_result(result: Any) -> list[TextContent]:
    """Format result as MCP TextContent."""
    import json

    if isinstance(result, dict):
        text = json.dumps(result, indent=2, default=str)
    elif isinstance(result, list):
        text = json.dumps(result, indent=2, default=str)
    else:
        text = str(result)
    return [TextContent(type="text", text=text)]


def _format_error(error: Exception) -> list[TextContent]:
    """Format error as MCP TextContent."""
    return [TextContent(type="text", text=f"Error: {error}")]


# =============================================================================
# Tool Definitions
# =============================================================================

def get_tools() -> list[Tool]:
    """Get all MCP tool definitions."""
    return [
        # =====================================================================
        # Connection Tools
        # =====================================================================
        Tool(
            name="siggen_discover",
            description="Scan for R&S signal generators on the network (port 5025)",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {
                        "type": "string",
                        "description": "Host to scan (default: from settings)",
                    },
                    "start_port": {
                        "type": "integer",
                        "description": "Start port (default: 5025)",
                        "default": 5025,
                    },
                    "end_port": {
                        "type": "integer",
                        "description": "End port (default: 5035)",
                        "default": 5035,
                    },
                },
            },
        ),
        Tool(
            name="siggen_connect",
            description="Connect to R&S signal generator at specified host:port",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {
                        "type": "string",
                        "description": "Signal generator hostname or IP",
                    },
                    "port": {
                        "type": "integer",
                        "description": "TCP port (default: 5025)",
                    },
                },
            },
        ),
        Tool(
            name="siggen_disconnect",
            description="Disconnect from signal generator (turns off RF output first)",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
            },
        ),
        Tool(
            name="siggen_identify",
            description=(
                "Get signal generator identification (*IDN?): "
                "manufacturer, model, serial, firmware, capabilities"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
            },
        ),
        Tool(
            name="siggen_get_status",
            description="Get signal generator connection and configuration status",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
            },
        ),
        Tool(
            name="siggen_get_model_info",
            description=(
                "Get detailed model capabilities "
                "(max freq, IQ BW, ARB support, digital standards)"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
            },
        ),

        # =====================================================================
        # RF Output Tools
        # =====================================================================
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

        # =====================================================================
        # Analog Modulation Tools
        # =====================================================================
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

        # =====================================================================
        # IQ Modulation Tools
        # =====================================================================
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

        # =====================================================================
        # ARB Waveform Tools
        # =====================================================================
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

        # =====================================================================
        # Digital Standard Tools
        # =====================================================================
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

        # =====================================================================
        # Sweep Tools
        # =====================================================================
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

        # =====================================================================
        # Reference Oscillator Tools
        # =====================================================================
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

        # =====================================================================
        # Calibration Tools
        # =====================================================================
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

        # =====================================================================
        # Raw SCPI Tools
        # =====================================================================
        Tool(
            name="siggen_scpi_send",
            description="Send raw SCPI command (no response expected)",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "SCPI command string",
                    },
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
                "required": ["command"],
            },
        ),
        Tool(
            name="siggen_scpi_query",
            description="Send SCPI query and return response",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "SCPI query (should end with ?)",
                    },
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
                "required": ["command"],
            },
        ),
        Tool(
            name="siggen_reset",
            description="Reset signal generator to default state (*RST)",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
            },
        ),
        Tool(
            name="siggen_preset",
            description="Preset signal generator (SYSTem:PRESet)",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
            },
        ),

        # =====================================================================
        # Template Tools
        # =====================================================================
        Tool(
            name="siggen_list_templates",
            description="List available signal configuration templates",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="siggen_load_template",
            description="Load signal configuration template (preset name or file path)",
            inputSchema={
                "type": "object",
                "properties": {
                    "template": {
                        "type": "string",
                        "description": (
                            "Template name (cw_wifi_24ghz, cw_1ghz, "
                            "iec_61000_4_3, iso_11452_2, lte_band1_10mhz, "
                            "lte_band7_20mhz, nr5g_n78_100mhz, nr5g_n41_50mhz, "
                            "wlan_wifi6_80mhz, wlan_wifi6e_160mhz, "
                            "two_tone_1mhz, two_tone_10mhz) or JSON file path"
                        ),
                    },
                    "frequency_hz": {
                        "type": "number",
                        "description": "Custom frequency for CW templates",
                    },
                    "power_dbm": {
                        "type": "number",
                        "description": "Custom power level",
                    },
                },
                "required": ["template"],
            },
        ),
        Tool(
            name="siggen_apply_template",
            description="Apply loaded template configuration to signal generator",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
            },
        ),

        # =====================================================================
        # State Management Tools
        # =====================================================================
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


# =============================================================================
# Tool Handlers
# =============================================================================

async def handle_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """
    Handle tool invocation.

    Args:
        name: Tool name
        arguments: Tool arguments

    Returns:
        List of TextContent with result
    """
    global _current_template

    try:
        # Extract common parameters
        host = arguments.get("host")
        port = arguments.get("port")

        # =================================================================
        # Connection Tools
        # =================================================================
        if name == "siggen_discover":
            return await _handle_discover(arguments)
        elif name == "siggen_connect":
            sg = await _get_siggen(host, port)
            return _format_result({
                "status": "connected",
                "address": sg.address,
                "instrument": sg.info.to_dict() if sg.info else None,
            })
        elif name == "siggen_disconnect":
            settings = get_settings()
            h = host or settings.default_host
            p = port or settings.default_port
            success = await _close_siggen(h, p)
            return _format_result({"status": "disconnected" if success else "not_connected"})
        elif name == "siggen_identify":
            sg = await _get_siggen(host, port)
            info = await sg.identify()
            return _format_result(info.to_dict())
        elif name == "siggen_get_status":
            sg = await _get_siggen(host, port)
            status = sg.get_status()
            return _format_result(status)
        elif name == "siggen_get_model_info":
            sg = await _get_siggen(host, port)
            if sg.info:
                return _format_result(sg.info.to_dict())
            return _format_result({"error": "No instrument info available"})

        # =================================================================
        # RF Output Tools
        # =================================================================
        elif name == "siggen_set_frequency":
            sg = await _get_siggen(host, port)
            await sg.set_frequency(arguments["frequency_hz"])
            return _format_result({
                "status": "configured",
                "frequency_hz": arguments["frequency_hz"],
            })
        elif name == "siggen_set_power":
            sg = await _get_siggen(host, port)
            await sg.set_power(arguments["power_dbm"])
            return _format_result({
                "status": "configured",
                "power_dbm": arguments["power_dbm"],
            })
        elif name == "siggen_output_on":
            sg = await _get_siggen(host, port)
            await sg.output_on()
            return _format_result({"status": "rf_output_enabled"})
        elif name == "siggen_output_off":
            sg = await _get_siggen(host, port)
            await sg.output_off()
            return _format_result({"status": "rf_output_disabled"})
        elif name == "siggen_set_phase":
            sg = await _get_siggen(host, port)
            await sg.set_phase(arguments["phase_deg"])
            return _format_result({
                "status": "configured",
                "phase_deg": arguments["phase_deg"],
            })

        # =================================================================
        # Analog Modulation Tools
        # =================================================================
        elif name == "siggen_configure_am":
            sg = await _get_siggen(host, port)
            await sg.configure_am(
                arguments["depth_percent"],
                arguments.get("enable", True),
            )
            return _format_result({
                "status": "configured",
                "am_depth_percent": arguments["depth_percent"],
                "enabled": arguments.get("enable", True),
            })
        elif name == "siggen_configure_fm":
            sg = await _get_siggen(host, port)
            await sg.configure_fm(
                arguments["deviation_hz"],
                arguments.get("enable", True),
            )
            return _format_result({
                "status": "configured",
                "fm_deviation_hz": arguments["deviation_hz"],
                "enabled": arguments.get("enable", True),
            })
        elif name == "siggen_configure_pm":
            sg = await _get_siggen(host, port)
            await sg.configure_pm(
                arguments["deviation_rad"],
                arguments.get("enable", True),
            )
            return _format_result({
                "status": "configured",
                "pm_deviation_rad": arguments["deviation_rad"],
                "enabled": arguments.get("enable", True),
            })
        elif name == "siggen_configure_pulse":
            sg = await _get_siggen(host, port)
            await sg.configure_pulse(
                arguments["width_s"],
                arguments.get("period_s"),
                arguments.get("enable", True),
            )
            return _format_result({
                "status": "configured",
                "pulse_width_s": arguments["width_s"],
                "pulse_period_s": arguments.get("period_s"),
                "enabled": arguments.get("enable", True),
            })
        elif name == "siggen_modulation_all_off":
            sg = await _get_siggen(host, port)
            await sg.modulation_all_off()
            return _format_result({"status": "all_modulations_off"})

        # =================================================================
        # IQ Modulation Tools
        # =================================================================
        elif name == "siggen_iq_on":
            sg = await _get_siggen(host, port)
            await sg.iq_on()
            return _format_result({"status": "iq_modulation_enabled"})
        elif name == "siggen_iq_off":
            sg = await _get_siggen(host, port)
            await sg.iq_off()
            return _format_result({"status": "iq_modulation_disabled"})
        elif name == "siggen_configure_iq_impairments":
            sg = await _get_siggen(host, port)
            if "gain_imbalance_db" in arguments:
                await sg.scpi_send(
                    f"SOURce:IQ:IMPairment:LEAKage:I {arguments.get('i_offset_percent', 0)}"
                )
                await sg.scpi_send(
                    f"SOURce:IQ:IMPairment:LEAKage:Q {arguments.get('q_offset_percent', 0)}"
                )
                gain = arguments.get('gain_imbalance_db', 0)
                await sg.scpi_send(
                    f"SOURce:IQ:IMPairment:IQRatio:MAGNitude {gain}"
                )
                quad = arguments.get('quadrature_offset_deg', 0)
                await sg.scpi_send(
                    f"SOURce:IQ:IMPairment:QUADrature:ANGLe {quad}"
                )
                await sg.scpi_send("SOURce:IQ:IMPairment:STATe ON")
            return _format_result({"status": "iq_impairments_configured"})

        # =================================================================
        # ARB Waveform Tools
        # =================================================================
        elif name == "siggen_load_waveform":
            sg = await _get_siggen(host, port)
            await sg.load_waveform(arguments["waveform_path"])
            return _format_result({
                "status": "waveform_loaded",
                "path": arguments["waveform_path"],
            })
        elif name == "siggen_arb_on":
            sg = await _get_siggen(host, port)
            await sg.arb_on()
            return _format_result({"status": "arb_enabled"})
        elif name == "siggen_arb_off":
            sg = await _get_siggen(host, port)
            await sg.arb_off()
            return _format_result({"status": "arb_disabled"})
        elif name == "siggen_set_arb_clock":
            sg = await _get_siggen(host, port)
            await sg.scpi_send(f"SOURce1:BB:ARBitrary:CLOCk {arguments['clock_hz']}")
            return _format_result({
                "status": "configured",
                "arb_clock_hz": arguments["clock_hz"],
            })
        elif name == "siggen_list_waveforms":
            sg = await _get_siggen(host, port)
            directory = arguments.get("directory", "/var/user/waveform")
            response = await sg.scpi_query(f"MMEMory:CATalog? '{directory}'")
            return _format_result({
                "directory": directory,
                "contents": response,
            })

        # =================================================================
        # Digital Standard Tools
        # =================================================================
        elif name == "siggen_configure_lte":
            sg = await _get_siggen(host, port)
            bw = arguments["bandwidth_mhz"]
            duplex = arguments.get("duplex_mode", "FDD")
            await sg.scpi_send("SOURce1:BB:EUTRa:PRESet")
            await sg.scpi_send(f"SOURce1:BB:EUTRa:DL:BW BW{bw:.0f}_00" if bw != 1.4
                               else "SOURce1:BB:EUTRa:DL:BW BW1_40")
            await sg.scpi_send(f"SOURce1:BB:EUTRa:DUPLex {duplex}")
            await sg.scpi_send("SOURce1:BB:EUTRa:STATe ON")
            return _format_result({
                "status": "configured",
                "standard": "LTE",
                "bandwidth_mhz": bw,
                "duplex_mode": duplex,
            })
        elif name == "siggen_configure_5gnr":
            sg = await _get_siggen(host, port)
            bw = arguments["bandwidth_mhz"]
            scs = arguments.get("subcarrier_spacing_khz", 30)
            await sg.scpi_send("SOURce1:BB:NR5G:PRESet")
            await sg.scpi_send(f"SOURce1:BB:NR5G:SCHed:CELL1:SUBF0:BWP0:RBNUmber {bw}")
            await sg.scpi_send(f"SOURce1:BB:NR5G:SCHed:CELL1:SUBF0:BWP0:SCSPacing SCS{scs}")
            await sg.scpi_send("SOURce1:BB:NR5G:STATe ON")
            return _format_result({
                "status": "configured",
                "standard": "5G NR",
                "bandwidth_mhz": bw,
                "subcarrier_spacing_khz": scs,
            })
        elif name == "siggen_configure_wlan":
            sg = await _get_siggen(host, port)
            standard = arguments["standard"]
            bw = arguments.get("bandwidth_mhz", 20)
            await sg.scpi_send("SOURce1:BB:WLNN:PRESet")
            # Map standard to R&S SCPI parameter
            std_map = {
                "802.11a": "A", "802.11b": "B", "802.11g": "G",
                "802.11n": "N", "802.11ac": "AC", "802.11ax": "AX",
            }
            std_val = std_map.get(standard, "AX")
            await sg.scpi_send(f"SOURce1:BB:WLNN:FBLock1:STANdard {std_val}")
            await sg.scpi_send(f"SOURce1:BB:WLNN:FBLock1:BW BW{bw}")
            await sg.scpi_send("SOURce1:BB:WLNN:STATe ON")
            return _format_result({
                "status": "configured",
                "standard": f"WLAN {standard}",
                "bandwidth_mhz": bw,
            })
        elif name == "siggen_configure_bluetooth":
            sg = await _get_siggen(host, port)
            mode = arguments.get("mode", "LE")
            await sg.scpi_send("SOURce1:BB:BTOoth:PRESet")
            await sg.scpi_send(f"SOURce1:BB:BTOoth:PACKet:TYPE {mode}")
            await sg.scpi_send("SOURce1:BB:BTOoth:STATe ON")
            return _format_result({
                "status": "configured",
                "standard": "Bluetooth",
                "mode": mode,
            })
        elif name == "siggen_generate_waveform":
            sg = await _get_siggen(host, port)
            await sg.scpi_send("SOURce1:BB:ARBitrary:TRIGger:EXECute")
            await sg._scpi.wait_opc(timeout=120.0)
            return _format_result({"status": "waveform_generated"})

        # =================================================================
        # Sweep Tools
        # =================================================================
        elif name == "siggen_configure_freq_sweep":
            sg = await _get_siggen(host, port)
            start = arguments["start_freq_hz"]
            stop = arguments["stop_freq_hz"]
            sg._safety.validate_frequency_range(start, stop)
            await sg.scpi_send(f"SOURce1:FREQuency:STARt {start}")
            await sg.scpi_send(f"SOURce1:FREQuency:STOP {stop}")
            if "step_hz" in arguments:
                await sg.scpi_send(f"SOURce1:SWEep:FREQuency:STEP:LINear {arguments['step_hz']}")
            dwell = arguments.get("dwell_time_s", 0.01)
            await sg.scpi_send(f"SOURce1:SWEep:FREQuency:DWELl {dwell}")
            await sg.scpi_send("SOURce1:FREQuency:MODE SWEep")
            return _format_result({
                "status": "configured",
                "mode": "frequency_sweep",
                "start_freq_hz": start,
                "stop_freq_hz": stop,
            })
        elif name == "siggen_configure_power_sweep":
            sg = await _get_siggen(host, port)
            start = arguments["start_power_dbm"]
            stop = arguments["stop_power_dbm"]
            sg._safety.validate_power(start)
            sg._safety.validate_power(stop)
            await sg.scpi_send(f"SOURce1:POWer:STARt {start}")
            await sg.scpi_send(f"SOURce1:POWer:STOP {stop}")
            if "step_db" in arguments:
                await sg.scpi_send(f"SOURce1:SWEep:POWer:STEP {arguments['step_db']}")
            dwell = arguments.get("dwell_time_s", 0.01)
            await sg.scpi_send(f"SOURce1:SWEep:POWer:DWELl {dwell}")
            await sg.scpi_send("SOURce1:POWer:MODE SWEep")
            return _format_result({
                "status": "configured",
                "mode": "power_sweep",
                "start_power_dbm": start,
                "stop_power_dbm": stop,
            })
        elif name == "siggen_configure_list_mode":
            sg = await _get_siggen(host, port)
            freqs = arguments["frequencies_hz"]
            powers = arguments["powers_dbm"]
            if len(freqs) != len(powers):
                return _format_error(
                    ValueError("frequencies_hz and powers_dbm must have same length")
                )
            # Validate all values
            for f in freqs:
                sg._safety.validate_frequency(f)
            for p in powers:
                sg._safety.validate_power(p)
            freq_str = ",".join(str(f) for f in freqs)
            pow_str = ",".join(str(p) for p in powers)
            await sg.scpi_send(f"SOURce1:LIST:FREQuency {freq_str}")
            await sg.scpi_send(f"SOURce1:LIST:POWer {pow_str}")
            dwell = arguments.get("dwell_time_s", 0.01)
            dwell_str = ",".join([str(dwell)] * len(freqs))
            await sg.scpi_send(f"SOURce1:LIST:DWELl {dwell_str}")
            await sg.scpi_send("SOURce1:FREQuency:MODE LIST")
            return _format_result({
                "status": "configured",
                "mode": "list",
                "points": len(freqs),
            })

        # =================================================================
        # Reference Oscillator Tools
        # =================================================================
        elif name == "siggen_set_reference_source":
            sg = await _get_siggen(host, port)
            await sg.set_reference_source(arguments["source"])
            return _format_result({
                "status": "configured",
                "reference_source": arguments["source"],
            })
        elif name == "siggen_get_reference_status":
            sg = await _get_siggen(host, port)
            source = await sg.get_reference_source()
            return _format_result({
                "reference_source": source.strip(),
            })

        # =================================================================
        # Calibration Tools
        # =================================================================
        elif name == "siggen_run_calibration":
            sg = await _get_siggen(host, port)
            result = await sg.run_calibration()
            return _format_result({
                "status": "calibration_complete",
                "result": result,
            })
        elif name == "siggen_get_calibration_status":
            sg = await _get_siggen(host, port)
            try:
                cal_date = await sg.scpi_query("CALibration:DATE?")
            except Exception:
                cal_date = "unknown"
            return _format_result({
                "last_calibration_date": cal_date.strip(),
            })

        # =================================================================
        # Raw SCPI Tools
        # =================================================================
        elif name == "siggen_scpi_send":
            sg = await _get_siggen(host, port)
            await sg.scpi_send(arguments["command"])
            return _format_result({"status": "sent", "command": arguments["command"]})
        elif name == "siggen_scpi_query":
            sg = await _get_siggen(host, port)
            response = await sg.scpi_query(arguments["command"])
            return _format_result({"command": arguments["command"], "response": response})
        elif name == "siggen_reset":
            sg = await _get_siggen(host, port)
            await sg.reset()
            return _format_result({"status": "reset"})
        elif name == "siggen_preset":
            sg = await _get_siggen(host, port)
            await sg.preset()
            return _format_result({"status": "preset"})

        # =================================================================
        # Template Tools
        # =================================================================
        elif name == "siggen_list_templates":
            return _format_result({
                "presets": [
                    {"name": "cw_1ghz", "description": "CW signal at 1 GHz, -10 dBm"},
                    {"name": "cw_wifi_24ghz", "description": "CW at WiFi 2.4 GHz ch 6"},
                    {"name": "cw_wifi_5ghz", "description": "CW at WiFi 5 GHz band center"},
                    {"name": "cw_lte_band1", "description": "CW at LTE Band 1 DL center"},
                    {"name": "cw_ism_915mhz", "description": "CW at 915 MHz ISM band"},
                    {
                        "name": "iec_61000_4_3_level3",
                        "description": "IEC 61000-4-3 Level 3 (10 V/m)",
                    },
                    {
                        "name": "iec_61000_4_3_level1",
                        "description": "IEC 61000-4-3 Level 1 (1 V/m)",
                    },
                    {
                        "name": "iec_61000_4_3_level2",
                        "description": "IEC 61000-4-3 Level 2 (3 V/m)",
                    },
                    {
                        "name": "iec_61000_4_3_level4",
                        "description": "IEC 61000-4-3 Level 4 (30 V/m)",
                    },
                    {
                        "name": "iso_11452_2",
                        "description": "ISO 11452-2 immunity (200 V/m)",
                    },
                    {
                        "name": "lte_band1_10mhz",
                        "description": "LTE FDD Band 1 10 MHz downlink",
                    },
                    {
                        "name": "lte_band7_20mhz",
                        "description": "LTE FDD Band 7 20 MHz downlink",
                    },
                    {
                        "name": "nr5g_n78_100mhz",
                        "description": "5G NR Band n78 100 MHz",
                    },
                    {
                        "name": "nr5g_n41_50mhz",
                        "description": "5G NR Band n41 50 MHz",
                    },
                    {
                        "name": "wlan_wifi6_80mhz",
                        "description": "WiFi 6 (802.11ax) 80 MHz",
                    },
                    {
                        "name": "wlan_wifi6e_160mhz",
                        "description": "WiFi 6E (802.11ax) 160 MHz",
                    },
                    {
                        "name": "two_tone_1mhz",
                        "description": "Two-tone 1 MHz spacing for IP3/IMD testing",
                    },
                    {
                        "name": "two_tone_10mhz",
                        "description": "Two-tone 10 MHz spacing",
                    },
                ],
                "custom": "Provide frequency_hz and power_dbm for custom CW templates",
            })
        elif name == "siggen_load_template":
            template_name = arguments["template"]
            freq = arguments.get("frequency_hz")
            power = arguments.get("power_dbm")

            if template_name == "cw_1ghz":
                _current_template = CWSignalTemplate.at_frequency(1e9)
            elif template_name == "cw_wifi_24ghz":
                _current_template = CWSignalTemplate.wifi_24ghz_carrier()
            elif template_name == "cw_wifi_5ghz":
                _current_template = CWSignalTemplate.wifi_5ghz_carrier()
            elif template_name == "cw_lte_band1":
                _current_template = CWSignalTemplate.lte_band_1()
            elif template_name == "cw_ism_915mhz":
                _current_template = CWSignalTemplate.ism_915mhz()
            elif template_name.startswith("iec_61000_4_3"):
                level = 3
                if "level1" in template_name:
                    level = 1
                elif "level2" in template_name:
                    level = 2
                elif "level4" in template_name:
                    level = 4
                _current_template = ImmunityTestTemplate.iec_61000_4_3(level)
            elif template_name == "iso_11452_2":
                _current_template = ImmunityTestTemplate.iso_11452_2()
            elif template_name == "lte_band1_10mhz":
                _current_template = LTEDownlinkTemplate.band_1_10mhz()
            elif template_name == "lte_band7_20mhz":
                _current_template = LTEDownlinkTemplate.band_7_20mhz()
            elif template_name == "nr5g_n78_100mhz":
                _current_template = NR5GTemplate.n78_100mhz()
            elif template_name == "nr5g_n41_50mhz":
                _current_template = NR5GTemplate.n41_50mhz()
            elif template_name == "wlan_wifi6_80mhz":
                _current_template = WLANTemplate.wifi6_80mhz()
            elif template_name == "wlan_wifi6e_160mhz":
                _current_template = WLANTemplate.wifi6e_160mhz()
            elif template_name == "two_tone_1mhz":
                _current_template = TwoToneTemplate.standard_1mhz_spacing()
            elif template_name == "two_tone_10mhz":
                _current_template = TwoToneTemplate.standard_10mhz_spacing()
            elif freq is not None:
                _current_template = CWSignalTemplate.at_frequency(
                    freq, power or -10.0
                )
            elif template_name.endswith(".json"):
                _current_template = SignalTemplate.load(template_name)
            else:
                return _format_error(ValueError(f"Unknown template: {template_name}"))

            if power is not None and _current_template is not None:
                _current_template.power_dbm = power

            return _format_result({
                "status": "template_loaded",
                "template": _current_template.get_summary() if _current_template else None,
            })
        elif name == "siggen_apply_template":
            if _current_template is None:
                return _format_error(
                    ValueError("No template loaded. Use siggen_load_template first.")
                )
            sg = await _get_siggen(host, port)
            await sg.set_frequency(_current_template.frequency_hz)
            await sg.set_power(_current_template.power_dbm)

            # Apply modulation if specified
            mod = _current_template.modulation_config
            if mod.get("am_enabled"):
                await sg.configure_am(mod.get("am_depth_percent", 80.0), enable=True)
            else:
                await sg.scpi_send("SOURce1:AM:STATe OFF")

            if _current_template.output_enabled:
                await sg.output_on()

            return _format_result({
                "status": "template_applied",
                "template": _current_template.name,
                "frequency_hz": _current_template.frequency_hz,
                "power_dbm": _current_template.power_dbm,
            })

        # =================================================================
        # State Management Tools
        # =================================================================
        elif name == "siggen_save_state":
            sg = await _get_siggen(host, port)
            state = await _state_manager.capture_state(sg)
            if arguments.get("notes"):
                state.notes = arguments["notes"]
            state.save(arguments["filepath"])
            return _format_result({
                "status": "state_saved",
                "filepath": arguments["filepath"],
                "summary": state.get_summary(),
            })
        elif name == "siggen_load_state":
            sg = await _get_siggen(host, port)
            state = InstrumentState.load(arguments["filepath"])
            await _state_manager.restore_state(sg, state)
            return _format_result({
                "status": "state_restored",
                "filepath": arguments["filepath"],
                "summary": state.get_summary(),
            })
        elif name == "siggen_get_full_state":
            sg = await _get_siggen(host, port)
            state = await _state_manager.capture_state(sg)
            return _format_result(state.to_dict())

        else:
            return _format_error(ValueError(f"Unknown tool: {name}"))

    except SignalGeneratorError as e:
        logger.error(f"Signal generator error in {name}: {e}")
        return _format_error(e)
    except Exception as e:
        logger.error(f"Unexpected error in {name}: {e}")
        return _format_error(e)


async def _handle_discover(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle signal generator discovery."""
    settings = get_settings()
    host = arguments.get("host", settings.default_host)
    start_port = arguments.get("start_port", 5025)
    end_port = arguments.get("end_port", 5035)

    discovered = []

    for port in range(start_port, end_port + 1):
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=1.0,
            )
            # Send *IDN? query
            writer.write(b"*IDN?\n")
            await writer.drain()

            data = await asyncio.wait_for(reader.readline(), timeout=2.0)
            idn = data.decode().strip()

            writer.close()
            await writer.wait_closed()

            if idn:
                info = InstrumentInfo.from_idn(idn)
                discovered.append({
                    "host": host,
                    "port": port,
                    "idn": idn,
                    "instrument": info.to_dict(),
                })

        except Exception:
            continue

    return _format_result({
        "scanned": f"{host}:{start_port}-{end_port}",
        "found": len(discovered),
        "instruments": discovered,
    })
