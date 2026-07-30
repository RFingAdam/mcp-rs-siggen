"""High-level driver for R&S signal generators.

The transport comes from :func:`scpi_core.transport.factory.create_transport`
rather than a socket class owned by this package. That swap is a correctness fix,
not tidying: the transport this driver used to carry took its lock separately for
the send and the read of a query, so two concurrent tool calls could each receive
the other's answer, and it had no notion of desync -- after one read timeout every
later query returned the *previous* query's response, forever, with no error.

Every call below therefore states an :class:`~scpi_core.Idempotency`. It decides
whether the transport may re-send after a failure, and getting it wrong is not a
style question: re-sending ``OUTPut1:STATe ON`` is harmless, but re-sending a
``*RST`` or a calibration wipes work the caller already did. Value assignments are
SETTING (re-assigning the same value is a no-op), reads are QUERY, and anything
that transitions state -- reset, preset, RF output, calibration -- is ACTION and is
never retried.
"""

import logging
from typing import Any

from scpi_core import Idempotency, SCPITransport
from scpi_core.transport.factory import create_transport

from ..exceptions import ConfigurationError
from ..models.siggen_types import InstrumentInfo, SignalGeneratorFamily
from ..safety.validators import SafetyLimits, SafetyValidator, sanitize_scpi_param

logger = logging.getLogger(__name__)


