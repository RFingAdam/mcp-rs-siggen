"""Immunity test signal templates (IEC 61000-4-3, ISO 11452-2, etc.)."""

from dataclasses import dataclass
from typing import Any

from .base import SignalTemplate


@dataclass
class ImmunityTestTemplate(SignalTemplate):
    """
    Template for radiated/conducted immunity testing.

    Provides factory methods for standard EMC immunity test configurations
    per IEC 61000-4-3 (radiated) and ISO 11452-2 (automotive).
    """

    sweep_start_hz: float = 80e6
    sweep_stop_hz: float = 6e9
    dwell_time_s: float = 3.0
    step_size_percent: float = 1.0
    am_depth_percent: float = 80.0
    am_frequency_hz: float = 1e3

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        data = super().to_dict()
        data.update({
            "sweep_start_hz": self.sweep_start_hz,
            "sweep_stop_hz": self.sweep_stop_hz,
            "dwell_time_s": self.dwell_time_s,
            "step_size_percent": self.step_size_percent,
            "am_depth_percent": self.am_depth_percent,
            "am_frequency_hz": self.am_frequency_hz,
        })
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ImmunityTestTemplate":
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
            sweep_start_hz=data.get("sweep_start_hz", 80e6),
            sweep_stop_hz=data.get("sweep_stop_hz", 6e9),
            dwell_time_s=data.get("dwell_time_s", 3.0),
            step_size_percent=data.get("step_size_percent", 1.0),
            am_depth_percent=data.get("am_depth_percent", 80.0),
            am_frequency_hz=data.get("am_frequency_hz", 1e3),
        )

    @classmethod
    def iec_61000_4_3(
        cls,
        test_level: int = 3,
    ) -> "ImmunityTestTemplate":
        """
        Create IEC 61000-4-3 radiated immunity test template.

        IEC 61000-4-3 defines radiated immunity testing levels:
        - Level 1: 1 V/m
        - Level 2: 3 V/m
        - Level 3: 10 V/m (most common)
        - Level 4: 30 V/m

        The signal is 80% AM modulated with 1 kHz sine.
        Frequency range: 80 MHz to 6 GHz (per recent amendments).

        Args:
            test_level: Test level 1-4

        Returns:
            ImmunityTestTemplate configured for IEC 61000-4-3
        """
        # Field strength levels (V/m) - power level depends on antenna + amp
        level_map = {1: 1, 2: 3, 3: 10, 4: 30}
        field_strength = level_map.get(test_level, 10)

        # Power level is nominal; actual power depends on chamber setup
        # These are typical starting points for common antenna/amp combos
        power_map = {1: -10.0, 2: 0.0, 3: 10.0, 4: 20.0}
        power = power_map.get(test_level, 10.0)

        return cls(
            name=f"IEC 61000-4-3 Level {test_level}",
            description=(
                f"Radiated immunity per IEC 61000-4-3, Level {test_level} "
                f"({field_strength} V/m), 80% AM @ 1 kHz, 80 MHz - 6 GHz"
            ),
            frequency_hz=80e6,  # Start frequency
            power_dbm=power,
            output_enabled=False,  # Safety: don't auto-enable
            modulation_config={
                "am_enabled": True,
                "am_depth_percent": 80.0,
                "am_frequency_hz": 1000.0,
            },
            sweep_start_hz=80e6,
            sweep_stop_hz=6e9,
            dwell_time_s=3.0,
            step_size_percent=1.0,
            am_depth_percent=80.0,
            am_frequency_hz=1e3,
            metadata={
                "standard": "IEC 61000-4-3",
                "test_level": test_level,
                "field_strength_vm": field_strength,
            },
        )

    @classmethod
    def iso_11452_2(
        cls,
        field_strength_vm: float = 200.0,
    ) -> "ImmunityTestTemplate":
        """
        Create ISO 11452-2 automotive radiated immunity test template.

        ISO 11452-2 defines component-level radiated immunity for automotive.
        Typical field strengths: 30-200 V/m.
        Modulation: CW or 80% AM @ 1 kHz.
        Frequency range: 200 MHz to 2 GHz (extendable to 18 GHz).

        Args:
            field_strength_vm: Required field strength in V/m

        Returns:
            ImmunityTestTemplate configured for ISO 11452-2
        """
        return cls(
            name=f"ISO 11452-2 ({field_strength_vm} V/m)",
            description=(
                f"Automotive radiated immunity per ISO 11452-2, "
                f"{field_strength_vm} V/m, 80% AM @ 1 kHz, 200 MHz - 2 GHz"
            ),
            frequency_hz=200e6,  # Start frequency
            power_dbm=10.0,  # Nominal; depends on amp/antenna
            output_enabled=False,  # Safety: don't auto-enable
            modulation_config={
                "am_enabled": True,
                "am_depth_percent": 80.0,
                "am_frequency_hz": 1000.0,
            },
            sweep_start_hz=200e6,
            sweep_stop_hz=2e9,
            dwell_time_s=2.0,
            step_size_percent=1.0,
            am_depth_percent=80.0,
            am_frequency_hz=1e3,
            metadata={
                "standard": "ISO 11452-2",
                "field_strength_vm": field_strength_vm,
            },
        )
