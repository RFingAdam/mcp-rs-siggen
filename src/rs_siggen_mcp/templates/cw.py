"""CW (Continuous Wave) signal template."""

from dataclasses import dataclass
from typing import Any

from .base import SignalTemplate


@dataclass
class CWSignalTemplate(SignalTemplate):
    """
    Template for CW signal generation.

    Provides factory methods for common CW signal configurations.
    """

    @classmethod
    def at_frequency(
        cls,
        frequency_hz: float,
        power_dbm: float = -10.0,
        name: str | None = None,
        description: str | None = None,
    ) -> "CWSignalTemplate":
        """
        Create CW signal template at a specific frequency.

        Args:
            frequency_hz: Carrier frequency in Hz
            power_dbm: Output power in dBm (default: -10)
            name: Optional template name
            description: Optional description

        Returns:
            CWSignalTemplate instance
        """
        if name is None:
            if frequency_hz >= 1e9:
                freq_str = f"{frequency_hz/1e9:.3f} GHz"
            elif frequency_hz >= 1e6:
                freq_str = f"{frequency_hz/1e6:.3f} MHz"
            else:
                freq_str = f"{frequency_hz/1e3:.3f} kHz"
            name = f"CW {freq_str}"

        if description is None:
            description = f"CW signal at {name.replace('CW ', '')} @ {power_dbm} dBm"

        return cls(
            name=name,
            description=description,
            frequency_hz=frequency_hz,
            power_dbm=power_dbm,
        )

    @classmethod
    def wifi_24ghz_carrier(cls) -> "CWSignalTemplate":
        """Create CW signal at 2.4 GHz WiFi center."""
        return cls.at_frequency(
            frequency_hz=2.437e9,
            power_dbm=-10.0,
            name="CW WiFi 2.4 GHz",
            description="CW signal at WiFi 2.4 GHz channel 6 center (2.437 GHz)",
        )

    @classmethod
    def wifi_5ghz_carrier(cls) -> "CWSignalTemplate":
        """Create CW signal at 5 GHz WiFi center."""
        return cls.at_frequency(
            frequency_hz=5.5e9,
            power_dbm=-10.0,
            name="CW WiFi 5 GHz",
            description="CW signal at WiFi 5 GHz band center (5.5 GHz)",
        )

    @classmethod
    def lte_band_1(cls) -> "CWSignalTemplate":
        """Create CW signal at LTE Band 1 center."""
        return cls.at_frequency(
            frequency_hz=2.14e9,
            power_dbm=-10.0,
            name="CW LTE Band 1",
            description="CW signal at LTE Band 1 DL center (2.14 GHz)",
        )

    @classmethod
    def ism_915mhz(cls) -> "CWSignalTemplate":
        """Create CW signal at 915 MHz ISM band."""
        return cls.at_frequency(
            frequency_hz=915e6,
            power_dbm=-10.0,
            name="CW ISM 915 MHz",
            description="CW signal at 915 MHz ISM band center",
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CWSignalTemplate":
        """Create from dictionary."""
        base = SignalTemplate.from_dict(data)
        return cls(
            name=base.name,
            description=base.description,
            frequency_hz=base.frequency_hz,
            power_dbm=base.power_dbm,
            output_enabled=base.output_enabled,
            modulation_config=base.modulation_config,
            created_at=base.created_at,
            metadata=base.metadata,
        )
