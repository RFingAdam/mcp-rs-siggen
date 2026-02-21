"""Tests for safety validators."""

import pytest

from rs_siggen_mcp.exceptions import SafetyError
from rs_siggen_mcp.safety.validators import SafetyLimits, SafetyValidator


class TestSafetyLimits:
    """Test SafetyLimits dataclass."""

    def test_defaults(self):
        """Test default safety limits."""
        limits = SafetyLimits()
        assert limits.max_power_dbm == 20.0
        assert limits.min_power_dbm == -140.0
        assert limits.max_frequency_hz == 67e9
        assert limits.min_frequency_hz == 8e3
        assert limits.max_am_depth_pct == 100.0
        assert limits.max_fm_deviation_hz == 40e6

    def test_custom_limits(self):
        """Test custom safety limits."""
        limits = SafetyLimits(
            max_power_dbm=10.0,
            min_power_dbm=-60.0,
            max_frequency_hz=6e9,
            min_frequency_hz=100e3,
        )
        assert limits.max_power_dbm == 10.0
        assert limits.min_power_dbm == -60.0
        assert limits.max_frequency_hz == 6e9
        assert limits.min_frequency_hz == 100e3


class TestSafetyValidator:
    """Test SafetyValidator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.limits = SafetyLimits(
            max_power_dbm=20.0,
            min_power_dbm=-140.0,
            max_frequency_hz=67e9,
            min_frequency_hz=8e3,
        )
        self.validator = SafetyValidator(self.limits)

    def test_validate_power_ok(self):
        """Test valid power levels."""
        self.validator.validate_power(0.0)
        self.validator.validate_power(-10.0)
        self.validator.validate_power(20.0)
        self.validator.validate_power(-140.0)

    def test_validate_power_too_high(self):
        """Test power exceeds maximum."""
        with pytest.raises(SafetyError) as exc_info:
            self.validator.validate_power(21.0)
        assert exc_info.value.parameter == "power_dbm"
        assert exc_info.value.value == 21.0
        assert exc_info.value.limit == 20.0

    def test_validate_power_too_low(self):
        """Test power below minimum."""
        with pytest.raises(SafetyError) as exc_info:
            self.validator.validate_power(-141.0)
        assert exc_info.value.parameter == "power_dbm"
        assert exc_info.value.value == -141.0

    def test_validate_frequency_ok(self):
        """Test valid frequencies."""
        self.validator.validate_frequency(1e9)
        self.validator.validate_frequency(8e3)
        self.validator.validate_frequency(67e9)
        self.validator.validate_frequency(2.4e9)

    def test_validate_frequency_too_high(self):
        """Test frequency exceeds maximum."""
        with pytest.raises(SafetyError) as exc_info:
            self.validator.validate_frequency(68e9)
        assert exc_info.value.parameter == "frequency_hz"

    def test_validate_frequency_too_low(self):
        """Test frequency below minimum."""
        with pytest.raises(SafetyError) as exc_info:
            self.validator.validate_frequency(1e3)
        assert exc_info.value.parameter == "frequency_hz"

    def test_validate_frequency_range_ok(self):
        """Test valid frequency range."""
        self.validator.validate_frequency_range(1e9, 2e9)

    def test_validate_frequency_range_start_above_stop(self):
        """Test start frequency >= stop frequency."""
        with pytest.raises(ValueError):
            self.validator.validate_frequency_range(2e9, 1e9)

    def test_validate_frequency_range_equal(self):
        """Test start == stop frequency."""
        with pytest.raises(ValueError):
            self.validator.validate_frequency_range(1e9, 1e9)

    def test_validate_modulation_depth_ok(self):
        """Test valid modulation depths."""
        self.validator.validate_modulation_depth(0)
        self.validator.validate_modulation_depth(50)
        self.validator.validate_modulation_depth(100)

    def test_validate_modulation_depth_out_of_range(self):
        """Test invalid modulation depths."""
        with pytest.raises(ValueError):
            self.validator.validate_modulation_depth(101)
        with pytest.raises(ValueError):
            self.validator.validate_modulation_depth(-1)

    def test_validate_deviation_ok(self):
        """Test valid FM deviations."""
        self.validator.validate_deviation(75e3)
        self.validator.validate_deviation(0)

    def test_validate_deviation_negative(self):
        """Test negative FM deviation."""
        with pytest.raises(ValueError):
            self.validator.validate_deviation(-1)

    def test_validate_pulse_width_ok(self):
        """Test valid pulse parameters."""
        self.validator.validate_pulse_width(1e-6)
        self.validator.validate_pulse_width(1e-6, 10e-6)

    def test_validate_pulse_width_zero(self):
        """Test zero pulse width."""
        with pytest.raises(ValueError):
            self.validator.validate_pulse_width(0)

    def test_validate_pulse_width_exceeds_period(self):
        """Test pulse width >= period."""
        with pytest.raises(ValueError):
            self.validator.validate_pulse_width(10e-6, 5e-6)

    def test_default_limits(self):
        """Test validator with default limits."""
        validator = SafetyValidator()
        validator.validate_power(0.0)
        validator.validate_frequency(1e9)

    def test_custom_limits(self):
        """Test validator with custom limits."""
        limits = SafetyLimits(max_power_dbm=0.0)
        validator = SafetyValidator(limits)
        with pytest.raises(SafetyError):
            validator.validate_power(1.0)

    def test_custom_am_depth_limit(self):
        """Test custom AM depth limit."""
        limits = SafetyLimits(max_am_depth_pct=80.0)
        validator = SafetyValidator(limits)
        validator.validate_modulation_depth(80.0)
        with pytest.raises(ValueError):
            validator.validate_modulation_depth(81.0)

    def test_validate_deviation_exceeds_max(self):
        """Test FM deviation exceeding maximum."""
        with pytest.raises(ValueError):
            self.validator.validate_deviation(41e6)

    def test_validate_deviation_at_max(self):
        """Test FM deviation at exactly the maximum."""
        self.validator.validate_deviation(40e6)

    def test_custom_fm_deviation_limit(self):
        """Test custom FM deviation limit."""
        limits = SafetyLimits(max_fm_deviation_hz=10e6)
        validator = SafetyValidator(limits)
        validator.validate_deviation(10e6)
        with pytest.raises(ValueError):
            validator.validate_deviation(11e6)
