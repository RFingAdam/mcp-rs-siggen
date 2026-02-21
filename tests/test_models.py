"""Tests for signal generator data models."""


from rs_siggen_mcp.models.siggen_types import (
    BasebandConfig,
    DigitalStandard,
    InstrumentInfo,
    ModulationConfig,
    ModulationType,
    RFConfig,
    SignalGeneratorFamily,
    SweepConfig,
    WaveformInfo,
)


class TestSignalGeneratorFamily:
    """Test SignalGeneratorFamily enum."""

    def test_all_families(self):
        """Test all families are defined."""
        families = list(SignalGeneratorFamily)
        assert len(families) == 9  # 8 models + UNKNOWN
        assert SignalGeneratorFamily.SMW200A in families
        assert SignalGeneratorFamily.SMBV100B in families
        assert SignalGeneratorFamily.SMM100A in families
        assert SignalGeneratorFamily.SMCV100B in families
        assert SignalGeneratorFamily.SGT100A in families
        assert SignalGeneratorFamily.SGS100A in families
        assert SignalGeneratorFamily.SMA100B in families
        assert SignalGeneratorFamily.SMB100B in families
        assert SignalGeneratorFamily.UNKNOWN in families

    def test_max_frequency(self):
        """Test max frequency for each family."""
        assert SignalGeneratorFamily.SMW200A.max_frequency_hz == 67e9
        assert SignalGeneratorFamily.SMBV100B.max_frequency_hz == 6e9
        assert SignalGeneratorFamily.SMM100A.max_frequency_hz == 44e9
        assert SignalGeneratorFamily.SGS100A.max_frequency_hz == 12.75e9
        assert SignalGeneratorFamily.SMA100B.max_frequency_hz == 67e9
        assert SignalGeneratorFamily.SMB100B.max_frequency_hz == 40e9

    def test_has_iq_modulation(self):
        """Test IQ modulation capability."""
        assert SignalGeneratorFamily.SMW200A.has_iq_modulation is True
        assert SignalGeneratorFamily.SMBV100B.has_iq_modulation is True
        assert SignalGeneratorFamily.SGT100A.has_iq_modulation is True
        assert SignalGeneratorFamily.SGS100A.has_iq_modulation is False
        assert SignalGeneratorFamily.SMA100B.has_iq_modulation is False
        assert SignalGeneratorFamily.SMB100B.has_iq_modulation is False

    def test_has_arb_generator(self):
        """Test ARB generator capability."""
        assert SignalGeneratorFamily.SMW200A.has_arb_generator is True
        assert SignalGeneratorFamily.SMBV100B.has_arb_generator is True
        assert SignalGeneratorFamily.SGT100A.has_arb_generator is False
        assert SignalGeneratorFamily.SGS100A.has_arb_generator is False

    def test_has_digital_standards(self):
        """Test digital standards capability."""
        assert SignalGeneratorFamily.SMW200A.has_digital_standards is True
        assert SignalGeneratorFamily.SMBV100B.has_digital_standards is True
        assert SignalGeneratorFamily.SGT100A.has_digital_standards is False
        assert SignalGeneratorFamily.SGS100A.has_digital_standards is False

    def test_iq_bandwidth(self):
        """Test IQ bandwidth for each family."""
        assert SignalGeneratorFamily.SMW200A.iq_bandwidth_hz == 2e9
        assert SignalGeneratorFamily.SMBV100B.iq_bandwidth_hz == 1e9
        assert SignalGeneratorFamily.SGS100A.iq_bandwidth_hz is None
        assert SignalGeneratorFamily.SMA100B.iq_bandwidth_hz is None


