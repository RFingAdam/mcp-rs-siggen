"""Two-tone signal template for intermodulation testing."""

from dataclasses import dataclass
from typing import Any

from .base import SignalTemplate


@dataclass
class TwoToneTemplate(SignalTemplate):
    """Two-tone signal template for intermodulation testing."""

    @classmethod
    def standard_1mhz_spacing(cls, center_freq_hz: float = 1e9) -> "TwoToneTemplate":
        """Create two-tone template with 1 MHz spacing."""
        return cls(
            name="Two-Tone 1 MHz Spacing",
            description="Two-tone signal with 1 MHz spacing for IP3/IMD testing",
            frequency_hz=center_freq_hz,
            power_dbm=-10.0,
            modulation_config={"type": "two_tone", "spacing_hz": 1e6},
        )

    @classmethod
    def standard_10mhz_spacing(cls, center_freq_hz: float = 1e9) -> "TwoToneTemplate":
        """Create two-tone template with 10 MHz spacing."""
        return cls(
            name="Two-Tone 10 MHz Spacing",
            description="Two-tone signal with 10 MHz spacing",
            frequency_hz=center_freq_hz,
            power_dbm=-10.0,
            modulation_config={"type": "two_tone", "spacing_hz": 10e6},
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TwoToneTemplate":
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
