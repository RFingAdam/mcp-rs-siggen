"""Tests for security hardening: SCPI sanitization, path validation, and raw SCPI guards."""

import logging
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch  # noqa: F401

import pytest

from rs_siggen_mcp.safety.validators import sanitize_scpi_param, validate_safe_path

# =============================================================================
# Issue 1: SCPI Parameter Sanitization Tests
# =============================================================================


class TestSanitizeScpiParam:
    """Test sanitize_scpi_param() rejects SCPI injection payloads."""

    def test_clean_string_passes(self):
        """Test that clean string parameters pass through unchanged."""
        assert sanitize_scpi_param("test_waveform.wfm") == "test_waveform.wfm"
        assert sanitize_scpi_param("/var/user/waveform") == "/var/user/waveform"
        assert sanitize_scpi_param("FDD") == "FDD"
        assert sanitize_scpi_param("802.11ax") == "802.11ax"
        assert sanitize_scpi_param("LE") == "LE"

    def test_semicolon_injection_rejected(self):
        """Test that semicolons (SCPI command separators) are rejected."""
        with pytest.raises(ValueError, match="SCPI injection detected"):
            sanitize_scpi_param(";*RST")

    def test_semicolon_mid_string_rejected(self):
        """Test semicolon in the middle of a command is rejected."""
        with pytest.raises(ValueError, match="SCPI injection detected"):
            sanitize_scpi_param("SOURce1:FREQuency 1e9;*RST")

    def test_newline_injection_rejected(self):
        """Test that newline characters are rejected."""
        with pytest.raises(ValueError, match="SCPI injection detected"):
            sanitize_scpi_param("test\n*RST")

    def test_carriage_return_injection_rejected(self):
        """Test that carriage return characters are rejected."""
        with pytest.raises(ValueError, match="SCPI injection detected"):
            sanitize_scpi_param("test\r*RST")

    def test_crlf_injection_rejected(self):
        """Test that CRLF sequences are rejected."""
        with pytest.raises(ValueError, match="SCPI injection detected"):
            sanitize_scpi_param("test\r\n*RST")

    def test_star_at_start_rejected(self):
        """Test that leading * is rejected (could trigger *RST, *CLS, etc.)."""
        with pytest.raises(ValueError, match="SCPI injection detected.*\\*"):
            sanitize_scpi_param("*RST")

    def test_star_with_leading_space_rejected(self):
        """Test that * with leading whitespace is also rejected."""
        with pytest.raises(ValueError, match="SCPI injection detected.*\\*"):
            sanitize_scpi_param("  *RST")

    def test_star_in_middle_allowed(self):
        """Test that * in the middle of a string is allowed (e.g., file globs)."""
        assert sanitize_scpi_param("test*waveform") == "test*waveform"

    def test_empty_string_passes(self):
        """Test that empty string passes validation."""
        assert sanitize_scpi_param("") == ""

    def test_numeric_string_passes(self):
        """Test that numeric strings pass."""
        assert sanitize_scpi_param("1000000") == "1000000"
        assert sanitize_scpi_param("-10.5") == "-10.5"

    def test_non_string_rejected(self):
        """Test that non-string types are rejected."""
        with pytest.raises(ValueError, match="Expected string parameter"):
            sanitize_scpi_param(123)  # type: ignore

    def test_complex_injection_payload(self):
        """Test complex injection payloads are caught."""
        # Command separator + reset
        with pytest.raises(ValueError):
            sanitize_scpi_param("normal;*RST;*CLS")

        # Newline-based injection
        with pytest.raises(ValueError):
            sanitize_scpi_param("value\n*RST\n*CLS")

    def test_rst_without_star_passes(self):
        """Test that 'RST' without leading star passes (not a common command)."""
        assert sanitize_scpi_param("RST") == "RST"

    def test_path_with_spaces_passes(self):
        """Test paths with spaces pass validation."""
        assert sanitize_scpi_param("/var/user/my waveform.wfm") == "/var/user/my waveform.wfm"


# =============================================================================
# Issue 2: File Path Validation Tests
# =============================================================================


