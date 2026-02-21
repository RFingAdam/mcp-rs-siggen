"""Tests for limit testing system."""

import tempfile
from pathlib import Path

import pytest

from rs_siggen_mcp.limits import (
    LimitFailure,
    LimitLine,
    LimitManager,
    LimitResult,
    LimitSegment,
)


class TestLimitSegment:
    """Test LimitSegment dataclass."""

    def test_basic_max_limit(self):
        """Test max limit segment."""
        seg = LimitSegment(
            start_freq_hz=1e9,
            stop_freq_hz=2e9,
            max_db=-10.0,
            name="test",
        )
        assert seg.contains_frequency(1.5e9)
        assert not seg.contains_frequency(3e9)

    def test_basic_min_limit(self):
        """Test min limit segment."""
        seg = LimitSegment(
            start_freq_hz=1e9,
            stop_freq_hz=2e9,
            min_db=-30.0,
        )
        assert seg.min_db == -30.0

    def test_both_limits(self):
        """Test segment with both max and min."""
        seg = LimitSegment(
            start_freq_hz=1e9,
            stop_freq_hz=2e9,
            max_db=-10.0,
            min_db=-30.0,
        )
        assert seg.max_db == -10.0
        assert seg.min_db == -30.0

    def test_no_limits_raises(self):
        """Test that no limits raises error."""
        with pytest.raises(ValueError):
            LimitSegment(start_freq_hz=1e9, stop_freq_hz=2e9)

    def test_invalid_range_raises(self):
        """Test that invalid range raises error."""
        with pytest.raises(ValueError):
            LimitSegment(start_freq_hz=2e9, stop_freq_hz=1e9, max_db=0)

    def test_check_value_pass(self):
        """Test value within limits."""
        seg = LimitSegment(
            start_freq_hz=1e9,
            stop_freq_hz=2e9,
            max_db=-10.0,
            min_db=-30.0,
        )
        result = seg.check_value(1.5e9, -20.0)
        assert result is None  # Pass

    def test_check_value_fail_max(self):
        """Test value exceeds max limit."""
        seg = LimitSegment(
            start_freq_hz=1e9,
            stop_freq_hz=2e9,
            max_db=-10.0,
        )
        result = seg.check_value(1.5e9, -5.0)
        assert result is not None
        assert result.limit_type == "max"
        assert result.measured_value == -5.0
        assert result.limit_value == -10.0

    def test_check_value_fail_min(self):
        """Test value below min limit."""
        seg = LimitSegment(
            start_freq_hz=1e9,
            stop_freq_hz=2e9,
            min_db=-30.0,
        )
        result = seg.check_value(1.5e9, -35.0)
        assert result is not None
        assert result.limit_type == "min"

    def test_check_value_outside_range(self):
        """Test value at frequency outside segment."""
        seg = LimitSegment(
            start_freq_hz=1e9,
            stop_freq_hz=2e9,
            max_db=-10.0,
        )
        result = seg.check_value(3e9, 0.0)
        assert result is None  # Outside range, no check

    def test_to_dict(self):
        """Test dictionary conversion."""
        seg = LimitSegment(
            start_freq_hz=1e9,
            stop_freq_hz=2e9,
            max_db=-10.0,
            name="test",
        )
        d = seg.to_dict()
        assert d["start_freq_hz"] == 1e9
        assert d["max_db"] == -10.0
        assert d["name"] == "test"

    def test_from_dict(self):
        """Test creation from dictionary."""
        d = {
            "start_freq_hz": 1e9,
            "stop_freq_hz": 2e9,
            "max_db": -10.0,
            "min_db": -30.0,
            "name": "test",
        }
        seg = LimitSegment.from_dict(d)
        assert seg.start_freq_hz == 1e9
        assert seg.max_db == -10.0


class TestLimitFailure:
    """Test LimitFailure dataclass."""

    def test_to_dict(self):
        """Test dictionary conversion."""
        failure = LimitFailure(
            frequency_hz=1.5e9,
            measured_value=-5.0,
            limit_value=-10.0,
            limit_type="max",
            segment_name="test",
        )
        d = failure.to_dict()
        assert d["frequency_hz"] == 1.5e9
        assert d["violation_db"] == 5.0
        assert d["limit_type"] == "max"


