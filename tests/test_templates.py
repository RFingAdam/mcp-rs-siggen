"""Tests for signal templates."""

import tempfile
from pathlib import Path

from rs_siggen_mcp.templates.base import SignalTemplate
from rs_siggen_mcp.templates.cw import CWSignalTemplate
from rs_siggen_mcp.templates.immunity import ImmunityTestTemplate
from rs_siggen_mcp.templates.lte import LTEDownlinkTemplate
from rs_siggen_mcp.templates.nr5g import NR5GTemplate
from rs_siggen_mcp.templates.two_tone import TwoToneTemplate
from rs_siggen_mcp.templates.wlan import WLANTemplate


class TestSignalTemplate:
    """Test base SignalTemplate class."""

    def test_creation(self):
        """Test basic template creation."""
        template = SignalTemplate(
            name="test",
            description="Test template",
            frequency_hz=1e9,
            power_dbm=-10.0,
        )
        assert template.name == "test"
        assert template.frequency_hz == 1e9
        assert template.power_dbm == -10.0
        assert template.output_enabled is True

    def test_to_dict(self):
        """Test dictionary conversion."""
        template = SignalTemplate(
            name="test",
            description="Test",
            frequency_hz=1e9,
            power_dbm=-10.0,
        )
        d = template.to_dict()
        assert d["name"] == "test"
        assert d["frequency_hz"] == 1e9
        assert d["template_type"] == "SignalTemplate"

    def test_from_dict(self):
        """Test creation from dictionary."""
        d = {
            "name": "test",
            "description": "Test",
            "frequency_hz": 1e9,
            "power_dbm": -10.0,
        }
        template = SignalTemplate.from_dict(d)
        assert template.name == "test"
        assert template.frequency_hz == 1e9

    def test_save_and_load(self):
        """Test save to file and load back."""
        template = SignalTemplate(
            name="test",
            description="Test",
            frequency_hz=1e9,
            power_dbm=-10.0,
        )
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            filepath = f.name

        try:
            template.save(filepath)
            loaded = SignalTemplate.load(filepath)
            assert loaded.name == "test"
            assert loaded.frequency_hz == 1e9
        finally:
            Path(filepath).unlink(missing_ok=True)

    def test_get_summary(self):
        """Test summary generation."""
        template = SignalTemplate(
            name="test",
            description="Test",
            frequency_hz=1e9,
            power_dbm=-10.0,
        )
        summary = template.get_summary()
        assert summary["name"] == "test"
        assert summary["frequency_hz"] == 1e9
        assert summary["has_modulation"] is False


class TestCWSignalTemplate:
    """Test CWSignalTemplate class."""

    def test_at_frequency_ghz(self):
        """Test CW template at GHz frequency."""
        template = CWSignalTemplate.at_frequency(2.4e9)
        assert template.frequency_hz == 2.4e9
        assert template.power_dbm == -10.0
        assert "2.400 GHz" in template.name

    def test_at_frequency_mhz(self):
        """Test CW template at MHz frequency."""
        template = CWSignalTemplate.at_frequency(915e6)
        assert template.frequency_hz == 915e6
        assert "915.000 MHz" in template.name

    def test_at_frequency_khz(self):
        """Test CW template at kHz frequency."""
        template = CWSignalTemplate.at_frequency(100e3)
        assert template.frequency_hz == 100e3
        assert "100.000 kHz" in template.name

    def test_at_frequency_custom_power(self):
        """Test CW template with custom power."""
        template = CWSignalTemplate.at_frequency(1e9, power_dbm=0.0)
        assert template.power_dbm == 0.0

    def test_at_frequency_custom_name(self):
        """Test CW template with custom name."""
        template = CWSignalTemplate.at_frequency(1e9, name="My Signal")
        assert template.name == "My Signal"

    def test_wifi_24ghz(self):
        """Test WiFi 2.4 GHz preset."""
        template = CWSignalTemplate.wifi_24ghz_carrier()
        assert template.frequency_hz == 2.437e9
        assert "WiFi" in template.name

    def test_wifi_5ghz(self):
        """Test WiFi 5 GHz preset."""
        template = CWSignalTemplate.wifi_5ghz_carrier()
        assert template.frequency_hz == 5.5e9

    def test_lte_band_1(self):
        """Test LTE Band 1 preset."""
        template = CWSignalTemplate.lte_band_1()
        assert template.frequency_hz == 2.14e9

    def test_ism_915mhz(self):
        """Test ISM 915 MHz preset."""
        template = CWSignalTemplate.ism_915mhz()
        assert template.frequency_hz == 915e6

    def test_save_and_load(self):
        """Test save and load CW template."""
        template = CWSignalTemplate.at_frequency(1e9)
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            filepath = f.name

        try:
            template.save(filepath)
            loaded = SignalTemplate.load(filepath)
            assert isinstance(loaded, CWSignalTemplate)
            assert loaded.frequency_hz == 1e9
        finally:
            Path(filepath).unlink(missing_ok=True)


