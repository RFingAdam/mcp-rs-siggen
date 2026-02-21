"""Safety validators for signal generator parameters."""

import logging
import re
from dataclasses import dataclass
from pathlib import Path

from ..exceptions import SafetyError

logger = logging.getLogger(__name__)


# =============================================================================
# SCPI Parameter Sanitizer (Issue 1)
# =============================================================================

# Characters that can be used for SCPI command injection
_SCPI_DANGEROUS_CHARS = re.compile(r"[;\n\r]")


def sanitize_scpi_param(value: str) -> str:
    """
    Sanitize a user-provided string parameter before interpolation into SCPI commands.

    Rejects strings containing SCPI metacharacters that could allow command injection:
    - `;` (SCPI command separator - allows chaining additional commands)
    - `\\n` and `\\r` (newlines that could inject commands on a new line)
    - Leading `*` (could trigger IEEE 488.2 common commands like *RST, *CLS)

    This function is intended for string parameters (filenames, identifiers,
    directory paths on the instrument, etc.). Numeric parameters that are already
    validated by SafetyValidator do not need this sanitizer.

    Args:
        value: The user-provided string to sanitize

    Returns:
        The validated string (unchanged if safe)

    Raises:
        ValueError: If the string contains dangerous SCPI metacharacters
    """
    if not isinstance(value, str):
        raise ValueError(f"Expected string parameter, got {type(value).__name__}")

    # Check for SCPI command separator and newline injection
    match = _SCPI_DANGEROUS_CHARS.search(value)
    if match:
        char = match.group()
        char_repr = repr(char)
        raise ValueError(
            f"SCPI injection detected: parameter contains forbidden character "
            f"{char_repr} at position {match.start()}"
        )

    # Check for leading * which could trigger IEEE 488.2 common commands
    if value.lstrip().startswith("*"):
        raise ValueError(
            "SCPI injection detected: parameter starts with '*' which could "
            "trigger instrument common commands (e.g., *RST, *CLS)"
        )

    return value


# =============================================================================
# File Path Validator (Issue 2)
# =============================================================================


def validate_safe_path(user_path: str | Path, base_dir: str | Path) -> Path:
    """
    Validate that a user-provided file path is safe and contained within the base directory.

    Uses Path.resolve() to canonicalize the path (resolving .., symlinks, etc.)
    and then checks that the resolved path is relative to the base directory.

    This prevents:
    - Path traversal attacks (../../etc/passwd)
    - Absolute path escapes (/etc/passwd)
    - Symlink attacks (symlink pointing outside base_dir)

    Args:
        user_path: The user-provided file path (relative or absolute)
        base_dir: The base directory that all paths must be contained within

    Returns:
        The resolved, validated Path object

    Raises:
        ValueError: If the path escapes the base directory or is otherwise unsafe
    """
    base_dir = Path(base_dir).resolve()
    user_path = Path(user_path)

    # If user_path is not absolute, treat it as relative to base_dir
    if not user_path.is_absolute():
        resolved = (base_dir / user_path).resolve()
    else:
        resolved = user_path.resolve()

    # Check that the resolved path is within the base directory
    if not resolved.is_relative_to(base_dir):
        raise ValueError(
            f"Path traversal detected: resolved path '{resolved}' is outside "
            f"the allowed base directory '{base_dir}'"
        )

    # Check if any component of the path is a symlink pointing outside base_dir
    # Walk up from the resolved path to check each existing component
    check_path = resolved
    while check_path != base_dir and check_path != check_path.parent:
        if check_path.is_symlink():
            link_target = check_path.resolve()
            if not link_target.is_relative_to(base_dir):
                raise ValueError(
                    f"Symlink attack detected: '{check_path}' points to "
                    f"'{link_target}' which is outside the allowed base directory"
                )
        check_path = check_path.parent

    return resolved


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
    max_am_depth_pct: float = 100.0
    max_fm_deviation_hz: float = 40e6


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
            SafetyError: If depth is out of range
        """
        if depth_percent < 0 or depth_percent > self.limits.max_am_depth_pct:
            raise SafetyError(
                f"AM modulation depth {depth_percent}% must be between 0 and "
                f"{self.limits.max_am_depth_pct}%",
                parameter="depth_percent",
                value=depth_percent,
                limit=self.limits.max_am_depth_pct,
            )

        logger.debug(f"AM depth {depth_percent}% validated")

    def validate_deviation(self, deviation_hz: float) -> None:
        """
        Validate FM deviation.

        Args:
            deviation_hz: FM deviation in Hz

        Raises:
            SafetyError: If deviation is negative or exceeds maximum
        """
        if deviation_hz < 0:
            raise SafetyError(
                f"FM deviation {deviation_hz} Hz must be positive",
                parameter="deviation_hz",
                value=deviation_hz,
                limit=0.0,
            )

        if deviation_hz > self.limits.max_fm_deviation_hz:
            raise SafetyError(
                f"FM deviation {deviation_hz/1e6:.3f} MHz exceeds maximum "
                f"{self.limits.max_fm_deviation_hz/1e6:.3f} MHz",
                parameter="deviation_hz",
                value=deviation_hz,
                limit=self.limits.max_fm_deviation_hz,
            )

        logger.debug(f"FM deviation {deviation_hz/1e3:.3f} kHz validated")

    def validate_pulse_width(self, width_s: float, period_s: float | None = None) -> None:
        """
        Validate pulse modulation parameters.

        Args:
            width_s: Pulse width in seconds
            period_s: Pulse period in seconds (optional)

        Raises:
            SafetyError: If parameters are invalid
        """
        if width_s <= 0:
            raise SafetyError(
                f"Pulse width {width_s} s must be positive",
                parameter="width_s",
                value=width_s,
                limit=0.0,
            )

        if period_s is not None:
            if period_s <= 0:
                raise SafetyError(
                    f"Pulse period {period_s} s must be positive",
                    parameter="period_s",
                    value=period_s,
                    limit=0.0,
                )
            if width_s >= period_s:
                raise SafetyError(
                    f"Pulse width ({width_s} s) must be less than period ({period_s} s)",
                    parameter="width_s",
                    value=width_s,
                    limit=period_s,
                )

        logger.debug(f"Pulse width {width_s*1e6:.1f} us validated")