class TestValidateSafePath:
    """Test validate_safe_path() against traversal and symlink attacks."""

    def setup_method(self):
        """Set up temporary directory for path tests."""
        self.tmpdir = tempfile.mkdtemp()
        self.base_dir = Path(self.tmpdir) / "siggen_states"
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_relative_path_within_base(self):
        """Test that relative paths within base_dir are accepted."""
        result = validate_safe_path("test_state.json", self.base_dir)
        assert result == self.base_dir / "test_state.json"

    def test_nested_relative_path(self):
        """Test that nested relative paths within base_dir are accepted."""
        result = validate_safe_path("subdir/test_state.json", self.base_dir)
        assert result == self.base_dir / "subdir" / "test_state.json"

    def test_absolute_path_within_base(self):
        """Test that absolute paths within base_dir are accepted."""
        abs_path = self.base_dir / "test_state.json"
        result = validate_safe_path(str(abs_path), self.base_dir)
        assert result == abs_path

    def test_traversal_with_dotdot_rejected(self):
        """Test that ../ traversal is rejected."""
        with pytest.raises(ValueError, match="Path traversal detected"):
            validate_safe_path("../../../etc/passwd", self.base_dir)

    def test_traversal_mid_path_rejected(self):
        """Test that ../ in the middle of a path is rejected."""
        with pytest.raises(ValueError, match="Path traversal detected"):
            validate_safe_path("subdir/../../etc/passwd", self.base_dir)

    def test_absolute_path_outside_base_rejected(self):
        """Test that absolute paths outside base_dir are rejected."""
        with pytest.raises(ValueError, match="Path traversal detected"):
            validate_safe_path("/etc/passwd", self.base_dir)

    def test_absolute_path_different_tree_rejected(self):
        """Test that absolute paths in a different tree are rejected."""
        with pytest.raises(ValueError, match="Path traversal detected"):
            validate_safe_path("/tmp/evil_state.json", self.base_dir)

    def test_symlink_inside_base_allowed(self):
        """Test that symlinks pointing within base_dir are allowed."""
        # Create a real file and a symlink pointing to it
        real_file = self.base_dir / "real_state.json"
        real_file.write_text('{"test": true}')
        link_path = self.base_dir / "link_state.json"
        link_path.symlink_to(real_file)

        result = validate_safe_path("link_state.json", self.base_dir)
        assert result.is_relative_to(self.base_dir)

    def test_symlink_outside_base_rejected(self):
        """Test that symlinks pointing outside base_dir are rejected."""
        # Create a file outside the base directory
        outside_file = Path(self.tmpdir) / "outside.json"
        outside_file.write_text('{"evil": true}')

        # Create a symlink inside base_dir pointing outside
        link_path = self.base_dir / "escape_link.json"
        link_path.symlink_to(outside_file)

        with pytest.raises(ValueError, match="(Path traversal|Symlink attack) detected"):
            validate_safe_path("escape_link.json", self.base_dir)

    def test_double_dot_at_boundary(self):
        """Test that exactly one ../ (reaching parent of base) is rejected."""
        with pytest.raises(ValueError, match="Path traversal detected"):
            validate_safe_path("..", self.base_dir)

    def test_path_object_input(self):
        """Test that Path objects work as input."""
        result = validate_safe_path(
            Path("test.json"), self.base_dir
        )
        assert result == self.base_dir / "test.json"

    def test_base_dir_itself(self):
        """Test that the base_dir itself is accepted."""
        result = validate_safe_path(".", self.base_dir)
        assert result == self.base_dir.resolve()

    def test_encoded_traversal_rejected(self):
        """Test that traversal via redundant paths is rejected after resolve."""
        with pytest.raises(ValueError, match="Path traversal detected"):
            validate_safe_path(
                "subdir/../../../etc/passwd", self.base_dir
            )


# =============================================================================
# Issue 3: Raw SCPI Guard and Logging Tests
# =============================================================================