class TestImmunityTestTemplate:
    """Test ImmunityTestTemplate class."""

    def test_iec_61000_4_3_level3(self):
        """Test IEC 61000-4-3 Level 3."""
        template = ImmunityTestTemplate.iec_61000_4_3(test_level=3)
        assert "IEC 61000-4-3" in template.name
        assert "Level 3" in template.name
        assert template.frequency_hz == 80e6
        assert template.sweep_start_hz == 80e6
        assert template.sweep_stop_hz == 6e9
        assert template.am_depth_percent == 80.0
        assert template.am_frequency_hz == 1e3
        assert template.output_enabled is False  # Safety
        assert template.modulation_config["am_enabled"] is True

    def test_iec_61000_4_3_level1(self):
        """Test IEC 61000-4-3 Level 1."""
        template = ImmunityTestTemplate.iec_61000_4_3(test_level=1)
        assert template.power_dbm == -10.0
        assert template.metadata["field_strength_vm"] == 1

    def test_iec_61000_4_3_level4(self):
        """Test IEC 61000-4-3 Level 4."""
        template = ImmunityTestTemplate.iec_61000_4_3(test_level=4)
        assert template.power_dbm == 20.0
        assert template.metadata["field_strength_vm"] == 30

    def test_iso_11452_2(self):
        """Test ISO 11452-2."""
        template = ImmunityTestTemplate.iso_11452_2()
        assert "ISO 11452-2" in template.name
        assert template.sweep_start_hz == 200e6
        assert template.sweep_stop_hz == 2e9
        assert template.am_depth_percent == 80.0
        assert template.output_enabled is False  # Safety

    def test_iso_11452_2_custom_field(self):
        """Test ISO 11452-2 with custom field strength."""
        template = ImmunityTestTemplate.iso_11452_2(field_strength_vm=100.0)
        assert template.metadata["field_strength_vm"] == 100.0

    def test_to_dict(self):
        """Test dictionary conversion."""
        template = ImmunityTestTemplate.iec_61000_4_3(test_level=3)
        d = template.to_dict()
        assert d["sweep_start_hz"] == 80e6
        assert d["sweep_stop_hz"] == 6e9
        assert d["am_depth_percent"] == 80.0
        assert d["template_type"] == "ImmunityTestTemplate"

    def test_from_dict(self):
        """Test creation from dictionary."""
        template = ImmunityTestTemplate.iec_61000_4_3(test_level=3)
        d = template.to_dict()
        restored = ImmunityTestTemplate.from_dict(d)
        assert restored.sweep_start_hz == 80e6
        assert restored.am_depth_percent == 80.0

    def test_save_and_load(self):
        """Test save and load immunity template."""
        template = ImmunityTestTemplate.iec_61000_4_3(test_level=3)
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            filepath = f.name

        try:
            template.save(filepath)
            loaded = SignalTemplate.load(filepath)
            assert isinstance(loaded, ImmunityTestTemplate)
            assert loaded.sweep_start_hz == 80e6
        finally:
            Path(filepath).unlink(missing_ok=True)


