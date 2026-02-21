"""Tests for MCP tool definitions and handlers."""


from rs_siggen_mcp.tools import get_tools


class TestGetTools:
    """Test tool definitions."""

    def test_returns_list(self):
        """Test that get_tools returns a list."""
        tools = get_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0

    def test_tool_count(self):
        """Test expected number of tools."""
        tools = get_tools()
        # We defined ~45 tools
        assert len(tools) >= 40

    def test_all_tools_have_names(self):
        """Test all tools have names."""
        tools = get_tools()
        for tool in tools:
            assert tool.name is not None
            assert len(tool.name) > 0

    def test_all_tools_have_descriptions(self):
        """Test all tools have descriptions."""
        tools = get_tools()
        for tool in tools:
            assert tool.description is not None
            assert len(tool.description) > 0

    def test_all_tools_have_schemas(self):
        """Test all tools have input schemas."""
        tools = get_tools()
        for tool in tools:
            assert tool.inputSchema is not None
            assert tool.inputSchema["type"] == "object"

    def test_tool_names_prefixed(self):
        """Test all tool names start with siggen_."""
        tools = get_tools()
        for tool in tools:
            assert tool.name.startswith("siggen_"), f"Tool {tool.name} missing siggen_ prefix"

    def test_unique_tool_names(self):
        """Test all tool names are unique."""
        tools = get_tools()
        names = [t.name for t in tools]
        assert len(names) == len(set(names)), "Duplicate tool names found"

    def test_connection_tools_exist(self):
        """Test connection tools are defined."""
        tools = get_tools()
        names = {t.name for t in tools}
        assert "siggen_discover" in names
        assert "siggen_connect" in names
        assert "siggen_disconnect" in names
        assert "siggen_identify" in names
        assert "siggen_get_status" in names
        assert "siggen_get_model_info" in names

    def test_rf_tools_exist(self):
        """Test RF output tools are defined."""
        tools = get_tools()
        names = {t.name for t in tools}
        assert "siggen_set_frequency" in names
        assert "siggen_set_power" in names
        assert "siggen_output_on" in names
        assert "siggen_output_off" in names
        assert "siggen_set_phase" in names

    def test_modulation_tools_exist(self):
        """Test modulation tools are defined."""
        tools = get_tools()
        names = {t.name for t in tools}
        assert "siggen_configure_am" in names
        assert "siggen_configure_fm" in names
        assert "siggen_configure_pm" in names
        assert "siggen_configure_pulse" in names
        assert "siggen_modulation_all_off" in names

    def test_iq_tools_exist(self):
        """Test IQ tools are defined."""
        tools = get_tools()
        names = {t.name for t in tools}
        assert "siggen_iq_on" in names
        assert "siggen_iq_off" in names
        assert "siggen_configure_iq_impairments" in names

    def test_arb_tools_exist(self):
        """Test ARB tools are defined."""
        tools = get_tools()
        names = {t.name for t in tools}
        assert "siggen_load_waveform" in names
        assert "siggen_arb_on" in names
        assert "siggen_arb_off" in names
        assert "siggen_set_arb_clock" in names
        assert "siggen_list_waveforms" in names

    def test_digital_standard_tools_exist(self):
        """Test digital standard tools are defined."""
        tools = get_tools()
        names = {t.name for t in tools}
        assert "siggen_configure_lte" in names
        assert "siggen_configure_5gnr" in names
        assert "siggen_configure_wlan" in names
        assert "siggen_configure_bluetooth" in names
        assert "siggen_generate_waveform" in names

    def test_sweep_tools_exist(self):
        """Test sweep tools are defined."""
        tools = get_tools()
        names = {t.name for t in tools}
        assert "siggen_configure_freq_sweep" in names
        assert "siggen_configure_power_sweep" in names
        assert "siggen_configure_list_mode" in names

    def test_reference_tools_exist(self):
        """Test reference tools are defined."""
        tools = get_tools()
        names = {t.name for t in tools}
        assert "siggen_set_reference_source" in names
        assert "siggen_get_reference_status" in names

    def test_calibration_tools_exist(self):
        """Test calibration tools are defined."""
        tools = get_tools()
        names = {t.name for t in tools}
        assert "siggen_run_calibration" in names
        assert "siggen_get_calibration_status" in names

    def test_scpi_tools_exist(self):
        """Test raw SCPI tools are defined."""
        tools = get_tools()
        names = {t.name for t in tools}
        assert "siggen_scpi_send" in names
        assert "siggen_scpi_query" in names
        assert "siggen_reset" in names
        assert "siggen_preset" in names

    def test_template_tools_exist(self):
        """Test template tools are defined."""
        tools = get_tools()
        names = {t.name for t in tools}
        assert "siggen_list_templates" in names
        assert "siggen_load_template" in names
        assert "siggen_apply_template" in names

    def test_state_tools_exist(self):
        """Test state tools are defined."""
        tools = get_tools()
        names = {t.name for t in tools}
        assert "siggen_save_state" in names
        assert "siggen_load_state" in names
        assert "siggen_get_full_state" in names

    def test_required_fields_set_frequency(self):
        """Test siggen_set_frequency has required fields."""
        tools = get_tools()
        tool = next(t for t in tools if t.name == "siggen_set_frequency")
        assert "required" in tool.inputSchema
        assert "frequency_hz" in tool.inputSchema["required"]

    def test_required_fields_set_power(self):
        """Test siggen_set_power has required fields."""
        tools = get_tools()
        tool = next(t for t in tools if t.name == "siggen_set_power")
        assert "required" in tool.inputSchema
        assert "power_dbm" in tool.inputSchema["required"]

    def test_required_fields_scpi_send(self):
        """Test siggen_scpi_send has required fields."""
        tools = get_tools()
        tool = next(t for t in tools if t.name == "siggen_scpi_send")
        assert "required" in tool.inputSchema
        assert "command" in tool.inputSchema["required"]
