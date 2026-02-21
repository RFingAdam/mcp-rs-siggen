"""LTE downlink signal template."""

from dataclasses import dataclass
from typing import Any

from .base import SignalTemplate


@dataclass
class LTEDownlinkTemplate(SignalTemplate):
    """LTE FDD downlink signal template."""

    @classmethod
    def band_1_10mhz(cls) -> "LTEDownlinkTemplate":
        """Create LTE Band 1 10 MHz downlink template."""
        return cls(
            name="LTE Band 1 10 MHz Downlink",
            description="LTE FDD Band 1 10 MHz downlink signal",
            frequency_hz=2.14e9,
            power_dbm=-10.0,
            modulation_config={
                "standard": "lte",
                "bandwidth_mhz": 10,
                "duplex": "fdd",
                "direction": "downlink",
            },
        )

    @classmethod
    def band_7_20mhz(cls) -> "LTEDownlinkTemplate":
        """Create LTE Band 7 20 MHz downlink template."""
        return cls(
            name="LTE Band 7 20 MHz Downlink",
            description="LTE FDD Band 7 20 MHz downlink signal",
            frequency_hz=2.655e9,
            power_dbm=-10.0,
            modulation_config={
                "standard": "lte",
                "bandwidth_mhz": 20,
                "duplex": "fdd",
                "direction": "downlink",
            },
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LTEDownlinkTemplate":
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
