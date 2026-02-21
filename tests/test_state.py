"""Tests for state management."""

import tempfile
from pathlib import Path

from rs_siggen_mcp.state import (
    InstrumentState,
    ModulationState,
    RFState,
    StateManager,
)


class TestRFState:
    """Test RFState dataclass."""

    def test_defaults(self):
        """Test default RF state."""
        rf = RFState(frequency_hz=1e9, power_dbm=-10.0)
        assert rf.output_enabled is False
        assert rf.phase_deg == 0.0

    def test_to_dict(self):
        """Test dictionary conversion."""
        rf = RFState(frequency_hz=1e9, power_dbm=-10.0, output_enabled=True)
        d = rf.to_dict()
        assert d["frequency_hz"] == 1e9
        assert d["power_dbm"] == -10.0
        assert d["output_enabled"] is True

    def test_from_dict(self):
        """Test creation from dictionary."""
        d = {"frequency_hz": 2.4e9, "power_dbm": 0.0, "output_enabled": True}
        rf = RFState.from_dict(d)
        assert rf.frequency_hz == 2.4e9
        assert rf.output_enabled is True

    def test_from_dict_defaults(self):
        """Test creation from dict with missing optional fields."""
        d = {"frequency_hz": 1e9, "power_dbm": -10.0}
        rf = RFState.from_dict(d)
        assert rf.output_enabled is False
        assert rf.phase_deg == 0.0


class TestModulationState:
    """Test ModulationState dataclass."""

    def test_defaults(self):
        """Test default modulation state."""
        mod = ModulationState()
        assert mod.am_enabled is False
        assert mod.fm_enabled is False
        assert mod.pm_enabled is False
        assert mod.pulse_enabled is False
        assert mod.iq_enabled is False

    def test_to_dict(self):
        """Test dictionary conversion."""
        mod = ModulationState(am_enabled=True, am_depth_percent=80.0)
        d = mod.to_dict()
        assert d["am_enabled"] is True
        assert d["am_depth_percent"] == 80.0
        assert d["fm_enabled"] is False

    def test_from_dict(self):
        """Test creation from dictionary."""
        d = {
            "am_enabled": True,
            "am_depth_percent": 80.0,
            "fm_enabled": True,
            "fm_deviation_hz": 75000.0,
        }
        mod = ModulationState.from_dict(d)
        assert mod.am_enabled is True
        assert mod.am_depth_percent == 80.0
        assert mod.fm_enabled is True
        assert mod.fm_deviation_hz == 75000.0

    def test_from_dict_empty(self):
        """Test creation from empty dictionary."""
        mod = ModulationState.from_dict({})
        assert mod.am_enabled is False
        assert mod.iq_enabled is False


class TestInstrumentState:
    """Test InstrumentState dataclass."""

    def setup_method(self):
        """Set up test fixtures."""
        self.rf = RFState(frequency_hz=1e9, power_dbm=-10.0, output_enabled=True)
        self.mod = ModulationState(am_enabled=True, am_depth_percent=80.0)
        self.state = InstrumentState(
            rf=self.rf,
            modulation=self.mod,
            reference_source="INTernal",
            notes="Test state",
        )

    def test_to_dict(self):
        """Test dictionary conversion."""
        d = self.state.to_dict()
        assert d["rf"]["frequency_hz"] == 1e9
        assert d["modulation"]["am_enabled"] is True
        assert d["reference_source"] == "INTernal"
        assert d["notes"] == "Test state"
        assert d["version"] == "1.0"

    def test_from_dict(self):
        """Test creation from dictionary."""
        d = self.state.to_dict()
        restored = InstrumentState.from_dict(d)
        assert restored.rf.frequency_hz == 1e9
        assert restored.rf.power_dbm == -10.0
        assert restored.modulation.am_enabled is True
        assert restored.notes == "Test state"

    def test_save_and_load(self):
        """Test save to file and load back."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            filepath = f.name

        try:
            self.state.save(filepath)
            loaded = InstrumentState.load(filepath)
            assert loaded.rf.frequency_hz == 1e9
            assert loaded.rf.power_dbm == -10.0
            assert loaded.modulation.am_enabled is True
            assert loaded.notes == "Test state"
        finally:
            Path(filepath).unlink(missing_ok=True)

    def test_get_summary(self):
        """Test state summary."""
        summary = self.state.get_summary()
        assert summary["frequency_hz"] == 1e9
        assert summary["power_dbm"] == -10.0
        assert summary["output_enabled"] is True
        assert summary["modulation"]["am"] is True
        assert summary["modulation"]["fm"] is False


class TestStateManager:
    """Test StateManager class."""

    def test_init_default(self):
        """Test default initialization."""
        mgr = StateManager()
        assert mgr.state_directory == Path("./siggen_states")

    def test_init_custom(self):
        """Test custom directory initialization."""
        mgr = StateManager("/tmp/test_states")
        assert mgr.state_directory == Path("/tmp/test_states")

    def test_list_saved_states_empty(self):
        """Test listing states when no files exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = StateManager(tmpdir)
            states = mgr.list_saved_states()
            assert states == []

    def test_list_saved_states(self):
        """Test listing saved state files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = StateManager(tmpdir)

            # Save a state
            rf = RFState(frequency_hz=1e9, power_dbm=-10.0)
            mod = ModulationState()
            state = InstrumentState(rf=rf, modulation=mod)
            state.save(Path(tmpdir) / "test_state.json")

            states = mgr.list_saved_states()
            assert len(states) == 1
            assert states[0]["filename"] == "test_state.json"
            assert "summary" in states[0]

    def test_list_saved_states_nonexistent_dir(self):
        """Test listing states from nonexistent directory."""
        mgr = StateManager("/nonexistent/path")
        states = mgr.list_saved_states()
        assert states == []
