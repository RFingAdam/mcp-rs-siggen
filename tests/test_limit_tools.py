"""Tests for limit line MCP tools (Issue #14)."""

import json
import tempfile
from pathlib import Path

import pytest

from rs_siggen_mcp.tools import handle_tool


class TestLimitCreate:
    """Test siggen_limit_create tool."""

    @pytest.fixture(autouse=True)
    def clear_limits(self):
        """Clear limit manager before each test."""
        from rs_siggen_mcp.tools._common import _limit_manager
        _limit_manager.clear_limits()
        yield
        _limit_manager.clear_limits()

    @pytest.mark.asyncio
    async def test_create_flat_limit(self):
        """Test creating a flat limit line."""
        result = await handle_tool("siggen_limit_create", {
            "name": "power_flatness",
            "start_freq_hz": 1e9,
            "stop_freq_hz": 6e9,
            "max_db": -9.0,
            "min_db": -11.0,
        })
        assert result.isError is False
        data = json.loads(result.content[0].text)
        assert data["status"] == "limit_created"
        assert data["name"] == "power_flatness"
        assert data["segments"] == 1

    @pytest.mark.asyncio
    async def test_create_segmented_limit(self):
        """Test creating a segmented limit line."""
        result = await handle_tool("siggen_limit_create", {
            "name": "cispr_25",
            "segments": [
                {"start_freq_hz": 150e3, "stop_freq_hz": 30e6, "max_db": 40.0},
                {"start_freq_hz": 30e6, "stop_freq_hz": 1e9, "max_db": 30.0},
            ],
            "description": "CISPR 25 limits",
        })
        assert result.isError is False
        data = json.loads(result.content[0].text)
        assert data["status"] == "limit_created"
        assert data["segments"] == 2


class TestLimitList:
    """Test siggen_limit_list tool."""

    @pytest.fixture(autouse=True)
    def clear_limits(self):
        """Clear limit manager before each test."""
        from rs_siggen_mcp.tools._common import _limit_manager
        _limit_manager.clear_limits()
        yield
        _limit_manager.clear_limits()

    @pytest.mark.asyncio
    async def test_list_empty(self):
        """Test listing when no limits are defined."""
        result = await handle_tool("siggen_limit_list", {})
        assert result.isError is False
        data = json.loads(result.content[0].text)
        assert data["count"] == 0

    @pytest.mark.asyncio
    async def test_list_with_limits(self):
        """Test listing after creating limits."""
        await handle_tool("siggen_limit_create", {
            "name": "limit_a",
            "start_freq_hz": 1e9,
            "stop_freq_hz": 6e9,
            "max_db": -5.0,
        })
        await handle_tool("siggen_limit_create", {
            "name": "limit_b",
            "start_freq_hz": 1e9,
            "stop_freq_hz": 6e9,
            "max_db": -10.0,
        })

        result = await handle_tool("siggen_limit_list", {})
        assert result.isError is False
        data = json.loads(result.content[0].text)
        assert data["count"] == 2


class TestLimitRemove:
    """Test siggen_limit_remove tool."""

    @pytest.fixture(autouse=True)
    def clear_limits(self):
        """Clear limit manager before each test."""
        from rs_siggen_mcp.tools._common import _limit_manager
        _limit_manager.clear_limits()
        yield
        _limit_manager.clear_limits()

    @pytest.mark.asyncio
    async def test_remove_existing(self):
        """Test removing an existing limit."""
        await handle_tool("siggen_limit_create", {
            "name": "to_remove",
            "start_freq_hz": 1e9,
            "stop_freq_hz": 6e9,
            "max_db": -5.0,
        })

        result = await handle_tool("siggen_limit_remove", {"name": "to_remove"})
        assert result.isError is False
        data = json.loads(result.content[0].text)
        assert data["status"] == "removed"

        # Verify removed
        list_result = await handle_tool("siggen_limit_list", {})
        list_data = json.loads(list_result.content[0].text)
        assert list_data["count"] == 0

    @pytest.mark.asyncio
    async def test_remove_nonexistent(self):
        """Test removing a non-existent limit."""
        result = await handle_tool("siggen_limit_remove", {"name": "does_not_exist"})
        assert result.isError is False
        data = json.loads(result.content[0].text)
        assert data["status"] == "not_found"


