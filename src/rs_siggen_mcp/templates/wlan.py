"""WiFi 6/6E signal template."""

from dataclasses import dataclass
from typing import Any

from .base import SignalTemplate


@dataclass
class WLANTemplate(SignalTemplate):
    """WiFi 6/6E signal template."""

    @classmethod
    def wifi6_80mhz(cls) -> "WLANTemplate":
        """Create WiFi 6 80 MHz template."""
        return cls(
            name="WiFi 6 80 MHz",
            description="WiFi 6 (802.11ax) 80 MHz signal",
            frequency_hz=5.21e9,
            power_dbm=-10.0,
            modulation_config={"standard": "wlan", "protocol": "802.11ax", "bandwidth_mhz": 80},
        )

    @classmethod
    def wifi6e_160mhz(cls) -> "WLANTemplate":
        """Create WiFi 6E 160 MHz template."""
        return cls(
            name="WiFi 6E 160 MHz",
            description="WiFi 6E (802.11ax) 160 MHz signal",
            frequency_hz=6.105e9,
            power_dbm=-10.0,
            modulation_config={"standard": "wlan", "protocol": "802.11ax", "bandwidth_mhz": 160},
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WLANTemplate":
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
