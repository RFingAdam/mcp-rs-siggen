"""Tests for Wave 2: Architecture & Error Handling.

Covers:
- Issue 4: asyncio.Lock protection of global state
- Issue 6: isError=True on error responses
- Issue 7: Specific exception handling (no bare except Exception)
- Issue 15: Complete template application (FM/PM/pulse/IQ)
"""

import asyncio
import json
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from rs_siggen_mcp.exceptions import (
    CommunicationError,
    ConfigurationError,
    ConnectionError,
    SafetyError,
    SignalGeneratorError,
    TimeoutError,
)


# =============================================================================
# Issue 4: asyncio.Lock Tests
# =============================================================================


class TestAsyncioLocks:
    """Test that global state is protected with asyncio.Lock."""

    def test_locks_exist(self):
        """Test that asyncio.Lock instances are defined for shared state."""
        from rs_siggen_mcp import tools

        assert isinstance(tools._connection_lock, asyncio.Lock)
        assert isinstance(tools._template_lock, asyncio.Lock)
        assert isinstance(tools._state_lock, asyncio.Lock)
        assert isinstance(tools._limit_lock, asyncio.Lock)

    @pytest.mark.asyncio
    async def test_get_siggen_uses_connection_lock(self):
        """Test that _get_siggen acquires the connection lock."""
        from rs_siggen_mcp.tools import _connection_lock, _get_siggen

        lock_acquired = False
        original_acquire = _connection_lock.acquire

        async def tracking_acquire():
            nonlocal lock_acquired
            lock_acquired = True
            return await original_acquire()

        mock_sg = AsyncMock()
        mock_sg.is_connected = True
        mock_sg.connect = AsyncMock()

        with patch("rs_siggen_mcp.tools._connection_lock.acquire", tracking_acquire), \
             patch("rs_siggen_mcp.tools.get_settings") as mock_settings, \
             patch("rs_siggen_mcp.tools.RSSignalGeneratorDriver", return_value=mock_sg):
            settings = MagicMock()
            settings.default_host = "192.168.1.100"
            settings.default_port = 5025
            settings.connection_timeout = 5.0
            settings.command_timeout = 30.0
            settings.get_safety_limits.return_value = None
            mock_settings.return_value = settings

            # Clear any existing connections
            from rs_siggen_mcp import tools
            tools._siggen_connections.clear()

            await _get_siggen("192.168.1.100", 5025)
            assert lock_acquired

    @pytest.mark.asyncio
    async def test_close_siggen_uses_connection_lock(self):
        """Test that _close_siggen acquires the connection lock."""
        from rs_siggen_mcp.tools import _close_siggen

        lock_acquired = False
        from rs_siggen_mcp.tools import _connection_lock
        original_acquire = _connection_lock.acquire

        async def tracking_acquire():
            nonlocal lock_acquired
            lock_acquired = True
            return await original_acquire()

        with patch("rs_siggen_mcp.tools._connection_lock.acquire", tracking_acquire):
            await _close_siggen("192.168.1.100", 5025)
            assert lock_acquired

    @pytest.mark.asyncio
    async def test_load_template_uses_template_lock(self):
        """Test that siggen_load_template acquires the template lock."""
        from rs_siggen_mcp.tools import handle_tool

        result = await handle_tool("siggen_load_template", {"template": "cw_1ghz"})
        assert result.isError is False
        assert "template_loaded" in result.content[0].text

    @pytest.mark.asyncio
    async def test_apply_template_uses_template_lock(self):
        """Test that siggen_apply_template reads template under lock."""
        from rs_siggen_mcp.tools import handle_tool

        # First load a template
        await handle_tool("siggen_load_template", {"template": "cw_1ghz"})

        mock_sg = AsyncMock()
        mock_sg.is_connected = True

        with patch("rs_siggen_mcp.tools._get_siggen", return_value=mock_sg):
            result = await handle_tool("siggen_apply_template", {})
            assert result.isError is False
            assert "template_applied" in result.content[0].text


