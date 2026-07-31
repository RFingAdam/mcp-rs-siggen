"""Instrument state management for signal generator configuration persistence."""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from scpi_core import Idempotency

if TYPE_CHECKING:
    from .driver.siggen_driver import RSSignalGeneratorDriver

logger = logging.getLogger(__name__)


@dataclass
class RFState:
    """State of RF output configuration."""

    frequency_hz: float
    power_dbm: float
    output_enabled: bool = False
    phase_deg: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "frequency_hz": self.frequency_hz,
            "power_dbm": self.power_dbm,
            "output_enabled": self.output_enabled,
            "phase_deg": self.phase_deg,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RFState":
        """Create from dictionary."""
        return cls(
            frequency_hz=data["frequency_hz"],
            power_dbm=data["power_dbm"],
            output_enabled=data.get("output_enabled", False),
            phase_deg=data.get("phase_deg", 0.0),
        )


@dataclass
class ModulationState:
    """State of modulation configuration."""

    am_enabled: bool = False
    am_depth_percent: float | None = None
    fm_enabled: bool = False
    fm_deviation_hz: float | None = None
    pm_enabled: bool = False
    pm_deviation_rad: float | None = None
    pulse_enabled: bool = False
    pulse_width_s: float | None = None
    pulse_period_s: float | None = None
    iq_enabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "am_enabled": self.am_enabled,
            "am_depth_percent": self.am_depth_percent,
            "fm_enabled": self.fm_enabled,
            "fm_deviation_hz": self.fm_deviation_hz,
            "pm_enabled": self.pm_enabled,
            "pm_deviation_rad": self.pm_deviation_rad,
            "pulse_enabled": self.pulse_enabled,
            "pulse_width_s": self.pulse_width_s,
            "pulse_period_s": self.pulse_period_s,
            "iq_enabled": self.iq_enabled,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModulationState":
        """Create from dictionary."""
        return cls(
            am_enabled=data.get("am_enabled", False),
            am_depth_percent=data.get("am_depth_percent"),
            fm_enabled=data.get("fm_enabled", False),
            fm_deviation_hz=data.get("fm_deviation_hz"),
            pm_enabled=data.get("pm_enabled", False),
            pm_deviation_rad=data.get("pm_deviation_rad"),
            pulse_enabled=data.get("pulse_enabled", False),
            pulse_width_s=data.get("pulse_width_s"),
            pulse_period_s=data.get("pulse_period_s"),
            iq_enabled=data.get("iq_enabled", False),
        )


