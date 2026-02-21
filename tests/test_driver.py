"""Tests for signal generator driver."""


import pytest

from rs_siggen_mcp.driver.siggen_driver import RSSignalGeneratorDriver
from rs_siggen_mcp.exceptions import ConfigurationError
from rs_siggen_mcp.models.siggen_types import InstrumentInfo, SignalGeneratorFamily
from rs_siggen_mcp.safety.validators import SafetyLimits


class TestRSSignalGeneratorDriverInit:
    """Test driver initialization."""

    def test_default_init(self):
        """Test default initialization."""
        driver = RSSignalGeneratorDriver()
        assert driver.is_connected is False
        assert driver.info is None
        assert driver.family == SignalGeneratorFamily.UNKNOWN

    def test_custom_init(self):
        """Test custom initialization."""
        limits = SafetyLimits(max_power_dbm=10.0)
        driver = RSSignalGeneratorDriver(
            host="10.0.0.1",
            port=5025,
            timeout=10.0,
            command_timeout=60.0,
            safety_limits=limits,
        )
        assert driver.address == "10.0.0.1:5025"


class TestRSSignalGeneratorDriverConnect:
    """Test driver connection and identification."""

    @pytest.mark.asyncio
    async def test_connect(self, mock_driver, mock_scpi_socket):
        """Test successful connection."""
        assert mock_driver.is_connected is True
        assert mock_driver.info is not None
        assert mock_driver.info.model == "SMW200A"

    @pytest.mark.asyncio
    async def test_identify(self, mock_driver, mock_scpi_socket):
        """Test instrument identification."""
        mock_scpi_socket.query.return_value = (
            "Rohde&Schwarz,SMBV100B,1420.7508K02/100001,5.00.042.00"
        )
        info = await mock_driver.identify()
        assert info.model == "SMBV100B"
        assert info.family == SignalGeneratorFamily.SMBV100B
        mock_scpi_socket.query.assert_called_with("*IDN?")


class TestRSSignalGeneratorDriverRF:
    """Test RF output control methods."""

    @pytest.mark.asyncio
    async def test_set_frequency(self, mock_driver, mock_scpi_socket):
        """Test setting frequency."""
        await mock_driver.set_frequency(1e9)
        mock_scpi_socket.send.assert_called_with("SOURce1:FREQuency:CW 1000000000.0")

    @pytest.mark.asyncio
    async def test_get_frequency(self, mock_driver, mock_scpi_socket):
        """Test getting frequency."""
        mock_scpi_socket.query.return_value = "1000000000"
        freq = await mock_driver.get_frequency()
        assert freq == 1e9
        mock_scpi_socket.query.assert_called_with("SOURce1:FREQuency:CW?")

    @pytest.mark.asyncio
    async def test_set_power(self, mock_driver, mock_scpi_socket):
        """Test setting power."""
        await mock_driver.set_power(-10.0)
        mock_scpi_socket.send.assert_called_with(
            "SOURce1:POWer:LEVel:IMMediate:AMPLitude -10.0"
        )

    @pytest.mark.asyncio
    async def test_get_power(self, mock_driver, mock_scpi_socket):
        """Test getting power."""
        mock_scpi_socket.query.return_value = "-10.0"
        power = await mock_driver.get_power()
        assert power == -10.0

    @pytest.mark.asyncio
    async def test_output_on(self, mock_driver, mock_scpi_socket):
        """Test enabling RF output."""
        await mock_driver.output_on()
        mock_scpi_socket.send.assert_called_with("OUTPut1:STATe ON")
        assert mock_driver._rf_output_on is True

    @pytest.mark.asyncio
    async def test_output_off(self, mock_driver, mock_scpi_socket):
        """Test disabling RF output."""
        await mock_driver.output_off()
        mock_scpi_socket.send.assert_called_with("OUTPut1:STATe OFF")
        assert mock_driver._rf_output_on is False

    @pytest.mark.asyncio
    async def test_get_output_state(self, mock_driver, mock_scpi_socket):
        """Test querying output state."""
        mock_scpi_socket.query.return_value = "1"
        state = await mock_driver.get_output_state()
        assert state is True

        mock_scpi_socket.query.return_value = "0"
        state = await mock_driver.get_output_state()
        assert state is False

    @pytest.mark.asyncio
    async def test_set_phase(self, mock_driver, mock_scpi_socket):
        """Test setting phase."""
        await mock_driver.set_phase(90.0)
        mock_scpi_socket.send.assert_called_with("SOURce1:PHASe 90.0")


