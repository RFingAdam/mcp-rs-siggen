"""Signal generator type definitions and enumerations."""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class SignalGeneratorFamily(Enum):
    """
    Rohde & Schwarz signal generator product families.

    Each family has different capabilities (max freq, IQ bandwidth, etc.).
    """

    SMW200A = "SMW200A"    # High-end, 67 GHz, 2 GHz IQ BW, MIMO
    SMBV100B = "SMBV100B"  # Mid-range, 6 GHz, 1 GHz IQ BW
    SMM100A = "SMM100A"    # Mid-range, 44 GHz
    SMCV100B = "SMCV100B"  # Mid-range, 7.125 GHz
    SGT100A = "SGT100A"    # Compact SGMA, 6 GHz
    SGS100A = "SGS100A"    # CW-only SGMA, 12.75 GHz
    SMA100B = "SMA100B"    # Analog, ultra-low phase noise, 67 GHz
    SMB100B = "SMB100B"    # Analog, microwave, 40 GHz
    UNKNOWN = "UNKNOWN"

    @property
    def max_frequency_hz(self) -> float:
        """Maximum frequency capability."""
        freq_map = {
            SignalGeneratorFamily.SMW200A: 67e9,
            SignalGeneratorFamily.SMBV100B: 6e9,
            SignalGeneratorFamily.SMM100A: 44e9,
            SignalGeneratorFamily.SMCV100B: 7.125e9,
            SignalGeneratorFamily.SGT100A: 6e9,
            SignalGeneratorFamily.SGS100A: 12.75e9,
            SignalGeneratorFamily.SMA100B: 67e9,
            SignalGeneratorFamily.SMB100B: 40e9,
            SignalGeneratorFamily.UNKNOWN: 67e9,
        }
        return freq_map.get(self, 67e9)

    @property
    def has_iq_modulation(self) -> bool:
        """Whether the instrument supports IQ modulation."""
        return self in (
            SignalGeneratorFamily.SMW200A,
            SignalGeneratorFamily.SMBV100B,
            SignalGeneratorFamily.SMM100A,
            SignalGeneratorFamily.SMCV100B,
            SignalGeneratorFamily.SGT100A,
        )

    @property
    def has_arb_generator(self) -> bool:
        """Whether the instrument has a built-in ARB generator."""
        return self in (
            SignalGeneratorFamily.SMW200A,
            SignalGeneratorFamily.SMBV100B,
            SignalGeneratorFamily.SMM100A,
            SignalGeneratorFamily.SMCV100B,
        )

    @property
    def has_digital_standards(self) -> bool:
        """Whether the instrument supports digital standard baseband generation."""
        return self in (
            SignalGeneratorFamily.SMW200A,
            SignalGeneratorFamily.SMBV100B,
            SignalGeneratorFamily.SMCV100B,
        )

    @property
    def iq_bandwidth_hz(self) -> float | None:
        """Maximum IQ modulation bandwidth."""
        bw_map = {
            SignalGeneratorFamily.SMW200A: 2e9,
            SignalGeneratorFamily.SMBV100B: 1e9,
            SignalGeneratorFamily.SMM100A: 1e9,
            SignalGeneratorFamily.SMCV100B: 500e6,
            SignalGeneratorFamily.SGT100A: 1e9,
        }
        return bw_map.get(self)


class ModulationType(Enum):
    """Modulation types supported by R&S signal generators."""

    AM = "AM"       # Amplitude modulation
    FM = "FM"       # Frequency modulation
    PM = "PM"       # Phase modulation
    PULSE = "PULM"  # Pulse modulation
    IQ = "IQ"       # IQ modulation


class DigitalStandard(Enum):
    """Digital communication standards for baseband generation."""

    LTE = "LTE"
    LTE_ADVANCED = "LTEA"
    NR5G = "NR5G"
    WLAN = "WLAN"
    BLUETOOTH = "BTO"
    WCDMA = "WCDMA"
    GSM = "GSM"
    CUSTOM_DIGITAL_MOD = "CDM"


