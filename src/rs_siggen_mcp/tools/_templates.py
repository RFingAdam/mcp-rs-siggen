"""Template tool handlers (list, load, apply)."""

from typing import Any

from mcp.types import CallToolResult, Tool
from scpi_core import Idempotency

from ..templates import (
    CWSignalTemplate,
    ImmunityTestTemplate,
    LTEDownlinkTemplate,
    NR5GTemplate,
    SignalTemplate,
    TwoToneTemplate,
    WLANTemplate,
)
from . import _common


async def handle_list_templates(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """List available signal configuration templates."""
    return _common._format_result({
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


async def handle_load_template(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Load signal configuration template."""
    template_name = arguments["template"]
    freq = arguments.get("frequency_hz")
    power = arguments.get("power_dbm")

    async with _common._template_lock:
        template: SignalTemplate | None = None

        if template_name == "cw_1ghz":
            template = CWSignalTemplate.at_frequency(1e9)
        elif template_name == "cw_wifi_24ghz":
            template = CWSignalTemplate.wifi_24ghz_carrier()
        elif template_name == "cw_wifi_5ghz":
            template = CWSignalTemplate.wifi_5ghz_carrier()
        elif template_name == "cw_lte_band1":
            template = CWSignalTemplate.lte_band_1()
        elif template_name == "cw_ism_915mhz":
            template = CWSignalTemplate.ism_915mhz()
        elif template_name.startswith("iec_61000_4_3"):
            level = 3
            if "level1" in template_name:
                level = 1
            elif "level2" in template_name:
                level = 2
            elif "level4" in template_name:
                level = 4
            template = ImmunityTestTemplate.iec_61000_4_3(level)
        elif template_name == "iso_11452_2":
            template = ImmunityTestTemplate.iso_11452_2()
        elif template_name == "lte_band1_10mhz":
            template = LTEDownlinkTemplate.band_1_10mhz()
        elif template_name == "lte_band7_20mhz":
            template = LTEDownlinkTemplate.band_7_20mhz()
        elif template_name == "nr5g_n78_100mhz":
            template = NR5GTemplate.n78_100mhz()
        elif template_name == "nr5g_n41_50mhz":
            template = NR5GTemplate.n41_50mhz()
        elif template_name == "wlan_wifi6_80mhz":
            template = WLANTemplate.wifi6_80mhz()
        elif template_name == "wlan_wifi6e_160mhz":
            template = WLANTemplate.wifi6e_160mhz()
        elif template_name == "two_tone_1mhz":
            template = TwoToneTemplate.standard_1mhz_spacing()
        elif template_name == "two_tone_10mhz":
            template = TwoToneTemplate.standard_10mhz_spacing()
        elif freq is not None:
            template = CWSignalTemplate.at_frequency(freq, power or -10.0)
        elif template_name.endswith(".json"):
            safe_template_path = _common.validate_safe_path(
                template_name, _common._state_manager.state_directory
            )
            template = SignalTemplate.load(safe_template_path)
        else:
            return _common._format_error(ValueError(f"Unknown template: {template_name}"))

        if power is not None and template is not None:
            template.power_dbm = power

        _common._current_template = template

        return _common._format_result({
            "status": "template_loaded",
            "template": template.get_summary() if template else None,
        })


async def handle_apply_template(
    arguments: dict[str, Any], host: str | None, port: int | None
) -> CallToolResult:
    """Apply loaded template configuration to signal generator."""
    async with _common._template_lock:
        if _common._current_template is None:
            return _common._format_error(
                ValueError("No template loaded. Use siggen_load_template first.")
            )
        template = _common._current_template

    sg = await _common._get_siggen(host, port)
    await sg.set_frequency(template.frequency_hz)
    await sg.set_power(template.power_dbm)

    mod = template.modulation_config

    # AM modulation
    if mod.get("am_enabled"):
        await sg.configure_am(mod.get("am_depth_percent", 80.0), enable=True)
    else:
        await sg.scpi_send("SOURce1:AM:STATe OFF", idempotency=Idempotency.SETTING)

    # FM modulation
    if mod.get("fm_enabled"):
        await sg.configure_fm(mod.get("fm_deviation_hz", 75000.0), enable=True)
    else:
        await sg.scpi_send("SOURce1:FM:STATe OFF", idempotency=Idempotency.SETTING)

    # PM modulation
    if mod.get("pm_enabled"):
        await sg.configure_pm(mod.get("pm_deviation_rad", 1.0), enable=True)
    else:
        await sg.scpi_send("SOURce1:PM:STATe OFF", idempotency=Idempotency.SETTING)

    # Pulse modulation
    if mod.get("pulse_enabled"):
        await sg.configure_pulse(
            mod.get("pulse_width_s", 1e-6),
            mod.get("pulse_period_s"),
            enable=True,
        )
    else:
        await sg.scpi_send("SOURce1:PULM:STATe OFF", idempotency=Idempotency.SETTING)

    # IQ modulation
    if mod.get("iq_enabled"):
        await sg.iq_on()
    else:
        await sg.scpi_send("SOURce:IQ:STATe OFF", idempotency=Idempotency.SETTING)

    if template.output_enabled:
        await sg.output_on()

    return _common._format_result({
        "status": "template_applied",
        "template": template.name,
        "frequency_hz": template.frequency_hz,
        "power_dbm": template.power_dbm,
    })


def get_tools() -> list[Tool]:
    """Get template tool definitions."""
    return [
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
    ]


TEMPLATE_HANDLERS = {
    "siggen_list_templates": handle_list_templates,
    "siggen_load_template": handle_load_template,
    "siggen_apply_template": handle_apply_template,
}
