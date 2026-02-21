"""Pass/fail limit testing for signal generator output measurements."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class LimitFailure:
    """Details of a single limit violation."""

    frequency_hz: float
    measured_value: float
    limit_value: float
    limit_type: str  # "max" or "min"
    segment_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "frequency_hz": self.frequency_hz,
            "measured_value": self.measured_value,
            "limit_value": self.limit_value,
            "limit_type": self.limit_type,
            "segment_name": self.segment_name,
            "violation_db": abs(self.measured_value - self.limit_value),
        }


@dataclass
class LimitSegment:
    """
    Single frequency range limit definition.

    Defines upper and/or lower limits for a frequency range.
    Either max_db or min_db (or both) must be specified.

    Attributes:
        start_freq_hz: Segment start frequency
        stop_freq_hz: Segment stop frequency
        max_db: Upper limit in dB (measured value must be <= this)
        min_db: Lower limit in dB (measured value must be >= this)
        name: Optional segment name for reporting
    """

    start_freq_hz: float
    stop_freq_hz: float
    max_db: float | None = None
    min_db: float | None = None
    name: str | None = None

    def __post_init__(self):
        """Validate segment configuration."""
        if self.max_db is None and self.min_db is None:
            raise ValueError("LimitSegment must have at least max_db or min_db specified")
        if self.start_freq_hz >= self.stop_freq_hz:
            raise ValueError("start_freq_hz must be less than stop_freq_hz")

    def contains_frequency(self, freq_hz: float) -> bool:
        """Check if frequency is within this segment."""
        return self.start_freq_hz <= freq_hz <= self.stop_freq_hz

    def check_value(self, freq_hz: float, value_db: float) -> LimitFailure | None:
        """
        Check if a value passes the limit at this frequency.

        Args:
            freq_hz: Frequency in Hz
            value_db: Measured value in dB

        Returns:
            LimitFailure if limit violated, None if pass
        """
        if not self.contains_frequency(freq_hz):
            return None

        if self.max_db is not None and value_db > self.max_db:
            return LimitFailure(
                frequency_hz=freq_hz,
                measured_value=value_db,
                limit_value=self.max_db,
                limit_type="max",
                segment_name=self.name,
            )

        if self.min_db is not None and value_db < self.min_db:
            return LimitFailure(
                frequency_hz=freq_hz,
                measured_value=value_db,
                limit_value=self.min_db,
                limit_type="min",
                segment_name=self.name,
            )

        return None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "start_freq_hz": self.start_freq_hz,
            "stop_freq_hz": self.stop_freq_hz,
            "max_db": self.max_db,
            "min_db": self.min_db,
            "name": self.name,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LimitSegment":
        """Create from dictionary."""
        return cls(
            start_freq_hz=data["start_freq_hz"],
            stop_freq_hz=data["stop_freq_hz"],
            max_db=data.get("max_db"),
            min_db=data.get("min_db"),
            name=data.get("name"),
        )


@dataclass
class LimitResult:
    """
    Result of limit checking.

    Contains pass/fail status and details of any violations.

    Attributes:
        passed: True if all points pass limits
        failures: List of limit violations
        total_points: Total number of points checked
        failed_points: Number of points that failed
        worst_failure: The violation with largest margin
    """

    passed: bool
    failures: list[LimitFailure]
    total_points: int
    failed_points: int
    worst_failure: LimitFailure | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result: dict[str, Any] = {
            "passed": self.passed,
            "total_points": self.total_points,
            "failed_points": self.failed_points,
            "pass_rate": (self.total_points - self.failed_points) / self.total_points
                         if self.total_points > 0 else 0,
        }

        if self.worst_failure:
            result["worst_failure"] = self.worst_failure.to_dict()

        if self.failures:
            result["failure_count"] = len(self.failures)
            result["failures"] = [f.to_dict() for f in self.failures[:10]]  # First 10
            if len(self.failures) > 10:
                result["additional_failures"] = len(self.failures) - 10

        return result


@dataclass
class LimitLine:
    """
    Complete limit line definition.

    A limit line consists of one or more segments that define
    pass/fail criteria over a frequency range.

    Attributes:
        name: Limit line name
        segments: List of limit segments
        description: Optional description
        created_at: Creation timestamp
    """

    name: str
    segments: list[LimitSegment]
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)

    def check_points(
        self,
        frequencies: list[float],
        values_db: list[float],
    ) -> LimitResult:
        """
        Check measurement data against all limit segments.

        Args:
            frequencies: List of frequencies in Hz
            values_db: List of measured values in dB

        Returns:
            LimitResult with pass/fail status and details
        """
        failures: list[LimitFailure] = []

        for i, freq in enumerate(frequencies):
            value_db = values_db[i]

            for segment in self.segments:
                failure = segment.check_value(freq, value_db)
                if failure:
                    failures.append(failure)
                    break  # Only one failure per frequency point

        # Find worst failure
        worst = None
        if failures:
            worst = max(failures, key=lambda f: abs(f.measured_value - f.limit_value))

        return LimitResult(
            passed=len(failures) == 0,
            failures=failures,
            total_points=len(frequencies),
            failed_points=len(failures),
            worst_failure=worst,
        )

    def check_single_point(self, freq_hz: float, value_db: float) -> LimitFailure | None:
        """
        Check a single point against limits.

        Args:
            freq_hz: Frequency in Hz
            value_db: Measured value in dB

        Returns:
            LimitFailure if violated, None if pass
        """
        for segment in self.segments:
            failure = segment.check_value(freq_hz, value_db)
            if failure:
                return failure
        return None

    def get_limit_at_frequency(self, freq_hz: float) -> dict[str, float | None]:
        """
        Get the limit values at a specific frequency.

        Args:
            freq_hz: Frequency in Hz

        Returns:
            Dictionary with max_db and min_db (None if no limit)
        """
        for segment in self.segments:
            if segment.contains_frequency(freq_hz):
                return {
                    "max_db": segment.max_db,
                    "min_db": segment.min_db,
                    "segment_name": segment.name,
                }
        return {"max_db": None, "min_db": None, "segment_name": None}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "segments": [s.to_dict() for s in self.segments],
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LimitLine":
        """Create from dictionary."""
        segments = [LimitSegment.from_dict(s) for s in data["segments"]]

        created_at = datetime.now()
        if data.get("created_at"):
            try:
                created_at = datetime.fromisoformat(data["created_at"])
            except ValueError:
                pass

        return cls(
            name=data["name"],
            segments=segments,
            description=data.get("description", ""),
            created_at=created_at,
        )

    def save(self, filepath: str | Path) -> None:
        """Save limit line to JSON file."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filepath: str | Path) -> "LimitLine":
        """Load limit line from JSON file."""
        with open(filepath) as f:
            data = json.load(f)
        return cls.from_dict(data)

    @classmethod
    def create_flat_limit(
        cls,
        name: str,
        start_freq_hz: float,
        stop_freq_hz: float,
        max_db: float | None = None,
        min_db: float | None = None,
    ) -> "LimitLine":
        """
        Create a simple flat limit line.

        Args:
            name: Limit line name
            start_freq_hz: Start frequency
            stop_freq_hz: Stop frequency
            max_db: Upper limit (constant across range)
            min_db: Lower limit (constant across range)

        Returns:
            LimitLine with single flat segment
        """
        segment = LimitSegment(
            start_freq_hz=start_freq_hz,
            stop_freq_hz=stop_freq_hz,
            max_db=max_db,
            min_db=min_db,
            name="full_range",
        )
        return cls(name=name, segments=[segment])

    @classmethod
    def create_power_flatness_limit(
        cls,
        start_freq_hz: float,
        stop_freq_hz: float,
        max_deviation_db: float = 1.0,
        nominal_power_dbm: float = 0.0,
    ) -> "LimitLine":
        """
        Create a power flatness limit.

        Args:
            start_freq_hz: Start frequency
            stop_freq_hz: Stop frequency
            max_deviation_db: Maximum allowed deviation from nominal
            nominal_power_dbm: Nominal power level

        Returns:
            LimitLine for power flatness checking
        """
        return cls.create_flat_limit(
            name=f"Power Flatness +/-{max_deviation_db} dB",
            start_freq_hz=start_freq_hz,
            stop_freq_hz=stop_freq_hz,
            max_db=nominal_power_dbm + max_deviation_db,
            min_db=nominal_power_dbm - max_deviation_db,
        )


