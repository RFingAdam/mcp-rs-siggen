"""Safety validators for signal generator parameters."""

import logging
from dataclasses import dataclass

from ..exceptions import SafetyError

logger = logging.getLogger(__name__)


@dataclass
class SafetyLimits:
    """
    Safety limits for signal generator parameters.

    All limits are configurable via environment variables.
    """

    max_power_dbm: float = 20.0
    min_power_dbm: float = -140.0
    max_frequency_hz: float = 67e9  # 67 GHz (SMW200A max)
    min_frequency_hz: float = 8e3  # 8 kHz


class SafetyValidator:
    """
    Validates signal generator parameters against safety limits.

    Prevents accidental damage to equipment or DUT by enforcing
    configurable limits on power and frequency.
    """

    def __init__(self, limits: SafetyLimits | None = None):
        """
        Initialize validator with limits.

        Args:
            limits: Safety limits (uses defaults if None)
        """
        self.limits = limits or SafetyLimits()

    def validate_power(self, power_dbm: float) -> None:
        """
        Validate output power level.

        Args:
            power_dbm: Power level in dBm

        Raises:
            SafetyError: If power exceeds limits
        """
        if power_dbm > self.limits.max_power_dbm:
            raise SafetyError(
                f"Power {power_dbm} dBm exceeds maximum allowed {self.limits.max_power_dbm} dBm",
                parameter="power_dbm",
                value=power_dbm,
                limit=self.limits.max_power_dbm,
            )

        if power_dbm < self.limits.min_power_dbm:
            raise SafetyError(
                f"Power {power_dbm} dBm below minimum allowed {self.limits.min_power_dbm} dBm",
                parameter="power_dbm",
                value=power_dbm,
                limit=self.limits.min_power_dbm,
            )

        logger.debug(f"Power {power_dbm} dBm validated")

    def validate_frequency(self, frequency_hz: float) -> None:
        """
        Validate frequency.

        Args:
            frequency_hz: Frequency in Hz

        Raises:
            SafetyError: If frequency exceeds limits
        """
        if frequency_hz > self.limits.max_frequency_hz:
            raise SafetyError(
                f"Frequency {frequency_hz/1e9:.3f} GHz exceeds maximum "
                f"{self.limits.max_frequency_hz/1e9:.3f} GHz",
                parameter="frequency_hz",
                value=frequency_hz,
                limit=self.limits.max_frequency_hz,
            )

        if frequency_hz < self.limits.min_frequency_hz:
            raise SafetyError(
                f"Frequency {frequency_hz/1e3:.3f} kHz below minimum "
                f"{self.limits.min_frequency_hz/1e3:.3f} kHz",
                parameter="frequency_hz",
                value=frequency_hz,
                limit=self.limits.min_frequency_hz,
            )

        logger.debug(f"Frequency {frequency_hz/1e6:.3f} MHz validated")

    def validate_frequency_range(
        self, start_freq_hz: float, stop_freq_hz: float
    ) -> None:
        """
        Validate frequency range.

        Args:
            start_freq_hz: Start frequency in Hz
            stop_freq_hz: Stop frequency in Hz

        Raises:
            SafetyError: If frequencies exceed limits
            ValueError: If start >= stop
        """
        self.validate_frequency(start_freq_hz)
        self.validate_frequency(stop_freq_hz)

        if start_freq_hz >= stop_freq_hz:
            raise ValueError(
                f"Start frequency ({start_freq_hz/1e6:.3f} MHz) must be less than "
                f"stop frequency ({stop_freq_hz/1e6:.3f} MHz)"
            )

    def validate_modulation_depth(self, depth_percent: float) -> None:
        """
        Validate AM modulation depth.

        Args:
            depth_percent: Modulation depth in percent

        Raises:
            ValueError: If depth is out of range
        """
        if depth_percent < 0 or depth_percent > 100:
            raise ValueError(
                f"AM modulation depth {depth_percent}% must be between 0 and 100%"
            )

        logger.debug(f"AM depth {depth_percent}% validated")

    def validate_deviation(self, deviation_hz: float) -> None:
        """
        Validate FM deviation.

        Args:
            deviation_hz: FM deviation in Hz

        Raises:
            ValueError: If deviation is negative
        """
        if deviation_hz < 0:
            raise ValueError(f"FM deviation {deviation_hz} Hz must be positive")

        logger.debug(f"FM deviation {deviation_hz/1e3:.3f} kHz validated")

    def validate_pulse_width(self, width_s: float, period_s: float | None = None) -> None:
        """
        Validate pulse modulation parameters.

        Args:
            width_s: Pulse width in seconds
            period_s: Pulse period in seconds (optional)

        Raises:
            ValueError: If parameters are invalid
        """
        if width_s <= 0:
            raise ValueError(f"Pulse width {width_s} s must be positive")

        if period_s is not None:
            if period_s <= 0:
                raise ValueError(f"Pulse period {period_s} s must be positive")
            if width_s >= period_s:
                raise ValueError(
                    f"Pulse width ({width_s} s) must be less than period ({period_s} s)"
                )

        logger.debug(f"Pulse width {width_s*1e6:.1f} us validated")
