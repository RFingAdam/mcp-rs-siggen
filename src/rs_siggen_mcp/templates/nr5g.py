"""5G NR signal template."""

from dataclasses import dataclass
from typing import Any

from .base import SignalTemplate


@dataclass
class NR5GTemplate(SignalTemplate):
    """5G NR signal template."""

    @classmethod
    def n78_100mhz(cls) -> "NR5GTemplate":
        """Create 5G NR Band n78 100 MHz template."""
        return cls(
            name="5G NR n78 100 MHz",
            description="5G NR Band n78 100 MHz signal",
            frequency_hz=3.5e9,
            power_dbm=-10.0,
            modulation_config={"standard": "nr5g", "bandwidth_mhz": 100, "numerology": 1},
        )

    @classmethod
    def n41_50mhz(cls) -> "NR5GTemplate":
        """Create 5G NR Band n41 50 MHz template."""
        return cls(
            name="5G NR n41 50 MHz",
            description="5G NR Band n41 50 MHz signal",
            frequency_hz=2.593e9,
            power_dbm=-10.0,
            modulation_config={"standard": "nr5g", "bandwidth_mhz": 50, "numerology": 1},
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NR5GTemplate":
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