class TestRSSignalGeneratorDriverModulation:
    """Test modulation control methods."""

    @pytest.mark.asyncio
    async def test_configure_am(self, mock_driver, mock_scpi_socket):
        """Test AM configuration."""
        await mock_driver.configure_am(80.0, enable=True)
        calls = [str(c) for c in mock_scpi_socket.send.call_args_list]
        assert any("AM:DEPTh 80.0" in c for c in calls)
        assert any("AM:STATe ON" in c for c in calls)

    @pytest.mark.asyncio
    async def test_configure_fm(self, mock_driver, mock_scpi_socket):
        """Test FM configuration."""
        await mock_driver.configure_fm(75e3, enable=True)
        calls = [str(c) for c in mock_scpi_socket.send.call_args_list]
        assert any("FM:DEViation 75000.0" in c for c in calls)
        assert any("FM:STATe ON" in c for c in calls)

    @pytest.mark.asyncio
    async def test_configure_pm(self, mock_driver, mock_scpi_socket):
        """Test PM configuration."""
        await mock_driver.configure_pm(1.5, enable=True)
        calls = [str(c) for c in mock_scpi_socket.send.call_args_list]
        assert any("PM:DEViation 1.5" in c for c in calls)
        assert any("PM:STATe ON" in c for c in calls)

    @pytest.mark.asyncio
    async def test_configure_pm_negative_deviation(self, mock_driver, mock_scpi_socket):
        """Test PM with negative deviation raises error."""
        with pytest.raises(ValueError):
            await mock_driver.configure_pm(-1.0)

    @pytest.mark.asyncio
    async def test_configure_pulse(self, mock_driver, mock_scpi_socket):
        """Test pulse modulation configuration."""
        await mock_driver.configure_pulse(1e-6, period_s=10e-6, enable=True)
        calls = [str(c) for c in mock_scpi_socket.send.call_args_list]
        assert any("PULM:WIDTh" in c for c in calls)
        assert any("PULM:PERiod" in c for c in calls)
        assert any("PULM:STATe ON" in c for c in calls)

    @pytest.mark.asyncio
    async def test_modulation_all_off(self, mock_driver, mock_scpi_socket):
        """Test turning off all modulations."""
        await mock_driver.modulation_all_off()
        mock_scpi_socket.send.assert_called_with("SOURce:MODulation:ALL:STATe OFF")


class TestRSSignalGeneratorDriverIQ:
    """Test IQ modulation methods."""

    @pytest.mark.asyncio
    async def test_iq_on(self, mock_driver, mock_scpi_socket):
        """Test enabling IQ modulation."""
        await mock_driver.iq_on()
        mock_scpi_socket.send.assert_called_with("SOURce:IQ:STATe ON")

    @pytest.mark.asyncio
    async def test_iq_off(self, mock_driver, mock_scpi_socket):
        """Test disabling IQ modulation."""
        await mock_driver.iq_off()
        mock_scpi_socket.send.assert_called_with("SOURce:IQ:STATe OFF")

    @pytest.mark.asyncio
    async def test_iq_on_cw_only(self, mock_driver, mock_scpi_socket):
        """Test IQ on CW-only instrument raises error."""
        mock_driver._info = InstrumentInfo(
            manufacturer="Rohde&Schwarz",
            model="SGS100A",
            serial="123",
            firmware="4.0",
            family=SignalGeneratorFamily.SGS100A,
        )
        with pytest.raises(ConfigurationError):
            await mock_driver.iq_on()


class TestRSSignalGeneratorDriverARB:
    """Test ARB waveform methods."""

    @pytest.mark.asyncio
    async def test_arb_on(self, mock_driver, mock_scpi_socket):
        """Test enabling ARB generator."""
        await mock_driver.arb_on()
        mock_scpi_socket.send.assert_called_with("SOURce1:BB:ARBitrary:STATe ON")

    @pytest.mark.asyncio
    async def test_arb_off(self, mock_driver, mock_scpi_socket):
        """Test disabling ARB generator."""
        await mock_driver.arb_off()
        mock_scpi_socket.send.assert_called_with("SOURce1:BB:ARBitrary:STATe OFF")

    @pytest.mark.asyncio
    async def test_load_waveform(self, mock_driver, mock_scpi_socket):
        """Test loading waveform."""
        await mock_driver.load_waveform("/var/user/waveform/test.wv")
        calls = [str(c) for c in mock_scpi_socket.send.call_args_list]
        assert any("WAVeform:SELect" in c for c in calls)

    @pytest.mark.asyncio
    async def test_arb_on_unsupported(self, mock_driver, mock_scpi_socket):
        """Test ARB on unsupported instrument."""
        mock_driver._info = InstrumentInfo(
            manufacturer="Rohde&Schwarz",
            model="SGS100A",
            serial="123",
            firmware="4.0",
            family=SignalGeneratorFamily.SGS100A,
        )
        with pytest.raises(ConfigurationError):
            await mock_driver.arb_on()