class TestRawScpiGuard:
    """Test the allow_raw_scpi config guard on raw SCPI tools."""

    @pytest.fixture
    def mock_siggen(self):
        """Create a mock signal generator for testing."""
        mock = AsyncMock()
        mock.is_connected = True
        mock.address = "192.168.1.100:5025"
        mock.info = MagicMock()
        mock.info.to_dict.return_value = {"model": "SMW200A"}
        return mock

    @pytest.mark.asyncio
    async def test_raw_scpi_send_blocked_when_disabled(self, mock_siggen):
        """Test that raw SCPI send returns error when disabled."""
        from rs_siggen_mcp.tools import handle_tool

        with patch("rs_siggen_mcp.tools.get_settings") as mock_settings, \
             patch("rs_siggen_mcp.tools._get_siggen", return_value=mock_siggen):
            settings = MagicMock()
            settings.allow_raw_scpi = False
            settings.default_host = "192.168.1.100"
            settings.default_port = 5025
            mock_settings.return_value = settings

            result = await handle_tool("siggen_scpi_send", {"command": "*RST"})
            assert len(result) == 1
            assert "disabled" in result[0].text.lower() or "SIGGEN_ALLOW_RAW_SCPI" in result[0].text

    @pytest.mark.asyncio
    async def test_raw_scpi_query_blocked_when_disabled(self, mock_siggen):
        """Test that raw SCPI query returns error when disabled."""
        from rs_siggen_mcp.tools import handle_tool

        with patch("rs_siggen_mcp.tools.get_settings") as mock_settings, \
             patch("rs_siggen_mcp.tools._get_siggen", return_value=mock_siggen):
            settings = MagicMock()
            settings.allow_raw_scpi = False
            settings.default_host = "192.168.1.100"
            settings.default_port = 5025
            mock_settings.return_value = settings

            result = await handle_tool("siggen_scpi_query", {"command": "*IDN?"})
            assert len(result) == 1
            assert "disabled" in result[0].text.lower() or "SIGGEN_ALLOW_RAW_SCPI" in result[0].text

    @pytest.mark.asyncio
    async def test_raw_scpi_send_allowed_when_enabled(self, mock_siggen):
        """Test that raw SCPI send works when enabled."""
        from rs_siggen_mcp.tools import handle_tool

        with patch("rs_siggen_mcp.tools.get_settings") as mock_settings, \
             patch("rs_siggen_mcp.tools._get_siggen", return_value=mock_siggen):
            settings = MagicMock()
            settings.allow_raw_scpi = True
            settings.default_host = "192.168.1.100"
            settings.default_port = 5025
            mock_settings.return_value = settings

            result = await handle_tool("siggen_scpi_send", {"command": "SOURce1:FREQuency 1e9"})
            assert len(result) == 1
            assert "sent" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_raw_scpi_query_allowed_when_enabled(self, mock_siggen):
        """Test that raw SCPI query works when enabled."""
        from rs_siggen_mcp.tools import handle_tool

        mock_siggen.scpi_query.return_value = "Rohde&Schwarz,SMW200A,123,4.30"
        with patch("rs_siggen_mcp.tools.get_settings") as mock_settings, \
             patch("rs_siggen_mcp.tools._get_siggen", return_value=mock_siggen):
            settings = MagicMock()
            settings.allow_raw_scpi = True
            settings.default_host = "192.168.1.100"
            settings.default_port = 5025
            mock_settings.return_value = settings

            result = await handle_tool("siggen_scpi_query", {"command": "*IDN?"})
            assert len(result) == 1
            assert "response" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_raw_scpi_send_logs_warning(self, mock_siggen, caplog):
        """Test that raw SCPI send logs a WARNING."""
        from rs_siggen_mcp.tools import handle_tool

        with patch("rs_siggen_mcp.tools.get_settings") as mock_settings, \
             patch("rs_siggen_mcp.tools._get_siggen", return_value=mock_siggen), \
             caplog.at_level(logging.WARNING, logger="rs_siggen_mcp.tools"):
            settings = MagicMock()
            settings.allow_raw_scpi = True
            settings.default_host = "192.168.1.100"
            settings.default_port = 5025
            mock_settings.return_value = settings

            await handle_tool("siggen_scpi_send", {"command": "*RST"})

            assert any(
                "Raw SCPI send" in record.message and "*RST" in record.message
                for record in caplog.records
            ), f"Expected WARNING log with command, got: {[r.message for r in caplog.records]}"

    @pytest.mark.asyncio
    async def test_raw_scpi_query_logs_warning(self, mock_siggen, caplog):
        """Test that raw SCPI query logs a WARNING."""
        from rs_siggen_mcp.tools import handle_tool

        mock_siggen.scpi_query.return_value = "response"
        with patch("rs_siggen_mcp.tools.get_settings") as mock_settings, \
             patch("rs_siggen_mcp.tools._get_siggen", return_value=mock_siggen), \
             caplog.at_level(logging.WARNING, logger="rs_siggen_mcp.tools"):
            settings = MagicMock()
            settings.allow_raw_scpi = True
            settings.default_host = "192.168.1.100"
            settings.default_port = 5025
            mock_settings.return_value = settings

            await handle_tool("siggen_scpi_query", {"command": "*IDN?"})

            assert any(
                "Raw SCPI query" in record.message and "*IDN?" in record.message
                for record in caplog.records
            ), f"Expected WARNING log with command, got: {[r.message for r in caplog.records]}"


