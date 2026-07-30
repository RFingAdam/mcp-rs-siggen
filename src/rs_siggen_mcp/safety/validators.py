"""Safety validators for signal generator parameters.

The SCPI-injection and path-containment *logic* moved to :mod:`scpi_core.safety`,
where one copy replaces what were three near-verbatim variants across the R&S
servers. The two functions below stay as thin adapters because the *wording* of
the refusal is this server's user-facing contract -- ``tests/test_security.py``
pins each phrase, and the three servers' phrasings had already diverged, so they
cannot be unified without changing behaviour those tests deliberately assert.

The split is: the core decides *which rule* fired and reports it as data on the
exception; this module renders that rule in this server's historical words. The
core's ``ScpiParamError`` / ``UnsafePathError`` already subclass ``ValueError``,
so re-raising as ``ValueError`` keeps the declared contract exact.

``SafetyLimits`` and ``SafetyValidator`` below are instrument-specific -- power,
frequency, AM depth and FM deviation envelopes for a signal generator -- and stay
here.
"""

import logging
from dataclasses import dataclass
from pathlib import Path

from scpi_core.safety import (
    PathRule,
    ScpiParamError,
    ScpiParamRule,
    UnsafePathError,
    check_safe_path,
    check_scpi_param,
)

from ..exceptions import SafetyError

logger = logging.getLogger(__name__)


# =============================================================================
# SCPI Parameter Sanitizer (Issue 1)
# =============================================================================


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
    try:
        return check_scpi_param(value)
    except ScpiParamError as e:
        raise ValueError(_scpi_param_message(e)) from e


def _scpi_param_message(e: ScpiParamError) -> str:
    """Render a core refusal in this server's historical wording."""
    if e.rule is ScpiParamRule.NOT_A_STRING:
        return f"Expected string parameter, got {e.type_name}"
    if e.rule is ScpiParamRule.DANGEROUS_CHARACTER:
        return (
            f"SCPI injection detected: parameter contains forbidden character "
            f"{e.character!r} at position {e.position}"
        )
    return (
        "SCPI injection detected: parameter starts with '*' which could "
        "trigger instrument common commands (e.g., *RST, *CLS)"
    )


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
    try:
        return check_safe_path(user_path, base_dir)
    except UnsafePathError as e:
        raise ValueError(_unsafe_path_message(e)) from e


def _unsafe_path_message(e: UnsafePathError) -> str:
    """Render a core refusal in this server's historical wording."""
    if e.rule is PathRule.TRAVERSAL:
        return (
            f"Path traversal detected: resolved path '{e.resolved}' is outside "
            f"the allowed base directory '{e.base}'"
        )
    return (
        f"Symlink attack detected: '{e.link}' points to "
        f"'{e.target}' which is outside the allowed base directory"
    )


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