class TestLTEDownlinkTemplate:
    """Test LTEDownlinkTemplate class."""

    def test_band_1_10mhz(self):
        """Test LTE Band 1 10 MHz template."""
        template = LTEDownlinkTemplate.band_1_10mhz()
        assert template.name == "LTE Band 1 10 MHz Downlink"
        assert template.frequency_hz == 2.14e9
        assert template.power_dbm == -10.0
        assert template.modulation_config["standard"] == "lte"
        assert template.modulation_config["bandwidth_mhz"] == 10
        assert template.modulation_config["duplex"] == "fdd"
        assert template.modulation_config["direction"] == "downlink"

    def test_band_7_20mhz(self):
        """Test LTE Band 7 20 MHz template."""
        template = LTEDownlinkTemplate.band_7_20mhz()
        assert template.name == "LTE Band 7 20 MHz Downlink"
        assert template.frequency_hz == 2.655e9
        assert template.power_dbm == -10.0
        assert template.modulation_config["bandwidth_mhz"] == 20

    def test_is_signal_template(self):
        """Test that LTEDownlinkTemplate is a SignalTemplate."""
        template = LTEDownlinkTemplate.band_1_10mhz()
        assert isinstance(template, SignalTemplate)

    def test_to_dict(self):
        """Test dictionary conversion."""
        template = LTEDownlinkTemplate.band_1_10mhz()
        d = template.to_dict()
        assert d["template_type"] == "LTEDownlinkTemplate"
        assert d["frequency_hz"] == 2.14e9
        assert d["modulation_config"]["standard"] == "lte"

    def test_save_and_load(self):
        """Test save and load LTE template."""
        template = LTEDownlinkTemplate.band_1_10mhz()
        with tempfile.NamedTemporaryFile(
            suffix=".json", delete=False
        ) as f:
            filepath = f.name

        try:
            template.save(filepath)
            loaded = SignalTemplate.load(filepath)
            assert isinstance(loaded, LTEDownlinkTemplate)
            assert loaded.frequency_hz == 2.14e9
        finally:
            Path(filepath).unlink(missing_ok=True)

    def test_get_summary(self):
        """Test summary generation."""
        template = LTEDownlinkTemplate.band_1_10mhz()
        summary = template.get_summary()
        assert summary["name"] == "LTE Band 1 10 MHz Downlink"
        assert summary["has_modulation"] is True


class TestNR5GTemplate:
    """Test NR5GTemplate class."""

    def test_n78_100mhz(self):
        """Test 5G NR n78 100 MHz template."""
        template = NR5GTemplate.n78_100mhz()
        assert template.name == "5G NR n78 100 MHz"
        assert template.frequency_hz == 3.5e9
        assert template.power_dbm == -10.0
        assert template.modulation_config["standard"] == "nr5g"
        assert template.modulation_config["bandwidth_mhz"] == 100
        assert template.modulation_config["numerology"] == 1

    def test_n41_50mhz(self):
        """Test 5G NR n41 50 MHz template."""
        template = NR5GTemplate.n41_50mhz()
        assert template.name == "5G NR n41 50 MHz"
        assert template.frequency_hz == 2.593e9
        assert template.modulation_config["bandwidth_mhz"] == 50

    def test_is_signal_template(self):
        """Test that NR5GTemplate is a SignalTemplate."""
        template = NR5GTemplate.n78_100mhz()
        assert isinstance(template, SignalTemplate)

    def test_to_dict(self):
        """Test dictionary conversion."""
        template = NR5GTemplate.n78_100mhz()
        d = template.to_dict()
        assert d["template_type"] == "NR5GTemplate"
        assert d["frequency_hz"] == 3.5e9

    def test_save_and_load(self):
        """Test save and load 5G NR template."""
        template = NR5GTemplate.n78_100mhz()
        with tempfile.NamedTemporaryFile(
            suffix=".json", delete=False
        ) as f:
            filepath = f.name

        try:
            template.save(filepath)
            loaded = SignalTemplate.load(filepath)
            assert isinstance(loaded, NR5GTemplate)
            assert loaded.frequency_hz == 3.5e9
        finally:
            Path(filepath).unlink(missing_ok=True)