class TestAllowRawScpiConfig:
    """Test the allow_raw_scpi config option."""

    def test_default_is_true(self):
        """Test that allow_raw_scpi defaults to True for backwards compatibility."""
        from rs_siggen_mcp.config import SiggenSettings

        settings = SiggenSettings()
        assert settings.allow_raw_scpi is True

    def test_can_be_set_to_false(self):
        """Test that allow_raw_scpi can be set to False."""
        from rs_siggen_mcp.config import SiggenSettings

        settings = SiggenSettings(allow_raw_scpi=False)
        assert settings.allow_raw_scpi is False

    def test_env_var_override(self, monkeypatch):
        """Test that SIGGEN_ALLOW_RAW_SCPI env var overrides default."""
        from rs_siggen_mcp.config import SiggenSettings

        monkeypatch.setenv("SIGGEN_ALLOW_RAW_SCPI", "false")
        settings = SiggenSettings()
        assert settings.allow_raw_scpi is False


# =============================================================================
# Integration-style tests: sanitizer applied in tools.py
# =============================================================================


class TestScpiSanitizationInTools:
    """Test that SCPI sanitization is applied in tool handlers."""

    @pytest.fixture
    def mock_siggen(self):
        """Create a mock signal generator."""
        mock = AsyncMock()
        mock.is_connected = True
        mock.address = "192.168.1.100:5025"
        mock.info = MagicMock()
        mock.info.to_dict.return_value = {"model": "SMW200A"}
        return mock

    @pytest.mark.asyncio
    async def test_list_waveforms_injection_blocked(self, mock_siggen):
        """Test that SCPI injection in directory param is blocked."""
        from rs_siggen_mcp.tools import handle_tool

        with patch("rs_siggen_mcp.tools._get_siggen", return_value=mock_siggen), \
             patch("rs_siggen_mcp.tools.get_settings") as mock_settings:
            settings = MagicMock()
            settings.default_host = "192.168.1.100"
            settings.default_port = 5025
            mock_settings.return_value = settings

            result = await handle_tool(
                "siggen_list_waveforms",
                {"directory": "/var/user;*RST"},
            )
            # Should return error due to semicolon
            assert len(result) == 1
            assert "error" in result[0].text.lower() or "injection" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_configure_bluetooth_injection_blocked(self, mock_siggen):
        """Test that SCPI injection in bluetooth mode is blocked."""
        from rs_siggen_mcp.tools import handle_tool

        with patch("rs_siggen_mcp.tools._get_siggen", return_value=mock_siggen), \
             patch("rs_siggen_mcp.tools.get_settings") as mock_settings:
            settings = MagicMock()
            settings.default_host = "192.168.1.100"
            settings.default_port = 5025
            mock_settings.return_value = settings

            result = await handle_tool(
                "siggen_configure_bluetooth",
                {"mode": "LE;*RST"},
            )
            assert len(result) == 1
            assert "error" in result[0].text.lower() or "injection" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_configure_lte_duplex_injection_blocked(self, mock_siggen):
        """Test that SCPI injection in LTE duplex_mode is blocked."""
        from rs_siggen_mcp.tools import handle_tool

        with patch("rs_siggen_mcp.tools._get_siggen", return_value=mock_siggen), \
             patch("rs_siggen_mcp.tools.get_settings") as mock_settings:
            settings = MagicMock()
            settings.default_host = "192.168.1.100"
            settings.default_port = 5025
            mock_settings.return_value = settings

            result = await handle_tool(
                "siggen_configure_lte",
                {"bandwidth_mhz": 10, "duplex_mode": "FDD\n*RST"},
            )
            assert len(result) == 1
            assert "error" in result[0].text.lower() or "injection" in result[0].text.lower()