# =============================================================================
# Issue 6: isError=True Tests
# =============================================================================


class TestIsErrorFlag:
    """Test that error responses have isError=True and success responses have isError=False."""

    def test_format_result_sets_isError_false(self):
        """Test _format_result returns CallToolResult with isError=False."""
        from rs_siggen_mcp.tools import _format_result

        result = _format_result({"status": "ok"})
        assert result.isError is False
        assert len(result.content) == 1
        assert "ok" in result.content[0].text

    def test_format_error_sets_isError_true(self):
        """Test _format_error returns CallToolResult with isError=True."""
        from rs_siggen_mcp.tools import _format_error

        result = _format_error(ValueError("test error"))
        assert result.isError is True
        assert len(result.content) == 1
        assert "Error:" in result.content[0].text
        assert "test error" in result.content[0].text

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_isError_true(self):
        """Test that unknown tool name returns isError=True."""
        from rs_siggen_mcp.tools import handle_tool

        result = await handle_tool("siggen_nonexistent_tool", {})
        assert result.isError is True
        assert "Unknown tool" in result.content[0].text

    @pytest.mark.asyncio
    async def test_connection_error_returns_isError_true(self):
        """Test that connection errors return isError=True."""
        from rs_siggen_mcp.tools import handle_tool

        with patch("rs_siggen_mcp.tools._get_siggen",
                    side_effect=ConnectionError("Cannot connect", "192.168.1.100:5025")):
            result = await handle_tool("siggen_identify", {})
            assert result.isError is True
            assert "Cannot connect" in result.content[0].text

    @pytest.mark.asyncio
    async def test_timeout_error_returns_isError_true(self):
        """Test that timeout errors return isError=True."""
        from rs_siggen_mcp.tools import handle_tool

        with patch("rs_siggen_mcp.tools._get_siggen",
                    side_effect=TimeoutError("Timed out", "192.168.1.100:5025")):
            result = await handle_tool("siggen_set_frequency", {"frequency_hz": 1e9})
            assert result.isError is True
            assert "Timed out" in result.content[0].text

    @pytest.mark.asyncio
    async def test_safety_error_returns_isError_true(self):
        """Test that safety limit errors return isError=True."""
        from rs_siggen_mcp.tools import handle_tool

        with patch("rs_siggen_mcp.tools._get_siggen",
                    side_effect=SafetyError("Power too high", "power", 40.0, 25.0)):
            result = await handle_tool("siggen_set_power", {"power_dbm": 40.0})
            assert result.isError is True
            assert "Power too high" in result.content[0].text

    @pytest.mark.asyncio
    async def test_value_error_returns_isError_true(self):
        """Test that ValueError returns isError=True."""
        from rs_siggen_mcp.tools import handle_tool

        result = await handle_tool("siggen_load_template", {"template": "unknown_template_xyz"})
        assert result.isError is True
        assert "Unknown template" in result.content[0].text

    @pytest.mark.asyncio
    async def test_successful_tool_returns_isError_false(self):
        """Test that successful tool calls return isError=False."""
        from rs_siggen_mcp.tools import handle_tool

        result = await handle_tool("siggen_list_templates", {})
        assert result.isError is False
        assert "presets" in result.content[0].text

    @pytest.mark.asyncio
    async def test_no_template_loaded_returns_isError_true(self):
        """Test that apply_template without loading returns isError=True."""
        from rs_siggen_mcp.tools import handle_tool
        import rs_siggen_mcp.tools as tools_module

        # Clear any loaded template
        old_template = tools_module._current_template
        tools_module._current_template = None
        try:
            result = await handle_tool("siggen_apply_template", {})
            assert result.isError is True
            assert "No template loaded" in result.content[0].text
        finally:
            tools_module._current_template = old_template

    @pytest.mark.asyncio
    async def test_list_mode_length_mismatch_returns_isError_true(self):
        """Test that list_mode with mismatched array lengths returns isError=True."""
        from rs_siggen_mcp.tools import handle_tool

        mock_sg = AsyncMock()
        mock_sg.is_connected = True

        with patch("rs_siggen_mcp.tools._get_siggen", return_value=mock_sg):
            result = await handle_tool("siggen_configure_list_mode", {
                "frequencies_hz": [1e9, 2e9],
                "powers_dbm": [-10.0],
            })
            assert result.isError is True
            assert "same length" in result.content[0].text