class TestRSSignalGeneratorDriverReference:
    """Test reference oscillator methods."""

    @pytest.mark.asyncio
    async def test_set_reference_internal(self, mock_driver, mock_scpi_socket):
        """Test setting internal reference."""
        await mock_driver.set_reference_source("INTernal")
        mock_scpi_socket.send.assert_called_with("SOURce1:ROSCillator:SOURce INTernal")

    @pytest.mark.asyncio
    async def test_set_reference_external(self, mock_driver, mock_scpi_socket):
        """Test setting external reference."""
        await mock_driver.set_reference_source("EXTernal")
        mock_scpi_socket.send.assert_called_with("SOURce1:ROSCillator:SOURce EXTernal")

    @pytest.mark.asyncio
    async def test_set_reference_invalid(self, mock_driver, mock_scpi_socket):
        """Test setting invalid reference source."""
        with pytest.raises(ValueError):
            await mock_driver.set_reference_source("INVALID")


class TestRSSignalGeneratorDriverReset:
    """Test reset and preset methods."""

    @pytest.mark.asyncio
    async def test_reset(self, mock_driver, mock_scpi_socket):
        """Test instrument reset."""
        mock_driver._rf_output_on = True
        mock_driver._frequency_hz = 1e9
        await mock_driver.reset()
        mock_scpi_socket.send.assert_called_with("*RST")
        assert mock_driver._rf_output_on is False
        assert mock_driver._frequency_hz is None

    @pytest.mark.asyncio
    async def test_preset(self, mock_driver, mock_scpi_socket):
        """Test instrument preset."""
        await mock_driver.preset()
        mock_scpi_socket.send.assert_called_with("SYSTem:PRESet")

    @pytest.mark.asyncio
    async def test_get_errors_no_errors(self, mock_driver, mock_scpi_socket):
        """Test querying errors when none exist."""
        mock_scpi_socket.query.return_value = '0,"No error"'
        errors = await mock_driver.get_errors()
        assert errors == []

    @pytest.mark.asyncio
    async def test_get_errors_with_errors(self, mock_driver, mock_scpi_socket):
        """Test querying errors when errors exist."""
        mock_scpi_socket.query.side_effect = [
            '-100,"Command error"',
            '0,"No error"',
        ]
        errors = await mock_driver.get_errors()
        assert len(errors) == 1
        assert "-100" in errors[0]


class TestRSSignalGeneratorDriverStatus:
    """Test status methods."""

    def test_get_status_connected(self, mock_driver):
        """Test status when connected."""
        mock_driver._frequency_hz = 1e9
        mock_driver._power_dbm = -10.0
        status = mock_driver.get_status()
        assert status["connected"] is True
        assert status["frequency_hz"] == 1e9
        assert status["power_dbm"] == -10.0
        assert "instrument" in status

    def test_get_status_minimal(self, mock_driver):
        """Test status with minimal info."""
        mock_driver._info = None
        mock_driver._frequency_hz = None
        mock_driver._power_dbm = None
        status = mock_driver.get_status()
        assert status["connected"] is True
        assert "frequency_hz" not in status


class TestRSSignalGeneratorDriverSCPI:
    """Test raw SCPI access."""

    @pytest.mark.asyncio
    async def test_scpi_send(self, mock_driver, mock_scpi_socket):
        """Test raw SCPI send."""
        await mock_driver.scpi_send("*RST")
        mock_scpi_socket.send.assert_called_with("*RST")

    @pytest.mark.asyncio
    async def test_scpi_query(self, mock_driver, mock_scpi_socket):
        """Test raw SCPI query."""
        mock_scpi_socket.query.return_value = "1000000000"
        response = await mock_driver.scpi_query("SOURce1:FREQuency:CW?")
        assert response == "1000000000"