class TestPathValidationInTools:
    """Test that path validation is applied in tool handlers for state save/load."""

    @pytest.fixture
    def mock_siggen(self):
        """Create a mock signal generator."""
        mock = AsyncMock()
        mock.is_connected = True
        mock.address = "192.168.1.100:5025"
        mock.info = MagicMock()
        mock.info.to_dict.return_value = {"model": "SMW200A"}
        return mock

    @pytest.mark.asyncio
    async def test_save_state_traversal_blocked(self, mock_siggen):
        """Test that path traversal in save_state filepath is blocked."""
        from rs_siggen_mcp.tools import handle_tool

        with patch("rs_siggen_mcp.tools._get_siggen", return_value=mock_siggen), \
             patch("rs_siggen_mcp.tools.get_settings") as mock_settings:
            settings = MagicMock()
            settings.default_host = "192.168.1.100"
            settings.default_port = 5025
            mock_settings.return_value = settings

            result = await handle_tool(
                "siggen_save_state",
                {"filepath": "../../../etc/evil.json"},
            )
            assert len(result) == 1
            assert "error" in result[0].text.lower() or "traversal" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_load_state_traversal_blocked(self, mock_siggen):
        """Test that path traversal in load_state filepath is blocked."""
        from rs_siggen_mcp.tools import handle_tool

        with patch("rs_siggen_mcp.tools._get_siggen", return_value=mock_siggen), \
             patch("rs_siggen_mcp.tools.get_settings") as mock_settings:
            settings = MagicMock()
            settings.default_host = "192.168.1.100"
            settings.default_port = 5025
            mock_settings.return_value = settings

            result = await handle_tool(
                "siggen_load_state",
                {"filepath": "/etc/passwd"},
            )
            assert len(result) == 1
            assert "error" in result[0].text.lower() or "traversal" in result[0].text.lower()


class TestDriverSanitization:
    """Test that the driver sanitizes string parameters."""

    @pytest.mark.asyncio
    async def test_load_waveform_injection_blocked(self, mock_scpi_socket):
        """Test that SCPI injection in waveform path is blocked by driver."""
        from rs_siggen_mcp.driver.siggen_driver import RSSignalGeneratorDriver

        driver = RSSignalGeneratorDriver.__new__(RSSignalGeneratorDriver)
        driver._scpi = mock_scpi_socket
        driver._safety = MagicMock()
        driver._rf_output_on = False
        driver._frequency_hz = None
        driver._power_dbm = None
        driver._info = MagicMock()
        driver._info.family.has_arb_generator = True

        with pytest.raises(ValueError, match="SCPI injection detected"):
            await driver.load_waveform("/var/user/wave;*RST")

    @pytest.mark.asyncio
    async def test_load_waveform_clean_path_passes(self, mock_scpi_socket):
        """Test that clean waveform paths work."""
        from rs_siggen_mcp.driver.siggen_driver import RSSignalGeneratorDriver

        driver = RSSignalGeneratorDriver.__new__(RSSignalGeneratorDriver)
        driver._scpi = mock_scpi_socket
        driver._safety = MagicMock()
        driver._rf_output_on = False
        driver._frequency_hz = None
        driver._power_dbm = None
        driver._info = MagicMock()
        driver._info.family.has_arb_generator = True

        await driver.load_waveform("/var/user/waveform/test.wv")
        mock_scpi_socket.send.assert_called_once_with(
            "SOURce1:BB:ARBitrary:WAVeform:SELect '/var/user/waveform/test.wv'"
        )
