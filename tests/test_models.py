"""Tests for signal generator data models."""


from rs_siggen_mcp.models.siggen_types import (
    DigitalStandard,
    InstrumentInfo,
    ModulationType,
    RFConfig,
    SignalGeneratorFamily,
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