class TestLimitCheck:
    """Test siggen_limit_check tool."""

    @pytest.fixture(autouse=True)
    def clear_limits(self):
        """Clear limit manager before each test."""
        from rs_siggen_mcp.tools._common import _limit_manager
        _limit_manager.clear_limits()
        yield
        _limit_manager.clear_limits()

    @pytest.mark.asyncio
    async def test_check_pass(self):
        """Test checking measurements that pass."""
        await handle_tool("siggen_limit_create", {
            "name": "test_limit",
            "start_freq_hz": 1e9,
            "stop_freq_hz": 6e9,
            "max_db": 0.0,
            "min_db": -20.0,
        })

        result = await handle_tool("siggen_limit_check", {
            "name": "test_limit",
            "frequencies": [1e9, 2e9, 3e9],
            "values_db": [-5.0, -10.0, -15.0],
        })
        assert result.isError is False
        data = json.loads(result.content[0].text)
        assert data["passed"] is True
        assert data["failed_points"] == 0

    @pytest.mark.asyncio
    async def test_check_fail(self):
        """Test checking measurements that fail."""
        await handle_tool("siggen_limit_create", {
            "name": "tight_limit",
            "start_freq_hz": 1e9,
            "stop_freq_hz": 6e9,
            "max_db": -10.0,
        })

        result = await handle_tool("siggen_limit_check", {
            "name": "tight_limit",
            "frequencies": [1e9, 2e9, 3e9],
            "values_db": [-5.0, -15.0, -3.0],
        })
        assert result.isError is False
        data = json.loads(result.content[0].text)
        assert data["passed"] is False
        assert data["failed_points"] == 2

    @pytest.mark.asyncio
    async def test_check_nonexistent_limit(self):
        """Test checking against a non-existent limit."""
        result = await handle_tool("siggen_limit_check", {
            "name": "missing",
            "frequencies": [1e9],
            "values_db": [-10.0],
        })
        assert result.isError is True
        assert "not found" in result.content[0].text.lower()


class TestLimitGetStatus:
    """Test siggen_limit_get_status tool."""

    @pytest.fixture(autouse=True)
    def clear_limits(self):
        """Clear limit manager before each test."""
        from rs_siggen_mcp.tools._common import _limit_manager
        _limit_manager.clear_limits()
        yield
        _limit_manager.clear_limits()

    @pytest.mark.asyncio
    async def test_overall_status_all_pass(self):
        """Test overall status when all limits pass."""
        await handle_tool("siggen_limit_create", {
            "name": "limit_1",
            "start_freq_hz": 1e9,
            "stop_freq_hz": 6e9,
            "max_db": 0.0,
        })
        await handle_tool("siggen_limit_create", {
            "name": "limit_2",
            "start_freq_hz": 1e9,
            "stop_freq_hz": 6e9,
            "min_db": -30.0,
        })

        result = await handle_tool("siggen_limit_get_status", {
            "frequencies": [1e9, 3e9, 5e9],
            "values_db": [-10.0, -15.0, -20.0],
        })
        assert result.isError is False
        data = json.loads(result.content[0].text)
        assert data["overall_passed"] is True
        assert data["limits_checked"] == 2
        assert data["limits_passed"] == 2

    @pytest.mark.asyncio
    async def test_overall_status_partial_fail(self):
        """Test overall status when one limit fails."""
        await handle_tool("siggen_limit_create", {
            "name": "loose",
            "start_freq_hz": 1e9,
            "stop_freq_hz": 6e9,
            "max_db": 0.0,
        })
        await handle_tool("siggen_limit_create", {
            "name": "tight",
            "start_freq_hz": 1e9,
            "stop_freq_hz": 6e9,
            "max_db": -20.0,
        })

        result = await handle_tool("siggen_limit_get_status", {
            "frequencies": [1e9, 3e9],
            "values_db": [-10.0, -15.0],
        })
        assert result.isError is False
        data = json.loads(result.content[0].text)
        assert data["overall_passed"] is False
        assert data["limits_failed"] == 1