class TestInstrumentInfo:
    """Test InstrumentInfo dataclass."""

    def test_from_idn_smw200a(self):
        """Test parsing SMW200A IDN response."""
        idn = "Rohde&Schwarz,SMW200A,1412.0000K02/123456,4.30.047.29"
        info = InstrumentInfo.from_idn(idn)
        assert info.manufacturer == "Rohde&Schwarz"
        assert info.model == "SMW200A"
        assert info.serial == "1412.0000K02/123456"
        assert info.firmware == "4.30.047.29"
        assert info.family == SignalGeneratorFamily.SMW200A

    def test_from_idn_smbv100b(self):
        """Test parsing SMBV100B IDN response."""
        idn = "Rohde&Schwarz,SMBV100B,1420.7508K02/100001,5.00.042.00"
        info = InstrumentInfo.from_idn(idn)
        assert info.model == "SMBV100B"
        assert info.family == SignalGeneratorFamily.SMBV100B

    def test_from_idn_sgs100a(self):
        """Test parsing SGS100A IDN response."""
        idn = "Rohde&Schwarz,SGS100A,1416.2506K02/200001,4.10.054.30"
        info = InstrumentInfo.from_idn(idn)
        assert info.family == SignalGeneratorFamily.SGS100A

    def test_from_idn_sma100b(self):
        """Test parsing SMA100B IDN response."""
        idn = "Rohde&Schwarz,SMA100B,1429.2008K02/300001,5.00.030.00"
        info = InstrumentInfo.from_idn(idn)
        assert info.family == SignalGeneratorFamily.SMA100B

    def test_from_idn_unknown(self):
        """Test parsing unknown instrument IDN."""
        idn = "SomeOther,Model123,SN001,FW1.0"
        info = InstrumentInfo.from_idn(idn)
        assert info.family == SignalGeneratorFamily.UNKNOWN

    def test_from_idn_short(self):
        """Test parsing truncated IDN response."""
        idn = "Rohde&Schwarz,SMW200A"
        info = InstrumentInfo.from_idn(idn)
        assert info.manufacturer == "Rohde&Schwarz"
        assert info.model == "SMW200A"

    def test_to_dict(self):
        """Test dictionary conversion."""
        info = InstrumentInfo(
            manufacturer="Rohde&Schwarz",
            model="SMW200A",
            serial="123",
            firmware="4.0",
            family=SignalGeneratorFamily.SMW200A,
        )
        d = info.to_dict()
        assert d["manufacturer"] == "Rohde&Schwarz"
        assert d["model"] == "SMW200A"
        assert d["family"] == "SMW200A"
        assert d["has_iq_modulation"] is True
        assert d["max_frequency_hz"] == 67e9
        assert d["iq_bandwidth_hz"] == 2e9


class TestModulationType:
    """Test ModulationType enum."""

    def test_all_types(self):
        """Test all modulation types."""
        assert ModulationType.AM.value == "AM"
        assert ModulationType.FM.value == "FM"
        assert ModulationType.PM.value == "PM"
        assert ModulationType.PULSE.value == "PULM"
        assert ModulationType.IQ.value == "IQ"


class TestDigitalStandard:
    """Test DigitalStandard enum."""

    def test_standards(self):
        """Test all digital standards."""
        assert DigitalStandard.LTE.value == "LTE"
        assert DigitalStandard.NR5G.value == "NR5G"
        assert DigitalStandard.WLAN.value == "WLAN"
        assert DigitalStandard.BLUETOOTH.value == "BTO"


class TestRFConfig:
    """Test RFConfig dataclass."""

    def test_defaults(self):
        """Test default RF config."""
        config = RFConfig(frequency_hz=1e9, power_dbm=-10)
        assert config.output_enabled is False
        assert config.phase_deg == 0.0
        assert config.reference_source == "INTernal"

    def test_to_dict(self):
        """Test dictionary conversion."""
        config = RFConfig(frequency_hz=1e9, power_dbm=-10, output_enabled=True)
        d = config.to_dict()
        assert d["frequency_hz"] == 1e9
        assert d["power_dbm"] == -10
        assert d["output_enabled"] is True

    def test_from_dict(self):
        """Test creation from dictionary."""
        d = {"frequency_hz": 2.4e9, "power_dbm": 0.0, "output_enabled": True}
        config = RFConfig.from_dict(d)
        assert config.frequency_hz == 2.4e9
        assert config.power_dbm == 0.0
        assert config.output_enabled is True


class TestWaveformInfo:
    """Test WaveformInfo dataclass."""

    def test_creation(self):
        """Test waveform info creation."""
        wf = WaveformInfo(
            name="test_waveform",
            path="/var/user/waveform/test.wv",
            sample_rate_hz=100e6,
            samples=1000000,
        )
        assert wf.name == "test_waveform"
        assert wf.path == "/var/user/waveform/test.wv"

    def test_to_dict(self):
        """Test dictionary conversion."""
        wf = WaveformInfo(name="test", path="/path")
        d = wf.to_dict()
        assert d["name"] == "test"
        assert d["path"] == "/path"
        assert d["sample_rate_hz"] is None


class TestSweepConfig:
    """Test SweepConfig dataclass."""

    def test_defaults(self):
        """Test default sweep config."""
        config = SweepConfig(start=1e9, stop=2e9)
        assert config.start == 1e9
        assert config.stop == 2e9
        assert config.step is None
        assert config.points is None
        assert config.dwell_time_s == 0.01

    def test_with_step(self):
        """Test sweep config with step size."""
        config = SweepConfig(start=1e9, stop=2e9, step=10e6)
        assert config.step == 10e6

    def test_with_points(self):
        """Test sweep config with number of points."""
        config = SweepConfig(start=1e9, stop=2e9, points=100)
        assert config.points == 100

    def test_custom_dwell(self):
        """Test sweep config with custom dwell time."""
        config = SweepConfig(start=1e9, stop=2e9, dwell_time_s=0.5)
        assert config.dwell_time_s == 0.5

    def test_to_dict(self):
        """Test dictionary conversion."""
        config = SweepConfig(
            start=1e9, stop=2e9, step=10e6, dwell_time_s=0.1
        )
        d = config.to_dict()
        assert d["start"] == 1e9
        assert d["stop"] == 2e9
        assert d["step"] == 10e6
        assert d["points"] is None
        assert d["dwell_time_s"] == 0.1