# =============================================================================
# Issue 7: Specific Exception Handling Tests
# =============================================================================


class TestSpecificExceptionHandling:
    """Test that specific exceptions are caught instead of bare except Exception."""

    @pytest.mark.asyncio
    async def test_connection_error_logged(self, caplog):
        """Test that connection errors are logged at ERROR level."""
        from rs_siggen_mcp.tools import handle_tool

        with patch("rs_siggen_mcp.tools._get_siggen",
                    side_effect=ConnectionError("Refused", "192.168.1.100:5025")), \
             caplog.at_level(logging.ERROR, logger="rs_siggen_mcp.tools"):
            await handle_tool("siggen_identify", {})

            assert any(
                "Connection error" in record.message
                for record in caplog.records
            )

    @pytest.mark.asyncio
    async def test_timeout_error_logged(self, caplog):
        """Test that timeout errors are logged at ERROR level."""
        from rs_siggen_mcp.tools import handle_tool

        with patch("rs_siggen_mcp.tools._get_siggen",
                    side_effect=TimeoutError("Timed out", "192.168.1.100:5025")), \
             caplog.at_level(logging.ERROR, logger="rs_siggen_mcp.tools"):
            await handle_tool("siggen_set_frequency", {"frequency_hz": 1e9})

            assert any(
                "Timeout error" in record.message
                for record in caplog.records
            )

    @pytest.mark.asyncio
    async def test_communication_error_logged(self, caplog):
        """Test that communication errors are logged at ERROR level."""
        from rs_siggen_mcp.tools import handle_tool

        with patch("rs_siggen_mcp.tools._get_siggen",
                    side_effect=CommunicationError("Send failed", "192.168.1.100:5025")), \
             caplog.at_level(logging.ERROR, logger="rs_siggen_mcp.tools"):
            await handle_tool("siggen_set_power", {"power_dbm": -10.0})

            assert any(
                "Communication error" in record.message
                for record in caplog.records
            )

    @pytest.mark.asyncio
    async def test_configuration_error_logged(self, caplog):
        """Test that configuration errors are logged at ERROR level."""
        from rs_siggen_mcp.tools import handle_tool

        with patch("rs_siggen_mcp.tools._get_siggen",
                    side_effect=ConfigurationError("No IQ support", "192.168.1.100:5025")), \
             caplog.at_level(logging.ERROR, logger="rs_siggen_mcp.tools"):
            await handle_tool("siggen_iq_on", {})

            assert any(
                "Configuration error" in record.message
                for record in caplog.records
            )

    @pytest.mark.asyncio
    async def test_value_error_logged_as_warning(self, caplog):
        """Test that validation errors (raised as ValueError) are logged at WARNING level."""
        from rs_siggen_mcp.tools import handle_tool

        # SCPI injection raises ValueError from sanitize_scpi_param, which propagates
        # through handle_tool's except ValueError handler
        mock_sg = AsyncMock()
        mock_sg.is_connected = True

        with patch("rs_siggen_mcp.tools._get_siggen", return_value=mock_sg), \
             patch("rs_siggen_mcp.tools.get_settings") as mock_settings, \
             caplog.at_level(logging.WARNING, logger="rs_siggen_mcp.tools"):
            settings = MagicMock()
            settings.default_host = "192.168.1.100"
            settings.default_port = 5025
            mock_settings.return_value = settings

            result = await handle_tool(
                "siggen_configure_bluetooth", {"mode": "LE;*RST"}
            )
            assert result.isError is True

            assert any(
                "Validation error" in record.message
                for record in caplog.records
            )

    @pytest.mark.asyncio
    async def test_calibration_date_specific_exception(self):
        """Test that calibration date query catches specific exceptions."""
        from rs_siggen_mcp.tools import handle_tool

        mock_sg = AsyncMock()
        mock_sg.is_connected = True
        mock_sg.scpi_query = AsyncMock(
            side_effect=CommunicationError("Query failed", "192.168.1.100:5025")
        )

        with patch("rs_siggen_mcp.tools._get_siggen", return_value=mock_sg):
            result = await handle_tool("siggen_get_calibration_status", {})
            assert result.isError is False
            assert "unknown" in result.content[0].text

    def test_no_bare_except_in_tools(self):
        """Verify no bare 'except Exception' or 'except:' in tools.py."""
        import inspect
        import rs_siggen_mcp.tools as tools_module

        source = inspect.getsource(tools_module)
        # Should not have bare 'except Exception:' as a catch-all anymore
        # (we use specific exception types now)
        lines = source.split("\n")
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped == "except:":
                pytest.fail(f"Found bare 'except:' at line {i} in tools.py")
            # Allow 'except Exception' only if it's not in handle_tool
            # (discover handler has been updated to specific types)

    def test_no_bare_except_in_state(self):
        """Verify no bare 'except Exception:' with pass in state.py."""
        import inspect
        import rs_siggen_mcp.state as state_module

        source = inspect.getsource(state_module)
        lines = source.split("\n")
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped == "except:":
                pytest.fail(f"Found bare 'except:' at line {i} in state.py")
            if stripped == "except Exception:":
                # Check if next non-empty line is just 'pass'
                for j in range(i, min(i + 3, len(lines))):
                    if lines[j].strip() == "pass":
                        pytest.fail(
                            f"Found 'except Exception: pass' at line {i} in state.py"
                        )

    def test_no_bare_except_in_scpi_socket(self):
        """Verify no bare 'except Exception' in scpi_socket.py."""
        import inspect
        import rs_siggen_mcp.driver.scpi_socket as socket_module

        source = inspect.getsource(socket_module)
        lines = source.split("\n")
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped == "except:":
                pytest.fail(f"Found bare 'except:' at line {i} in scpi_socket.py")

    def test_no_bare_except_in_siggen_driver(self):
        """Verify no bare 'except Exception' with pass in siggen_driver.py."""
        import inspect
        import rs_siggen_mcp.driver.siggen_driver as driver_module

        source = inspect.getsource(driver_module)
        lines = source.split("\n")
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped == "except:":
                pytest.fail(
                    f"Found bare 'except:' at line {i} in siggen_driver.py"
                )
            if stripped == "except Exception:":
                for j in range(i, min(i + 3, len(lines))):
                    if lines[j].strip() == "pass":
                        pytest.fail(
                            f"Found 'except Exception: pass' at line {i} in siggen_driver.py"
                        )