class TestWLANTemplate:
    """Test WLANTemplate class."""

    def test_wifi6_80mhz(self):
        """Test WiFi 6 80 MHz template."""
        template = WLANTemplate.wifi6_80mhz()
        assert template.name == "WiFi 6 80 MHz"
        assert template.frequency_hz == 5.21e9
        assert template.power_dbm == -10.0
        assert template.modulation_config["standard"] == "wlan"
        assert template.modulation_config["protocol"] == "802.11ax"
        assert template.modulation_config["bandwidth_mhz"] == 80

    def test_wifi6e_160mhz(self):
        """Test WiFi 6E 160 MHz template."""
        template = WLANTemplate.wifi6e_160mhz()
        assert template.name == "WiFi 6E 160 MHz"
        assert template.frequency_hz == 6.105e9
        assert template.modulation_config["bandwidth_mhz"] == 160

    def test_is_signal_template(self):
        """Test that WLANTemplate is a SignalTemplate."""
        template = WLANTemplate.wifi6_80mhz()
        assert isinstance(template, SignalTemplate)

    def test_to_dict(self):
        """Test dictionary conversion."""
        template = WLANTemplate.wifi6_80mhz()
        d = template.to_dict()
        assert d["template_type"] == "WLANTemplate"
        assert d["frequency_hz"] == 5.21e9

    def test_save_and_load(self):
        """Test save and load WLAN template."""
        template = WLANTemplate.wifi6_80mhz()
        with tempfile.NamedTemporaryFile(
            suffix=".json", delete=False
        ) as f:
            filepath = f.name

        try:
            template.save(filepath)
            loaded = SignalTemplate.load(filepath)
            assert isinstance(loaded, WLANTemplate)
            assert loaded.frequency_hz == 5.21e9
        finally:
            Path(filepath).unlink(missing_ok=True)


class TestTwoToneTemplate:
    """Test TwoToneTemplate class."""

    def test_1mhz_spacing(self):
        """Test two-tone 1 MHz spacing template."""
        template = TwoToneTemplate.standard_1mhz_spacing()
        assert template.name == "Two-Tone 1 MHz Spacing"
        assert template.frequency_hz == 1e9
        assert template.power_dbm == -10.0
        assert template.modulation_config["type"] == "two_tone"
        assert template.modulation_config["spacing_hz"] == 1e6

    def test_10mhz_spacing(self):
        """Test two-tone 10 MHz spacing template."""
        template = TwoToneTemplate.standard_10mhz_spacing()
        assert template.name == "Two-Tone 10 MHz Spacing"
        assert template.modulation_config["spacing_hz"] == 10e6

    def test_custom_center_freq(self):
        """Test two-tone with custom center frequency."""
        template = TwoToneTemplate.standard_1mhz_spacing(
            center_freq_hz=2.4e9
        )
        assert template.frequency_hz == 2.4e9

    def test_is_signal_template(self):
        """Test that TwoToneTemplate is a SignalTemplate."""
        template = TwoToneTemplate.standard_1mhz_spacing()
        assert isinstance(template, SignalTemplate)

    def test_to_dict(self):
        """Test dictionary conversion."""
        template = TwoToneTemplate.standard_1mhz_spacing()
        d = template.to_dict()
        assert d["template_type"] == "TwoToneTemplate"
        assert d["frequency_hz"] == 1e9

    def test_save_and_load(self):
        """Test save and load two-tone template."""
        template = TwoToneTemplate.standard_1mhz_spacing()
        with tempfile.NamedTemporaryFile(
            suffix=".json", delete=False
        ) as f:
            filepath = f.name

        try:
            template.save(filepath)
            loaded = SignalTemplate.load(filepath)
            assert isinstance(loaded, TwoToneTemplate)
            assert loaded.frequency_hz == 1e9
        finally:
            Path(filepath).unlink(missing_ok=True)