class RSSignalGeneratorDriver:
    """
    High-level async driver for Rohde & Schwarz signal generators.

    Provides validated, instrument-aware access to signal generator functions
    via SCPI over TCP/IP.

    Supported models: SMW200A, SMBV100B, SMM100A, SMCV100B, SGT100A, SGS100A,
    SMA100B, SMB100B.

    Example:
        driver = RSSignalGeneratorDriver(host="192.168.1.100")
        await driver.connect()
        await driver.set_frequency(1e9)
        await driver.set_power(-10)
        await driver.output_on()
    """

    def __init__(
        self,
        host: str = "192.168.1.100",
        port: int = 5025,
        timeout: float = 5.0,
        command_timeout: float = 30.0,
        safety_limits: SafetyLimits | None = None,
    ):
        """
        Initialize signal generator driver.

        Args:
            host: Instrument IP address
            port: SCPI TCP port (default 5025)
            timeout: Connection timeout
            command_timeout: Command timeout
            safety_limits: Safety limits for validation
        """
        self._scpi: SCPITransport = create_transport(
            host=host,
            port=port,
            timeout=timeout,
            command_timeout=command_timeout,
        )
        self._safety = SafetyValidator(safety_limits)
        self._info: InstrumentInfo | None = None
        self._rf_output_on = False
        self._frequency_hz: float | None = None
        self._power_dbm: float | None = None

    @property
    def is_connected(self) -> bool:
        """Check if connected to signal generator."""
        return self._scpi.is_connected

    @property
    def address(self) -> str:
        """Get connection address."""
        return self._scpi.address

    @property
    def info(self) -> InstrumentInfo | None:
        """Get instrument info (available after connect)."""
        return self._info

    @property
    def family(self) -> SignalGeneratorFamily:
        """Get instrument family."""
        if self._info:
            return self._info.family
        return SignalGeneratorFamily.UNKNOWN

    async def connect(self) -> InstrumentInfo:
        """
        Connect to signal generator and identify it.

        Returns:
            InstrumentInfo with instrument details

        Raises:
            ConnectionError: If connection fails
        """
        await self._scpi.connect()
        self._info = await self.identify()
        logger.info(
            f"Connected to {self._info.manufacturer} {self._info.model} "
            f"({self._info.family.value})"
        )
        return self._info

    async def disconnect(self) -> None:
        """Disconnect from signal generator."""
        # Turn off RF output for safety before disconnecting
        if self._rf_output_on:
            try:
                await self.output_off()
            except OSError as e:
                logger.warning("Failed to turn off RF output before disconnect: %s", e)
        await self._scpi.disconnect()

    async def identify(self) -> InstrumentInfo:
        """
        Query instrument identification.

        Returns:
            InstrumentInfo parsed from *IDN? response
        """
        idn = await self._scpi.query("*IDN?", idempotency=Idempotency.QUERY)
        info = InstrumentInfo.from_idn(idn)
        self._info = info
        return info

    async def reset(self) -> None:
        """Reset instrument to default state (*RST)."""
        await self._scpi.send("*RST", idempotency=Idempotency.ACTION)
        await self._scpi.wait_opc()
        self._rf_output_on = False
        self._frequency_hz = None
        self._power_dbm = None
        logger.info("Instrument reset")

    async def preset(self) -> None:
        """Preset instrument (SYSTem:PRESet)."""
        await self._scpi.send("SYSTem:PRESet", idempotency=Idempotency.ACTION)
        await self._scpi.wait_opc()
        self._rf_output_on = False
        self._frequency_hz = None
        self._power_dbm = None
        logger.info("Instrument preset")

    async def get_errors(self) -> list[str]:
        """
        Query and return all instrument errors.

        Returns:
            List of error strings. Empty list if no errors.
        """
        errors = []
        while True:
            response = await self._scpi.query(
                "SYSTem:ERRor?", idempotency=Idempotency.QUERY
            )
            # R&S format: <code>,\"<message>\"
            if response.startswith("0,") or response.startswith("+0,"):
                break
            errors.append(response)
        return errors

    # =========================================================================
    # RF Output Control
    # =========================================================================

    async def set_frequency(self, frequency_hz: float) -> None:
        """
        Set CW output frequency.

        Args:
            frequency_hz: Frequency in Hz

        Raises:
            SafetyError: If frequency exceeds limits
        """
        self._safety.validate_frequency(frequency_hz)
        await self._scpi.send(
            f"SOURce1:FREQuency:CW {frequency_hz}", idempotency=Idempotency.SETTING
        )
        self._frequency_hz = frequency_hz
        logger.info(f"Frequency set to {frequency_hz/1e6:.6f} MHz")

    async def get_frequency(self) -> float:
        """
        Query current CW frequency.

        Returns:
            Frequency in Hz
        """
        response = await self._scpi.query(
            "SOURce1:FREQuency:CW?", idempotency=Idempotency.QUERY
        )
        freq = float(response)
        self._frequency_hz = freq
        return freq

    async def set_power(self, power_dbm: float) -> None:
        """
        Set output power level.

        Args:
            power_dbm: Power level in dBm

        Raises:
            SafetyError: If power exceeds limits
        """
        self._safety.validate_power(power_dbm)
        await self._scpi.send(
            f"SOURce1:POWer:LEVel:IMMediate:AMPLitude {power_dbm}",
            idempotency=Idempotency.SETTING,
        )
        self._power_dbm = power_dbm
        logger.info(f"Power set to {power_dbm} dBm")

    async def get_power(self) -> float:
        """
        Query current output power.

        Returns:
            Power in dBm
        """
        response = await self._scpi.query("SOURce1:POWer?", idempotency=Idempotency.QUERY)
        power = float(response)
        self._power_dbm = power
        return power

    async def output_on(self) -> None:
        """Enable RF output.

        ACTION, not SETTING: a retry after a transport hiccup could energise the
        output a second time when the caller has already been told the first
        attempt failed. Nothing may radiate on a guess.
        """
        await self._scpi.send("OUTPut1:STATe ON", idempotency=Idempotency.ACTION)
        self._rf_output_on = True
        logger.info("RF output ON")

    async def output_off(self) -> None:
        """Disable RF output (safe state)."""
        await self._scpi.send("OUTPut1:STATe OFF", idempotency=Idempotency.ACTION)
        self._rf_output_on = False
        logger.info("RF output OFF")

    async def get_output_state(self) -> bool:
        """
        Query RF output state.

        Returns:
            True if output is enabled
        """
        response = await self._scpi.query("OUTPut1:STATe?", idempotency=Idempotency.QUERY)
        state = response.strip() in ("1", "ON")
        self._rf_output_on = state
        return state

    async def set_phase(self, phase_deg: float) -> None:
        """
        Set RF phase offset.

        Args:
            phase_deg: Phase in degrees
        """
        await self._scpi.send(
            f"SOURce1:PHASe {phase_deg}", idempotency=Idempotency.SETTING
        )
        logger.info(f"Phase set to {phase_deg} deg")

    # =========================================================================
    # Analog Modulation
    # =========================================================================

    async def configure_am(self, depth_percent: float, enable: bool = True) -> None:
        """
        Configure amplitude modulation.

        Args:
            depth_percent: Modulation depth in percent (0-100)
            enable: Enable AM modulation
        """
        self._safety.validate_modulation_depth(depth_percent)
        await self._scpi.send(
            f"SOURce1:AM:DEPTh {depth_percent}", idempotency=Idempotency.SETTING
        )
        await self._scpi.send(
            f"SOURce1:AM:STATe {'ON' if enable else 'OFF'}",
            idempotency=Idempotency.SETTING,
        )
        logger.info(f"AM: depth={depth_percent}%, enabled={enable}")

    async def configure_fm(self, deviation_hz: float, enable: bool = True) -> None:
        """
        Configure frequency modulation.

        Args:
            deviation_hz: FM deviation in Hz
            enable: Enable FM modulation
        """
        self._safety.validate_deviation(deviation_hz)
        await self._scpi.send(
            f"SOURce1:FM:DEViation {deviation_hz}", idempotency=Idempotency.SETTING
        )
        await self._scpi.send(
            f"SOURce1:FM:STATe {'ON' if enable else 'OFF'}",
            idempotency=Idempotency.SETTING,
        )
        logger.info(f"FM: deviation={deviation_hz/1e3:.3f} kHz, enabled={enable}")

    async def configure_pm(self, deviation_rad: float, enable: bool = True) -> None:
        """
        Configure phase modulation.

        Args:
            deviation_rad: PM deviation in radians
            enable: Enable PM modulation
        """
        if deviation_rad < 0:
            raise ValueError(f"PM deviation {deviation_rad} rad must be positive")
        await self._scpi.send(
            f"SOURce1:PM:DEViation {deviation_rad}", idempotency=Idempotency.SETTING
        )
        await self._scpi.send(
            f"SOURce1:PM:STATe {'ON' if enable else 'OFF'}",
            idempotency=Idempotency.SETTING,
        )
        logger.info(f"PM: deviation={deviation_rad} rad, enabled={enable}")

    async def configure_pulse(
        self,
        width_s: float,
        period_s: float | None = None,
        enable: bool = True,
    ) -> None:
        """
        Configure pulse modulation.

        Args:
            width_s: Pulse width in seconds
            period_s: Pulse period in seconds
            enable: Enable pulse modulation
        """
        self._safety.validate_pulse_width(width_s, period_s)
        await self._scpi.send(
            f"SOURce1:PULM:WIDTh {width_s}", idempotency=Idempotency.SETTING
        )
        if period_s is not None:
            await self._scpi.send(
                f"SOURce1:PULM:PERiod {period_s}", idempotency=Idempotency.SETTING
            )
        await self._scpi.send(
            f"SOURce1:PULM:STATe {'ON' if enable else 'OFF'}",
            idempotency=Idempotency.SETTING,
        )
        logger.info(f"Pulse: width={width_s*1e6:.1f} us, enabled={enable}")

    async def modulation_all_off(self) -> None:
        """Turn off all modulations."""
        await self._scpi.send(
            "SOURce:MODulation:ALL:STATe OFF", idempotency=Idempotency.SETTING
        )
        logger.info("All modulations OFF")

    # =========================================================================
    # IQ Modulation
    # =========================================================================

    async def iq_on(self) -> None:
        """Enable IQ modulation."""
        if self._info and not self._info.family.has_iq_modulation:
            raise ConfigurationError(
                f"{self._info.model} does not support IQ modulation",
                self.address,
            )
        await self._scpi.send("SOURce:IQ:STATe ON", idempotency=Idempotency.SETTING)
        logger.info("IQ modulation ON")

    async def iq_off(self) -> None:
        """Disable IQ modulation."""
        await self._scpi.send("SOURce:IQ:STATe OFF", idempotency=Idempotency.SETTING)
        logger.info("IQ modulation OFF")

    # =========================================================================
    # ARB Waveform Generator
    # =========================================================================

    async def load_waveform(self, waveform_path: str) -> None:
        """
        Load ARB waveform file.

        Args:
            waveform_path: Path to waveform file on the instrument
        """
        if self._info and not self._info.family.has_arb_generator:
            raise ConfigurationError(
                f"{self._info.model} does not have an ARB generator",
                self.address,
            )
        sanitize_scpi_param(waveform_path)
        await self._scpi.send(
            f"SOURce1:BB:ARBitrary:WAVeform:SELect '{waveform_path}'",
            idempotency=Idempotency.SETTING,
        )
        await self._scpi.wait_opc()
        logger.info(f"Waveform loaded: {waveform_path}")

    async def arb_on(self) -> None:
        """Enable ARB generator."""
        if self._info and not self._info.family.has_arb_generator:
            raise ConfigurationError(
                f"{self._info.model} does not have an ARB generator",
                self.address,
            )
        await self._scpi.send(
            "SOURce1:BB:ARBitrary:STATe ON", idempotency=Idempotency.SETTING
        )
        logger.info("ARB generator ON")

    async def arb_off(self) -> None:
        """Disable ARB generator."""
        await self._scpi.send(
            "SOURce1:BB:ARBitrary:STATe OFF", idempotency=Idempotency.SETTING
        )
        logger.info("ARB generator OFF")

    # =========================================================================
    # Reference Oscillator
    # =========================================================================

    async def set_reference_source(self, source: str) -> None:
        """
        Set reference oscillator source.

        Args:
            source: "INTernal" or "EXTernal"
        """
        source_upper = source.upper()
        if source_upper not in ("INTERNAL", "EXTERNAL", "INT", "EXT"):
            raise ValueError(f"Invalid reference source: {source}. Use INTernal or EXTernal.")
        # Normalize to R&S format
        if source_upper in ("INT", "INTERNAL"):
            scpi_val = "INTernal"
        else:
            scpi_val = "EXTernal"
        await self._scpi.send(
            f"SOURce1:ROSCillator:SOURce {scpi_val}", idempotency=Idempotency.SETTING
        )
        logger.info(f"Reference source set to {scpi_val}")

    async def get_reference_source(self) -> str:
        """
        Query reference oscillator source.

        Returns:
            Reference source string
        """
        return await self._scpi.query(
            "SOURce1:ROSCillator:SOURce?", idempotency=Idempotency.QUERY
        )

    # =========================================================================
    # Calibration
    # =========================================================================

    async def run_calibration(self) -> str:
        """
        Run internal calibration.

        Returns:
            Calibration result string
        """
        # A query in form only. `CALibration:ALL?` *performs* the calibration and
        # reports its verdict, so a retry would run it a second time -- minutes of
        # instrument time and a second set of stored correction data. ACTION.
        result = await self._scpi.query(
            "CALibration:ALL?", timeout=120.0, idempotency=Idempotency.ACTION
        )
        logger.info(f"Calibration result: {result}")
        return result

    # =========================================================================
    # Raw SCPI Access
    # =========================================================================

    async def wait_opc(self, timeout: float | None = None) -> bool:
        """Wait for operation complete."""
        return await self._scpi.wait_opc(timeout)

    def validate_frequency_range(self, start_hz: float, stop_hz: float) -> None:
        """Validate a frequency range."""
        self._safety.validate_frequency_range(start_hz, stop_hz)

    def validate_frequency(self, frequency_hz: float) -> None:
        """Validate a single frequency value."""
        self._safety.validate_frequency(frequency_hz)

    def validate_power(self, power_dbm: float) -> None:
        """Validate power level."""
        self._safety.validate_power(power_dbm)

    async def scpi_send(
        self, command: str, idempotency: Idempotency = Idempotency.ACTION
    ) -> None:
        """
        Send raw SCPI command.

        Args:
            command: SCPI command string
            idempotency: Whether the transport may re-send this after a failure.
                Callers that know the verb pass its class; the default is ACTION
                because an unclassified command must not be duplicated.
        """
        await self._scpi.send(command, idempotency=idempotency)

    async def scpi_query(
        self, command: str, idempotency: Idempotency = Idempotency.QUERY
    ) -> str:
        """
        Send raw SCPI query and return response.

        Args:
            command: SCPI query string
            idempotency: Whether the transport may re-send this after a failure.
                Pass ACTION for a query that also acts, such as ``CALibration:ALL?``.

        Returns:
            Response string
        """
        return await self._scpi.query(command, idempotency=idempotency)

    # =========================================================================
    # Status
    # =========================================================================

    def get_status(self) -> dict[str, Any]:
        """
        Get instrument connection and configuration status.

        Returns:
            Dictionary with status information
        """
        status: dict[str, Any] = {
            "connected": self.is_connected,
            "address": self.address,
            "rf_output_on": self._rf_output_on,
        }

        if self._info:
            status["instrument"] = self._info.to_dict()

        if self._frequency_hz is not None:
            status["frequency_hz"] = self._frequency_hz

        if self._power_dbm is not None:
            status["power_dbm"] = self._power_dbm

        return status