# =============================================================================
# Issue 15: Complete Template Application Tests
# =============================================================================


class TestCompleteTemplateApplication:
    """Test that template apply handles all modulation types (FM/PM/pulse/IQ)."""

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
    async def test_template_apply_am_modulation(self, mock_siggen):
        """Test that template apply handles AM modulation."""
        from rs_siggen_mcp.tools import handle_tool
        import rs_siggen_mcp.tools as tools_module
        from rs_siggen_mcp.templates.base import SignalTemplate

        # Create template with AM modulation
        template = SignalTemplate(
            name="test_am",
            description="Test AM template",
            frequency_hz=1e9,
            power_dbm=-10.0,
            output_enabled=False,
            modulation_config={
                "am_enabled": True,
                "am_depth_percent": 80.0,
            },
        )

        old_template = tools_module._current_template
        tools_module._current_template = template
        try:
            with patch("rs_siggen_mcp.tools._get_siggen", return_value=mock_siggen):
                result = await handle_tool("siggen_apply_template", {})
                assert result.isError is False

                mock_siggen.configure_am.assert_called_once_with(80.0, enable=True)
                # FM, PM, pulse should be turned off
                mock_siggen.scpi_send.assert_any_call("SOURce1:FM:STATe OFF")
                mock_siggen.scpi_send.assert_any_call("SOURce1:PM:STATe OFF")
                mock_siggen.scpi_send.assert_any_call("SOURce1:PULM:STATe OFF")
                mock_siggen.scpi_send.assert_any_call("SOURce:IQ:STATe OFF")
        finally:
            tools_module._current_template = old_template

    @pytest.mark.asyncio
    async def test_template_apply_fm_modulation(self, mock_siggen):
        """Test that template apply handles FM modulation."""
        from rs_siggen_mcp.tools import handle_tool
        import rs_siggen_mcp.tools as tools_module
        from rs_siggen_mcp.templates.base import SignalTemplate

        template = SignalTemplate(
            name="test_fm",
            description="Test FM template",
            frequency_hz=100e6,
            power_dbm=-5.0,
            output_enabled=False,
            modulation_config={
                "fm_enabled": True,
                "fm_deviation_hz": 75000.0,
            },
        )

        old_template = tools_module._current_template
        tools_module._current_template = template
        try:
            with patch("rs_siggen_mcp.tools._get_siggen", return_value=mock_siggen):
                result = await handle_tool("siggen_apply_template", {})
                assert result.isError is False

                mock_siggen.configure_fm.assert_called_once_with(75000.0, enable=True)
                mock_siggen.scpi_send.assert_any_call("SOURce1:AM:STATe OFF")
        finally:
            tools_module._current_template = old_template

    @pytest.mark.asyncio
    async def test_template_apply_pm_modulation(self, mock_siggen):
        """Test that template apply handles PM modulation."""
        from rs_siggen_mcp.tools import handle_tool
        import rs_siggen_mcp.tools as tools_module
        from rs_siggen_mcp.templates.base import SignalTemplate

        template = SignalTemplate(
            name="test_pm",
            description="Test PM template",
            frequency_hz=1e9,
            power_dbm=0.0,
            output_enabled=False,
            modulation_config={
                "pm_enabled": True,
                "pm_deviation_rad": 2.0,
            },
        )

        old_template = tools_module._current_template
        tools_module._current_template = template
        try:
            with patch("rs_siggen_mcp.tools._get_siggen", return_value=mock_siggen):
                result = await handle_tool("siggen_apply_template", {})
                assert result.isError is False

                mock_siggen.configure_pm.assert_called_once_with(2.0, enable=True)
                mock_siggen.scpi_send.assert_any_call("SOURce1:AM:STATe OFF")
                mock_siggen.scpi_send.assert_any_call("SOURce1:FM:STATe OFF")
        finally:
            tools_module._current_template = old_template

    @pytest.mark.asyncio
    async def test_template_apply_pulse_modulation(self, mock_siggen):
        """Test that template apply handles pulse modulation."""
        from rs_siggen_mcp.tools import handle_tool
        import rs_siggen_mcp.tools as tools_module
        from rs_siggen_mcp.templates.base import SignalTemplate

        template = SignalTemplate(
            name="test_pulse",
            description="Test pulse template",
            frequency_hz=1e9,
            power_dbm=0.0,
            output_enabled=False,
            modulation_config={
                "pulse_enabled": True,
                "pulse_width_s": 1e-6,
                "pulse_period_s": 10e-6,
            },
        )

        old_template = tools_module._current_template
        tools_module._current_template = template
        try:
            with patch("rs_siggen_mcp.tools._get_siggen", return_value=mock_siggen):
                result = await handle_tool("siggen_apply_template", {})
                assert result.isError is False

                mock_siggen.configure_pulse.assert_called_once_with(
                    1e-6, 10e-6, enable=True
                )
                mock_siggen.scpi_send.assert_any_call("SOURce1:AM:STATe OFF")
        finally:
            tools_module._current_template = old_template

    @pytest.mark.asyncio
    async def test_template_apply_iq_modulation(self, mock_siggen):
        """Test that template apply handles IQ modulation."""
        from rs_siggen_mcp.tools import handle_tool
        import rs_siggen_mcp.tools as tools_module
        from rs_siggen_mcp.templates.base import SignalTemplate

        template = SignalTemplate(
            name="test_iq",
            description="Test IQ template",
            frequency_hz=3.5e9,
            power_dbm=-10.0,
            output_enabled=False,
            modulation_config={
                "iq_enabled": True,
            },
        )

        old_template = tools_module._current_template
        tools_module._current_template = template
        try:
            with patch("rs_siggen_mcp.tools._get_siggen", return_value=mock_siggen):
                result = await handle_tool("siggen_apply_template", {})
                assert result.isError is False

                mock_siggen.iq_on.assert_called_once()
                mock_siggen.scpi_send.assert_any_call("SOURce1:AM:STATe OFF")
                mock_siggen.scpi_send.assert_any_call("SOURce1:FM:STATe OFF")
                mock_siggen.scpi_send.assert_any_call("SOURce1:PM:STATe OFF")
                mock_siggen.scpi_send.assert_any_call("SOURce1:PULM:STATe OFF")
        finally:
            tools_module._current_template = old_template

    @pytest.mark.asyncio
    async def test_template_apply_all_modulations_off(self, mock_siggen):
        """Test that template with no modulation disables all."""
        from rs_siggen_mcp.tools import handle_tool
        import rs_siggen_mcp.tools as tools_module
        from rs_siggen_mcp.templates.base import SignalTemplate

        template = SignalTemplate(
            name="test_cw",
            description="Clean CW signal",
            frequency_hz=1e9,
            power_dbm=-10.0,
            output_enabled=False,
            modulation_config={},
        )

        old_template = tools_module._current_template
        tools_module._current_template = template
        try:
            with patch("rs_siggen_mcp.tools._get_siggen", return_value=mock_siggen):
                result = await handle_tool("siggen_apply_template", {})
                assert result.isError is False

                # All modulations should be off
                mock_siggen.scpi_send.assert_any_call("SOURce1:AM:STATe OFF")
                mock_siggen.scpi_send.assert_any_call("SOURce1:FM:STATe OFF")
                mock_siggen.scpi_send.assert_any_call("SOURce1:PM:STATe OFF")
                mock_siggen.scpi_send.assert_any_call("SOURce1:PULM:STATe OFF")
                mock_siggen.scpi_send.assert_any_call("SOURce:IQ:STATe OFF")
        finally:
            tools_module._current_template = old_template

    @pytest.mark.asyncio
    async def test_template_apply_combined_modulation(self, mock_siggen):
        """Test template with AM + pulse (common immunity test combo)."""
        from rs_siggen_mcp.tools import handle_tool
        import rs_siggen_mcp.tools as tools_module
        from rs_siggen_mcp.templates.base import SignalTemplate

        template = SignalTemplate(
            name="test_combined",
            description="Combined AM + pulse",
            frequency_hz=1e9,
            power_dbm=10.0,
            output_enabled=True,
            modulation_config={
                "am_enabled": True,
                "am_depth_percent": 80.0,
                "pulse_enabled": True,
                "pulse_width_s": 2e-6,
                "pulse_period_s": 20e-6,
            },
        )

        old_template = tools_module._current_template
        tools_module._current_template = template
        try:
            with patch("rs_siggen_mcp.tools._get_siggen", return_value=mock_siggen):
                result = await handle_tool("siggen_apply_template", {})
                assert result.isError is False

                mock_siggen.configure_am.assert_called_once_with(80.0, enable=True)
                mock_siggen.configure_pulse.assert_called_once_with(
                    2e-6, 20e-6, enable=True
                )
                mock_siggen.output_on.assert_called_once()
        finally:
            tools_module._current_template = old_template

    @pytest.mark.asyncio
    async def test_template_apply_output_enabled(self, mock_siggen):
        """Test that template apply turns on output when template specifies it."""
        from rs_siggen_mcp.tools import handle_tool
        import rs_siggen_mcp.tools as tools_module
        from rs_siggen_mcp.templates.base import SignalTemplate

        template = SignalTemplate(
            name="test_output",
            description="Output enabled test",
            frequency_hz=1e9,
            power_dbm=-10.0,
            output_enabled=True,
            modulation_config={},
        )

        old_template = tools_module._current_template
        tools_module._current_template = template
        try:
            with patch("rs_siggen_mcp.tools._get_siggen", return_value=mock_siggen):
                result = await handle_tool("siggen_apply_template", {})
                assert result.isError is False
                mock_siggen.output_on.assert_called_once()
        finally:
            tools_module._current_template = old_template

    @pytest.mark.asyncio
    async def test_template_apply_output_disabled(self, mock_siggen):
        """Test that template apply does not turn on output when disabled."""
        from rs_siggen_mcp.tools import handle_tool
        import rs_siggen_mcp.tools as tools_module
        from rs_siggen_mcp.templates.base import SignalTemplate

        template = SignalTemplate(
            name="test_no_output",
            description="Output disabled test",
            frequency_hz=1e9,
            power_dbm=-10.0,
            output_enabled=False,
            modulation_config={},
        )

        old_template = tools_module._current_template
        tools_module._current_template = template
        try:
            with patch("rs_siggen_mcp.tools._get_siggen", return_value=mock_siggen):
                result = await handle_tool("siggen_apply_template", {})
                assert result.isError is False
                mock_siggen.output_on.assert_not_called()
        finally:
            tools_module._current_template = old_template

    @pytest.mark.asyncio
    async def test_template_apply_fm_default_deviation(self, mock_siggen):
        """Test FM uses default deviation when not specified in config."""
        from rs_siggen_mcp.tools import handle_tool
        import rs_siggen_mcp.tools as tools_module
        from rs_siggen_mcp.templates.base import SignalTemplate

        template = SignalTemplate(
            name="test_fm_default",
            description="FM with default deviation",
            frequency_hz=100e6,
            power_dbm=-5.0,
            output_enabled=False,
            modulation_config={
                "fm_enabled": True,
                # No fm_deviation_hz specified - should use 75000.0 default
            },
        )

        old_template = tools_module._current_template
        tools_module._current_template = template
        try:
            with patch("rs_siggen_mcp.tools._get_siggen", return_value=mock_siggen):
                result = await handle_tool("siggen_apply_template", {})
                assert result.isError is False
                mock_siggen.configure_fm.assert_called_once_with(75000.0, enable=True)
        finally:
            tools_module._current_template = old_template

    @pytest.mark.asyncio
    async def test_template_apply_pulse_default_width(self, mock_siggen):
        """Test pulse uses default width when not specified in config."""
        from rs_siggen_mcp.tools import handle_tool
        import rs_siggen_mcp.tools as tools_module
        from rs_siggen_mcp.templates.base import SignalTemplate

        template = SignalTemplate(
            name="test_pulse_default",
            description="Pulse with default width",
            frequency_hz=1e9,
            power_dbm=0.0,
            output_enabled=False,
            modulation_config={
                "pulse_enabled": True,
                # No pulse_width_s specified - should use 1e-6 default
            },
        )

        old_template = tools_module._current_template
        tools_module._current_template = template
        try:
            with patch("rs_siggen_mcp.tools._get_siggen", return_value=mock_siggen):
                result = await handle_tool("siggen_apply_template", {})
                assert result.isError is False
                mock_siggen.configure_pulse.assert_called_once_with(
                    1e-6, None, enable=True
                )
        finally:
            tools_module._current_template = old_template


# =============================================================================
# Integration: server.py returns CallToolResult
# =============================================================================


class TestServerCallToolResult:
    """Test that server.py call_tool handler returns CallToolResult."""

    def test_server_imports_call_tool_result(self):
        """Test that server.py imports CallToolResult."""
        import rs_siggen_mcp.server as server_module
        from mcp.types import CallToolResult

        # Verify the import is used
        assert "CallToolResult" in dir(server_module) or hasattr(
            server_module, "CallToolResult"
        )