class TestModulationConfig:
    """Test ModulationConfig dataclass."""

    def test_am_config(self):
        """Test AM modulation config."""
        config = ModulationConfig(
            mod_type="AM", enabled=True, depth_percent=80.0
        )
        assert config.mod_type == "AM"
        assert config.enabled is True
        assert config.depth_percent == 80.0
        assert config.source == "INTernal"

    def test_fm_config(self):
        """Test FM modulation config."""
        config = ModulationConfig(
            mod_type="FM", enabled=True, deviation_hz=75e3
        )
        assert config.mod_type == "FM"
        assert config.deviation_hz == 75e3

    def test_pulse_config(self):
        """Test pulse modulation config."""
        config = ModulationConfig(
            mod_type="PULSE",
            enabled=True,
            pulse_width_s=1e-6,
            pulse_period_s=10e-6,
        )
        assert config.pulse_width_s == 1e-6
        assert config.pulse_period_s == 10e-6

    def test_defaults(self):
        """Test default modulation config."""
        config = ModulationConfig(mod_type="AM")
        assert config.enabled is False
        assert config.depth_percent is None
        assert config.deviation_hz is None
        assert config.pulse_width_s is None
        assert config.pulse_period_s is None
        assert config.source == "INTernal"

    def test_to_dict_am(self):
        """Test AM config dictionary conversion."""
        config = ModulationConfig(
            mod_type="AM", enabled=True, depth_percent=80.0
        )
        d = config.to_dict()
        assert d["mod_type"] == "AM"
        assert d["enabled"] is True
        assert d["depth_percent"] == 80.0
        assert d["source"] == "INTernal"
        assert "deviation_hz" not in d
        assert "pulse_width_s" not in d

    def test_to_dict_fm(self):
        """Test FM config dictionary conversion."""
        config = ModulationConfig(
            mod_type="FM", enabled=True, deviation_hz=75e3
        )
        d = config.to_dict()
        assert d["mod_type"] == "FM"
        assert d["deviation_hz"] == 75e3
        assert "depth_percent" not in d

    def test_to_dict_pulse(self):
        """Test pulse config dictionary conversion."""
        config = ModulationConfig(
            mod_type="PULSE",
            enabled=True,
            pulse_width_s=1e-6,
            pulse_period_s=10e-6,
        )
        d = config.to_dict()
        assert d["pulse_width_s"] == 1e-6
        assert d["pulse_period_s"] == 10e-6


class TestBasebandConfig:
    """Test BasebandConfig dataclass."""

    def test_defaults(self):
        """Test default baseband config."""
        config = BasebandConfig()
        assert config.waveform_file is None
        assert config.clock_rate_hz is None
        assert config.arb_enabled is False
        assert config.digital_standard is None

    def test_arb_config(self):
        """Test ARB baseband config."""
        config = BasebandConfig(
            waveform_file="/var/user/waveform/test.wv",
            clock_rate_hz=100e6,
            arb_enabled=True,
        )
        assert config.waveform_file == "/var/user/waveform/test.wv"
        assert config.clock_rate_hz == 100e6
        assert config.arb_enabled is True

    def test_digital_standard_config(self):
        """Test digital standard baseband config."""
        config = BasebandConfig(digital_standard="LTE")
        assert config.digital_standard == "LTE"

    def test_to_dict(self):
        """Test dictionary conversion."""
        config = BasebandConfig(
            waveform_file="/var/user/waveform/test.wv",
            clock_rate_hz=100e6,
            arb_enabled=True,
            digital_standard="NR5G",
        )
        d = config.to_dict()
        assert d["waveform_file"] == "/var/user/waveform/test.wv"
        assert d["clock_rate_hz"] == 100e6
        assert d["arb_enabled"] is True
        assert d["digital_standard"] == "NR5G"

    def test_to_dict_defaults(self):
        """Test dictionary conversion with defaults."""
        config = BasebandConfig()
        d = config.to_dict()
        assert d["waveform_file"] is None
        assert d["clock_rate_hz"] is None
        assert d["arb_enabled"] is False
        assert d["digital_standard"] is None