@dataclass
class InstrumentState:
    """
    Complete signal generator configuration state.

    Captures all relevant settings that can be saved and restored,
    enabling reproducible signal generation configurations.

    Attributes:
        rf: RF output state (frequency, power, etc.)
        modulation: Modulation state (AM, FM, PM, pulse, IQ)
        reference_source: Reference oscillator source
        timestamp: When this state was captured
        instrument_info: Instrument identification info
        notes: Optional user notes
    """

    rf: RFState
    modulation: ModulationState
    reference_source: str = "INTernal"
    timestamp: datetime = field(default_factory=datetime.now)
    instrument_info: dict[str, str] = field(default_factory=dict)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        """
        Convert state to dictionary for serialization.

        Returns:
            Dictionary representation of the state
        """
        return {
            "rf": self.rf.to_dict(),
            "modulation": self.modulation.to_dict(),
            "reference_source": self.reference_source,
            "timestamp": self.timestamp.isoformat(),
            "instrument_info": self.instrument_info,
            "notes": self.notes,
            "version": "1.0",
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InstrumentState":
        """
        Create state from dictionary.

        Args:
            data: Dictionary representation of state

        Returns:
            InstrumentState instance
        """
        rf = RFState.from_dict(data["rf"])
        modulation = ModulationState.from_dict(data.get("modulation", {}))

        timestamp = datetime.now()
        if data.get("timestamp"):
            try:
                timestamp = datetime.fromisoformat(data["timestamp"])
            except ValueError:
                pass

        return cls(
            rf=rf,
            modulation=modulation,
            reference_source=data.get("reference_source", "INTernal"),
            timestamp=timestamp,
            instrument_info=data.get("instrument_info", {}),
            notes=data.get("notes", ""),
        )

    def save(self, filepath: str | Path) -> None:
        """
        Save state to JSON file.

        Args:
            filepath: Path to save the state file

        Raises:
            IOError: If file cannot be written
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filepath: str | Path) -> "InstrumentState":
        """
        Load state from JSON file.

        Args:
            filepath: Path to the state file

        Returns:
            Loaded InstrumentState instance

        Raises:
            FileNotFoundError: If file does not exist
            json.JSONDecodeError: If file is not valid JSON
            KeyError: If required fields are missing
        """
        filepath = Path(filepath)

        with open(filepath) as f:
            data = json.load(f)

        return cls.from_dict(data)

    def get_summary(self) -> dict[str, Any]:
        """
        Get a summary of the state.

        Returns:
            Dictionary with key state information
        """
        return {
            "timestamp": self.timestamp.isoformat(),
            "frequency_hz": self.rf.frequency_hz,
            "power_dbm": self.rf.power_dbm,
            "output_enabled": self.rf.output_enabled,
            "modulation": {
                "am": self.modulation.am_enabled,
                "fm": self.modulation.fm_enabled,
                "pm": self.modulation.pm_enabled,
                "pulse": self.modulation.pulse_enabled,
                "iq": self.modulation.iq_enabled,
            },
            "reference_source": self.reference_source,
            "instrument": self.instrument_info.get("model", "Unknown"),
        }


class StateManager:
    """
    Manages signal generator state capture and restoration.

    Provides methods to capture current state, save/load state files,
    and restore state to instrument.
    """

    def __init__(self, state_directory: str | Path | None = None):
        """
        Initialize state manager.

        Args:
            state_directory: Directory for state files (default: ./siggen_states)
        """
        if state_directory is None:
            state_directory = Path("./siggen_states")
        self.state_directory = Path(state_directory)

    async def capture_state(self, driver: "RSSignalGeneratorDriver") -> InstrumentState:
        """
        Capture current signal generator state.

        Args:
            driver: RSSignalGeneratorDriver instance

        Returns:
            Captured InstrumentState
        """
        # Query current RF settings
        freq = await driver.scpi_query(
            "SOURce1:FREQuency:CW?", idempotency=Idempotency.QUERY
        )
        power = await driver.scpi_query("SOURce1:POWer?", idempotency=Idempotency.QUERY)
        output = await driver.scpi_query(
            "OUTPut1:STATe?", idempotency=Idempotency.QUERY
        )

        rf = RFState(
            frequency_hz=float(freq),
            power_dbm=float(power),
            output_enabled=output.strip() in ("1", "ON"),
        )

        # Query modulation states
        mod = ModulationState()
        try:
            am_state = await driver.scpi_query(
                "SOURce1:AM:STATe?", idempotency=Idempotency.QUERY
            )
            mod.am_enabled = am_state.strip() in ("1", "ON")
            if mod.am_enabled:
                am_depth = await driver.scpi_query(
                    "SOURce1:AM:DEPTh?", idempotency=Idempotency.QUERY
                )
                mod.am_depth_percent = float(am_depth)
        except (OSError, ValueError) as e:
            logger.debug("Could not query AM state: %s", e)

        try:
            fm_state = await driver.scpi_query(
                "SOURce1:FM:STATe?", idempotency=Idempotency.QUERY
            )
            mod.fm_enabled = fm_state.strip() in ("1", "ON")
            if mod.fm_enabled:
                fm_dev = await driver.scpi_query(
                    "SOURce1:FM:DEViation?", idempotency=Idempotency.QUERY
                )
                mod.fm_deviation_hz = float(fm_dev)
        except (OSError, ValueError) as e:
            logger.debug("Could not query FM state: %s", e)

        try:
            pm_state = await driver.scpi_query(
                "SOURce1:PM:STATe?", idempotency=Idempotency.QUERY
            )
            mod.pm_enabled = pm_state.strip() in ("1", "ON")
            if mod.pm_enabled:
                pm_dev = await driver.scpi_query(
                    "SOURce1:PM:DEViation?", idempotency=Idempotency.QUERY
                )
                mod.pm_deviation_rad = float(pm_dev)
        except (OSError, ValueError) as e:
            logger.debug("Could not query PM state: %s", e)

        try:
            pulse_state = await driver.scpi_query(
                "SOURce1:PULM:STATe?", idempotency=Idempotency.QUERY
            )
            mod.pulse_enabled = pulse_state.strip() in ("1", "ON")
            if mod.pulse_enabled:
                pulse_w = await driver.scpi_query(
                    "SOURce1:PULM:WIDTh?", idempotency=Idempotency.QUERY
                )
                mod.pulse_width_s = float(pulse_w)
                pulse_p = await driver.scpi_query(
                    "SOURce1:PULM:PERiod?", idempotency=Idempotency.QUERY
                )
                mod.pulse_period_s = float(pulse_p)
        except (OSError, ValueError) as e:
            logger.debug("Could not query pulse state: %s", e)

        try:
            iq_state = await driver.scpi_query(
                "SOURce:IQ:STATe?", idempotency=Idempotency.QUERY
            )
            mod.iq_enabled = iq_state.strip() in ("1", "ON")
        except (OSError, ValueError) as e:
            logger.debug("Could not query IQ state: %s", e)

        # Query reference source
        try:
            ref = await driver.scpi_query(
                "SOURce1:ROSCillator:SOURce?", idempotency=Idempotency.QUERY
            )
            reference_source = ref.strip()
        except (OSError, ValueError) as e:
            logger.debug("Could not query reference source: %s", e)
            reference_source = "INTernal"

        # Get instrument info
        instrument_info = {}
        if driver.info:
            instrument_info = driver.info.to_dict()

        return InstrumentState(
            rf=rf,
            modulation=mod,
            reference_source=reference_source,
            instrument_info=instrument_info,
        )

    async def restore_state(
        self, driver: "RSSignalGeneratorDriver", state: InstrumentState
    ) -> None:
        """
        Restore signal generator to saved state.

        Args:
            driver: RSSignalGeneratorDriver instance
            state: State to restore
        """
        # Restore RF configuration
        await driver.set_frequency(state.rf.frequency_hz)
        await driver.set_power(state.rf.power_dbm)

        if state.rf.phase_deg != 0.0:
            await driver.set_phase(state.rf.phase_deg)

        # Restore modulation states
        if state.modulation.am_enabled and state.modulation.am_depth_percent is not None:
            await driver.configure_am(state.modulation.am_depth_percent, enable=True)
        else:
            await driver.scpi_send(
                "SOURce1:AM:STATe OFF", idempotency=Idempotency.SETTING
            )

        if state.modulation.fm_enabled and state.modulation.fm_deviation_hz is not None:
            await driver.configure_fm(state.modulation.fm_deviation_hz, enable=True)
        else:
            await driver.scpi_send(
                "SOURce1:FM:STATe OFF", idempotency=Idempotency.SETTING
            )

        if state.modulation.pm_enabled and state.modulation.pm_deviation_rad is not None:
            await driver.configure_pm(state.modulation.pm_deviation_rad, enable=True)
        else:
            await driver.scpi_send(
                "SOURce1:PM:STATe OFF", idempotency=Idempotency.SETTING
            )

        if state.modulation.pulse_enabled and state.modulation.pulse_width_s is not None:
            await driver.configure_pulse(
                state.modulation.pulse_width_s,
                state.modulation.pulse_period_s,
                enable=True,
            )
        else:
            await driver.scpi_send(
                "SOURce1:PULM:STATe OFF", idempotency=Idempotency.SETTING
            )

        if state.modulation.iq_enabled:
            await driver.iq_on()
        else:
            await driver.scpi_send(
                "SOURce:IQ:STATe OFF", idempotency=Idempotency.SETTING
            )

        # Restore reference source
        await driver.set_reference_source(state.reference_source)

        # Restore RF output state last for safety
        if state.rf.output_enabled:
            await driver.output_on()
        else:
            await driver.output_off()

    def list_saved_states(self) -> list[dict[str, Any]]:
        """
        List all saved state files.

        Returns:
            List of dictionaries with filename and summary info
        """
        states: list[dict[str, Any]] = []
        if not self.state_directory.exists():
            return states

        for filepath in self.state_directory.glob("*.json"):
            try:
                state = InstrumentState.load(filepath)
                states.append({
                    "filename": filepath.name,
                    "path": str(filepath),
                    "summary": state.get_summary(),
                })
            except (json.JSONDecodeError, KeyError, ValueError, OSError) as e:
                logger.warning("Failed to load state file %s: %s", filepath, e)
                states.append({
                    "filename": filepath.name,
                    "path": str(filepath),
                    "error": str(e),
                })

        return states