@dataclass
class InstrumentInfo:
    """
    Signal generator identification information.

    Parsed from *IDN? response:
    Rohde&Schwarz,<model>,<serial>,<firmware>
    """

    manufacturer: str
    model: str
    serial: str
    firmware: str
    family: SignalGeneratorFamily = SignalGeneratorFamily.UNKNOWN

    @classmethod
    def from_idn(cls, idn_string: str) -> "InstrumentInfo":
        """
        Parse *IDN? response string.

        Args:
            idn_string: Response from *IDN? query

        Returns:
            InstrumentInfo instance

        Example:
            >>> InstrumentInfo.from_idn("Rohde&Schwarz,SMW200A,1412.0000K02/123456,4.30.047.29")
        """
        parts = [p.strip() for p in idn_string.split(",")]

        if len(parts) < 4:
            return cls(
                manufacturer=parts[0] if parts else "Unknown",
                model=parts[1] if len(parts) > 1 else "Unknown",
                serial=parts[2] if len(parts) > 2 else "Unknown",
                firmware=parts[3] if len(parts) > 3 else "Unknown",
                family=SignalGeneratorFamily.UNKNOWN,
            )

        manufacturer = parts[0]
        model = parts[1]
        serial = parts[2]
        firmware = parts[3]

        # Auto-detect family from model string
        family = SignalGeneratorFamily.UNKNOWN
        model_upper = model.upper()
        for fam in SignalGeneratorFamily:
            if fam.value != "UNKNOWN" and fam.value.upper() in model_upper:
                family = fam
                break

        return cls(
            manufacturer=manufacturer,
            model=model,
            serial=serial,
            firmware=firmware,
            family=family,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "manufacturer": self.manufacturer,
            "model": self.model,
            "serial": self.serial,
            "firmware": self.firmware,
            "family": self.family.value,
            "max_frequency_hz": self.family.max_frequency_hz,
            "has_iq_modulation": self.family.has_iq_modulation,
            "has_arb_generator": self.family.has_arb_generator,
            "has_digital_standards": self.family.has_digital_standards,
            "iq_bandwidth_hz": self.family.iq_bandwidth_hz,
        }


@dataclass
class RFConfig:
    """RF output configuration."""

    frequency_hz: float
    power_dbm: float
    output_enabled: bool = False
    phase_deg: float = 0.0
    reference_source: str = "INTernal"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "frequency_hz": self.frequency_hz,
            "power_dbm": self.power_dbm,
            "output_enabled": self.output_enabled,
            "phase_deg": self.phase_deg,
            "reference_source": self.reference_source,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RFConfig":
        """Create from dictionary."""
        return cls(
            frequency_hz=data["frequency_hz"],
            power_dbm=data["power_dbm"],
            output_enabled=data.get("output_enabled", False),
            phase_deg=data.get("phase_deg", 0.0),
            reference_source=data.get("reference_source", "INTernal"),
        )


@dataclass
class WaveformInfo:
    """ARB waveform information."""

    name: str
    path: str
    sample_rate_hz: float | None = None
    samples: int | None = None
    runtime_s: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "path": self.path,
            "sample_rate_hz": self.sample_rate_hz,
            "samples": self.samples,
            "runtime_s": self.runtime_s,
        }


@dataclass
class SweepConfig:
    """Frequency or power sweep configuration."""

    start: float
    stop: float
    step: float | None = None
    points: int | None = None
    dwell_time_s: float = 0.01

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "start": self.start,
            "stop": self.stop,
            "step": self.step,
            "points": self.points,
            "dwell_time_s": self.dwell_time_s,
        }


@dataclass
class ModulationConfig:
    """Modulation configuration."""

    mod_type: str  # AM, FM, PM, PULSE, IQ
    enabled: bool = False
    depth_percent: float | None = None  # AM
    deviation_hz: float | None = None   # FM/PM
    pulse_width_s: float | None = None  # Pulse
    pulse_period_s: float | None = None  # Pulse
    source: str = "INTernal"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result: dict[str, Any] = {
            "mod_type": self.mod_type,
            "enabled": self.enabled,
            "source": self.source,
        }
        if self.depth_percent is not None:
            result["depth_percent"] = self.depth_percent
        if self.deviation_hz is not None:
            result["deviation_hz"] = self.deviation_hz
        if self.pulse_width_s is not None:
            result["pulse_width_s"] = self.pulse_width_s
        if self.pulse_period_s is not None:
            result["pulse_period_s"] = self.pulse_period_s
        return result


@dataclass
class BasebandConfig:
    """Baseband/ARB configuration."""

    waveform_file: str | None = None
    clock_rate_hz: float | None = None
    arb_enabled: bool = False
    digital_standard: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "waveform_file": self.waveform_file,
            "clock_rate_hz": self.clock_rate_hz,
            "arb_enabled": self.arb_enabled,
            "digital_standard": self.digital_standard,
        }