class TestLimitSaveLoad:
    """Test siggen_limit_save and siggen_limit_load tools."""

    @pytest.fixture(autouse=True)
    def clear_limits(self):
        """Clear limit manager before each test."""
        from rs_siggen_mcp.tools._common import _limit_manager
        _limit_manager.clear_limits()
        yield
        _limit_manager.clear_limits()

    @pytest.mark.asyncio
    async def test_save_and_load(self):
        """Test saving and loading a limit line."""
        from rs_siggen_mcp.tools._common import _state_manager

        with tempfile.TemporaryDirectory() as tmpdir:
            _state_manager.state_directory = Path(tmpdir)

            # Create a limit
            await handle_tool("siggen_limit_create", {
                "name": "saved_limit",
                "start_freq_hz": 1e9,
                "stop_freq_hz": 6e9,
                "max_db": -5.0,
                "min_db": -25.0,
            })

            # Save it
            save_result = await handle_tool("siggen_limit_save", {
                "name": "saved_limit",
                "filepath": "test_limit.json",
            })
            assert save_result.isError is False

            # Remove from manager
            await handle_tool("siggen_limit_remove", {"name": "saved_limit"})

            # Load it back
            load_result = await handle_tool("siggen_limit_load", {
                "filepath": "test_limit.json",
            })
            assert load_result.isError is False
            load_data = json.loads(load_result.content[0].text)
            assert load_data["name"] == "saved_limit"

            # Verify it works
            check_result = await handle_tool("siggen_limit_check", {
                "name": "saved_limit",
                "frequencies": [3e9],
                "values_db": [-10.0],
            })
            assert check_result.isError is False
            check_data = json.loads(check_result.content[0].text)
            assert check_data["passed"] is True

    @pytest.mark.asyncio
    async def test_save_nonexistent_limit(self):
        """Test saving a non-existent limit."""
        from rs_siggen_mcp.tools._common import _state_manager

        with tempfile.TemporaryDirectory() as tmpdir:
            _state_manager.state_directory = Path(tmpdir)

            result = await handle_tool("siggen_limit_save", {
                "name": "missing",
                "filepath": "test.json",
            })
            assert result.isError is True
            assert "not found" in result.content[0].text.lower()

    @pytest.mark.asyncio
    async def test_save_path_traversal_blocked(self):
        """Test that path traversal in save is blocked."""
        from rs_siggen_mcp.limits import LimitLine
        from rs_siggen_mcp.tools._common import _limit_manager, _state_manager

        with tempfile.TemporaryDirectory() as tmpdir:
            _state_manager.state_directory = Path(tmpdir)
            _limit_manager.add_limit(
                LimitLine.create_flat_limit("test", 1e9, 6e9, max_db=0.0)
            )

            result = await handle_tool("siggen_limit_save", {
                "name": "test",
                "filepath": "../../../etc/evil.json",
            })
            assert result.isError is True

    @pytest.mark.asyncio
    async def test_load_path_traversal_blocked(self):
        """Test that path traversal in load is blocked."""
        from rs_siggen_mcp.tools._common import _state_manager

        with tempfile.TemporaryDirectory() as tmpdir:
            _state_manager.state_directory = Path(tmpdir)

            result = await handle_tool("siggen_limit_load", {
                "filepath": "/etc/passwd",
            })
            assert result.isError is True