class TestLimitLine:
    """Test LimitLine class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.segments = [
            LimitSegment(
                start_freq_hz=1e9,
                stop_freq_hz=2e9,
                max_db=-10.0,
                name="low_band",
            ),
            LimitSegment(
                start_freq_hz=2e9,
                stop_freq_hz=3e9,
                max_db=-15.0,
                name="high_band",
            ),
        ]
        self.limit = LimitLine(
            name="test_limit",
            segments=self.segments,
            description="Test limit line",
        )

    def test_check_points_all_pass(self):
        """Test all points passing."""
        freqs = [1.5e9, 2.5e9]
        values = [-20.0, -20.0]
        result = self.limit.check_points(freqs, values)
        assert result.passed is True
        assert result.total_points == 2
        assert result.failed_points == 0

    def test_check_points_with_failures(self):
        """Test with some failures."""
        freqs = [1.5e9, 2.5e9]
        values = [-5.0, -20.0]  # First point fails
        result = self.limit.check_points(freqs, values)
        assert result.passed is False
        assert result.failed_points == 1
        assert result.worst_failure is not None

    def test_check_single_point_pass(self):
        """Test single point check - pass."""
        result = self.limit.check_single_point(1.5e9, -20.0)
        assert result is None

    def test_check_single_point_fail(self):
        """Test single point check - fail."""
        result = self.limit.check_single_point(1.5e9, -5.0)
        assert result is not None
        assert result.limit_type == "max"

    def test_get_limit_at_frequency(self):
        """Test getting limit at specific frequency."""
        result = self.limit.get_limit_at_frequency(1.5e9)
        assert result["max_db"] == -10.0
        assert result["segment_name"] == "low_band"

    def test_get_limit_at_frequency_outside(self):
        """Test getting limit at frequency outside segments."""
        result = self.limit.get_limit_at_frequency(5e9)
        assert result["max_db"] is None

    def test_save_and_load(self):
        """Test save to file and load back."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            filepath = f.name

        try:
            self.limit.save(filepath)
            loaded = LimitLine.load(filepath)
            assert loaded.name == "test_limit"
            assert len(loaded.segments) == 2
            assert loaded.segments[0].max_db == -10.0
        finally:
            Path(filepath).unlink(missing_ok=True)

    def test_to_dict(self):
        """Test dictionary conversion."""
        d = self.limit.to_dict()
        assert d["name"] == "test_limit"
        assert len(d["segments"]) == 2

    def test_from_dict(self):
        """Test creation from dictionary."""
        d = self.limit.to_dict()
        restored = LimitLine.from_dict(d)
        assert restored.name == "test_limit"
        assert len(restored.segments) == 2

    def test_create_flat_limit(self):
        """Test flat limit creation."""
        limit = LimitLine.create_flat_limit(
            name="flat",
            start_freq_hz=1e9,
            stop_freq_hz=6e9,
            max_db=-10.0,
        )
        assert limit.name == "flat"
        assert len(limit.segments) == 1
        assert limit.segments[0].max_db == -10.0

    def test_create_power_flatness_limit(self):
        """Test power flatness limit creation."""
        limit = LimitLine.create_power_flatness_limit(
            start_freq_hz=1e9,
            stop_freq_hz=6e9,
            max_deviation_db=0.5,
            nominal_power_dbm=-10.0,
        )
        assert limit.segments[0].max_db == -9.5
        assert limit.segments[0].min_db == -10.5


class TestLimitResult:
    """Test LimitResult dataclass."""

    def test_passing_result(self):
        """Test passing result."""
        result = LimitResult(
            passed=True,
            failures=[],
            total_points=100,
            failed_points=0,
        )
        d = result.to_dict()
        assert d["passed"] is True
        assert d["pass_rate"] == 1.0

    def test_failing_result(self):
        """Test failing result."""
        failure = LimitFailure(
            frequency_hz=1.5e9,
            measured_value=-5.0,
            limit_value=-10.0,
            limit_type="max",
        )
        result = LimitResult(
            passed=False,
            failures=[failure],
            total_points=100,
            failed_points=1,
            worst_failure=failure,
        )
        d = result.to_dict()
        assert d["passed"] is False
        assert d["failure_count"] == 1
        assert "worst_failure" in d

    def test_empty_result(self):
        """Test result with no points."""
        result = LimitResult(
            passed=True,
            failures=[],
            total_points=0,
            failed_points=0,
        )
        d = result.to_dict()
        assert d["pass_rate"] == 0


class TestLimitManager:
    """Test LimitManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = LimitManager()

    def test_add_limit(self):
        """Test adding limit."""
        limit = LimitLine.create_flat_limit("test", 1e9, 2e9, max_db=-10.0)
        self.manager.add_limit(limit)
        assert "test" in self.manager.list_limits()

    def test_remove_limit(self):
        """Test removing limit."""
        limit = LimitLine.create_flat_limit("test", 1e9, 2e9, max_db=-10.0)
        self.manager.add_limit(limit)
        assert self.manager.remove_limit("test") is True
        assert self.manager.remove_limit("nonexistent") is False

    def test_get_limit(self):
        """Test getting limit by name."""
        limit = LimitLine.create_flat_limit("test", 1e9, 2e9, max_db=-10.0)
        self.manager.add_limit(limit)
        retrieved = self.manager.get_limit("test")
        assert retrieved is not None
        assert retrieved.name == "test"
        assert self.manager.get_limit("nonexistent") is None

    def test_list_limits(self):
        """Test listing all limits."""
        self.manager.add_limit(
            LimitLine.create_flat_limit("limit1", 1e9, 2e9, max_db=-10.0)
        )
        self.manager.add_limit(
            LimitLine.create_flat_limit("limit2", 2e9, 3e9, max_db=-15.0)
        )
        names = self.manager.list_limits()
        assert len(names) == 2
        assert "limit1" in names
        assert "limit2" in names

    def test_clear_limits(self):
        """Test clearing all limits."""
        self.manager.add_limit(
            LimitLine.create_flat_limit("test", 1e9, 2e9, max_db=-10.0)
        )
        self.manager.clear_limits()
        assert len(self.manager.list_limits()) == 0

    def test_check_all(self):
        """Test checking against all limits."""
        self.manager.add_limit(
            LimitLine.create_flat_limit("test", 1e9, 2e9, max_db=-10.0)
        )
        results = self.manager.check_all([1.5e9], [-20.0])
        assert "test" in results
        assert results["test"].passed is True

    def test_get_overall_status(self):
        """Test overall status."""
        self.manager.add_limit(
            LimitLine.create_flat_limit("pass_limit", 1e9, 2e9, max_db=-10.0)
        )
        self.manager.add_limit(
            LimitLine.create_flat_limit("fail_limit", 1e9, 2e9, max_db=-25.0)
        )
        status = self.manager.get_overall_status([1.5e9], [-20.0])
        assert status["overall_passed"] is False
        assert status["limits_checked"] == 2
        assert status["limits_passed"] == 1
        assert status["limits_failed"] == 1