class LimitManager:
    """
    Manages limit line definitions for a testing session.

    Provides storage and retrieval of limit lines, and batch
    checking of measurements against multiple limits.
    """

    def __init__(self):
        """Initialize limit manager."""
        self._limits: dict[str, LimitLine] = {}

    def add_limit(self, limit: LimitLine) -> None:
        """
        Add or update a limit line.

        Args:
            limit: LimitLine to add
        """
        self._limits[limit.name] = limit

    def remove_limit(self, name: str) -> bool:
        """
        Remove a limit line by name.

        Args:
            name: Name of limit to remove

        Returns:
            True if removed, False if not found
        """
        if name in self._limits:
            del self._limits[name]
            return True
        return False

    def get_limit(self, name: str) -> LimitLine | None:
        """
        Get a limit line by name.

        Args:
            name: Name of limit to retrieve

        Returns:
            LimitLine or None if not found
        """
        return self._limits.get(name)

    def list_limits(self) -> list[str]:
        """
        List all limit line names.

        Returns:
            List of limit names
        """
        return list(self._limits.keys())

    def clear_limits(self) -> None:
        """Remove all limit lines."""
        self._limits.clear()

    def check_all(
        self,
        frequencies: list[float],
        values_db: list[float],
    ) -> dict[str, LimitResult]:
        """
        Check measurement against all defined limits.

        Args:
            frequencies: List of frequencies in Hz
            values_db: List of measured values in dB

        Returns:
            Dictionary mapping limit name to result
        """
        results = {}
        for name, limit in self._limits.items():
            results[name] = limit.check_points(frequencies, values_db)
        return results

    def get_overall_status(
        self,
        frequencies: list[float],
        values_db: list[float],
    ) -> dict[str, Any]:
        """
        Get overall pass/fail status across all limits.

        Args:
            frequencies: List of frequencies in Hz
            values_db: List of measured values in dB

        Returns:
            Dictionary with overall status and per-limit results
        """
        results = self.check_all(frequencies, values_db)
        all_passed = all(r.passed for r in results.values())

        return {
            "overall_passed": all_passed,
            "limits_checked": len(results),
            "limits_passed": sum(1 for r in results.values() if r.passed),
            "limits_failed": sum(1 for r in results.values() if not r.passed),
            "results": {name: result.to_dict() for name, result in results.items()},
        }
