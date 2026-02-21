# R&S Signal Generator MCP Server

[![CI](https://github.com/RFingAdam/mcp-rs-siggen/actions/workflows/ci.yml/badge.svg)](https://github.com/RFingAdam/mcp-rs-siggen/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-green.svg)](LICENSE)

MCP (Model Context Protocol) server for Rohde & Schwarz signal generator automation via TCP/IP SCPI. Control signal generators from Claude Desktop, Claude Code, or any MCP-compatible client with 53 tools across 13 categories.

## Architecture

```
┌──────────────────┐     MCP (stdio)     ┌──────────────────────────────┐
│   MCP Client     │◄──────────────────►│   rs-siggen-mcp              │
│  (Claude, etc.)  │                     │                              │
└──────────────────┘                     │  server.py                   │
                                         │    ├── tools/                │
                                         │    │   ├── _connection.py    │
                                         │    │   ├── _rf_output.py     │
                                         │    │   ├── _modulation.py    │
                                         │    │   ├── _digital_standards│
                                         │    │   ├── _sweep.py         │
                                         │    │   ├── _templates.py     │
                                         │    │   ├── _limits.py        │
                                         │    │   └── ...               │
                                         │    ├── driver.py ────────────┼──► SCPI over TCP/IP
                                         │    └── safety/validators.py  │        port 5025
                                         └──────────────────────────────┘
                                                                             ┌──────────────┐
                                                                             │  R&S Signal   │
                                                                             │  Generator    │
                                                                             └──────────────┘
```

## Supported Instruments

| Model | Type | Max Frequency | IQ Bandwidth | Key Capabilities |
|-------|------|--------------|--------------|------------------|
| **SMW200A** | Vector signal generator | 67 GHz | 2 GHz | MIMO, digital standards, ARB |
| **SMBV100B** | Vector signal generator | 6 GHz | 1 GHz | Digital standards, ARB |
| **SMM100A** | Vector signal generator | 44 GHz | — | Modulation, ARB |
| **SMCV100B** | Vector signal generator | 7.125 GHz | — | Digital standards |
| **SGT100A** | SGMA vector RF source | 6 GHz | 1 GHz | Compact, SGMA |
| **SGS100A** | SGMA CW RF source | 12.75 GHz | — | CW-only, SGMA |
| **SMA100B** | Analog signal generator | 67 GHz | — | Ultra-low phase noise |
| **SMB100B** | Analog microwave generator | 40 GHz | — | Microwave |

## Installation

```bash
pip install rs-siggen-mcp
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv pip install rs-siggen-mcp
```

For development:

```bash
git clone https://github.com/RFingAdam/mcp-rs-siggen.git
cd mcp-rs-siggen
uv sync --dev
```

## Quick Start

```bash
# Set your instrument's IP address
export SIGGEN_DEFAULT_HOST=192.168.1.100

# Run the MCP server
rs-siggen-mcp
```

## Integration

### Claude Desktop

Add to your Claude Desktop MCP configuration (`~/.claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "rs-siggen": {
      "command": "rs-siggen-mcp",
      "env": {
        "SIGGEN_DEFAULT_HOST": "192.168.1.100"
      }
    }
  }
}
```

### Claude Code

Add to your project's `.mcp.json`:

```json
{
  "mcpServers": {
    "rs-siggen": {
      "command": "uv",
      "args": ["--directory", "/path/to/mcp-rs-siggen", "run", "rs-siggen-mcp"]
    }
  }
}
```

## Tool Reference

### Connection (6 tools)

| Tool | Description |
|------|-------------|
| `siggen_discover` | Scan for R&S signal generators on the network |
| `siggen_connect` | Connect to a signal generator |
| `siggen_disconnect` | Disconnect (turns off RF output first) |
| `siggen_identify` | Get instrument identification (*IDN?) |
| `siggen_get_status` | Get connection and configuration status |
| `siggen_get_model_info` | Get model capabilities (max freq, IQ BW, etc.) |

### RF Output (5 tools)

| Tool | Description |
|------|-------------|
| `siggen_set_frequency` | Set output frequency |
| `siggen_set_power` | Set output power level |
| `siggen_output_on` | Enable RF output |
| `siggen_output_off` | Disable RF output |
| `siggen_set_phase` | Set output phase |

### Analog Modulation (5 tools)

| Tool | Description |
|------|-------------|
| `siggen_configure_am` | Configure amplitude modulation |
| `siggen_configure_fm` | Configure frequency modulation |
| `siggen_configure_pm` | Configure phase modulation |
| `siggen_configure_pulse` | Configure pulse modulation |
| `siggen_modulation_all_off` | Disable all modulation |

### IQ Modulation (3 tools)

| Tool | Description |
|------|-------------|
| `siggen_iq_on` | Enable IQ modulation |
| `siggen_iq_off` | Disable IQ modulation |
| `siggen_configure_iq_impairments` | Set IQ gain, offset, skew impairments |

### ARB Waveforms (5 tools)

| Tool | Description |
|------|-------------|
| `siggen_load_waveform` | Load a waveform file |
| `siggen_arb_on` | Enable ARB generator |
| `siggen_arb_off` | Disable ARB generator |
| `siggen_set_arb_clock` | Set ARB clock rate |
| `siggen_list_waveforms` | List available waveform files |

### Digital Standards (5 tools)

| Tool | Description |
|------|-------------|
| `siggen_configure_lte` | Configure LTE signal |
| `siggen_configure_5gnr` | Configure 5G NR signal |
| `siggen_configure_wlan` | Configure WLAN signal |
| `siggen_configure_bluetooth` | Configure Bluetooth signal |
| `siggen_generate_waveform` | Generate baseband waveform |

### Sweep (3 tools)

| Tool | Description |
|------|-------------|
| `siggen_configure_freq_sweep` | Configure frequency sweep |
| `siggen_configure_power_sweep` | Configure power sweep |
| `siggen_configure_list_mode` | Configure list mode sweep |

### Reference (2 tools)

| Tool | Description |
|------|-------------|
| `siggen_set_reference_source` | Set reference oscillator source |
| `siggen_get_reference_status` | Get reference oscillator status |

### Calibration (2 tools)

| Tool | Description |
|------|-------------|
| `siggen_run_calibration` | Run internal calibration |
| `siggen_get_calibration_status` | Get calibration status |

### SCPI (4 tools)

| Tool | Description |
|------|-------------|
| `siggen_scpi_send` | Send raw SCPI command |
| `siggen_scpi_query` | Send SCPI query and get response |
| `siggen_reset` | Reset instrument (*RST) |
| `siggen_preset` | Preset instrument |

### Signal Templates (3 tools)

| Tool | Description |
|------|-------------|
| `siggen_list_templates` | List available signal templates |
| `siggen_load_template` | Load a signal template |
| `siggen_apply_template` | Apply loaded template to instrument |

### Instrument State (3 tools)

| Tool | Description |
|------|-------------|
| `siggen_save_state` | Save instrument state to file |
| `siggen_load_state` | Load instrument state from file |
| `siggen_get_full_state` | Get complete instrument state |

### Limit Lines (7 tools)

| Tool | Description |
|------|-------------|
| `siggen_limit_create` | Create a limit line (flat or segmented) |
| `siggen_limit_list` | List all active limit lines |
| `siggen_limit_remove` | Remove a limit line by name |
| `siggen_limit_check` | Check measurements against a limit |
| `siggen_limit_get_status` | Get overall pass/fail across all limits |
| `siggen_limit_save` | Save a limit line to JSON |
| `siggen_limit_load` | Load a limit line from JSON |

## Configuration

All settings can be configured via environment variables with the `SIGGEN_` prefix:

| Variable | Default | Description |
|----------|---------|-------------|
| `SIGGEN_DEFAULT_HOST` | `192.168.1.100` | Signal generator hostname or IP |
| `SIGGEN_DEFAULT_PORT` | `5025` | SCPI TCP port |
| `SIGGEN_CONNECTION_TIMEOUT` | `5.0` | Connection timeout (seconds) |
| `SIGGEN_COMMAND_TIMEOUT` | `30.0` | Command timeout (seconds) |
| `SIGGEN_MAX_POWER_DBM` | `20.0` | Maximum allowed output power (dBm) |
| `SIGGEN_MIN_POWER_DBM` | `-140.0` | Minimum allowed output power (dBm) |
| `SIGGEN_MAX_FREQUENCY_HZ` | `67e9` | Maximum allowed frequency (Hz) |
| `SIGGEN_MIN_FREQUENCY_HZ` | `8e3` | Minimum allowed frequency (Hz) |
| `SIGGEN_ALLOW_RAW_SCPI` | `true` | Enable/disable raw SCPI command access |
| `SIGGEN_LOG_LEVEL` | `INFO` | Log level |

You can also create a `.env` file in the project directory with these settings.

## Security

This server includes multiple security layers:

- **SCPI Input Sanitization** - All user-provided string parameters are validated against injection patterns (semicolons, newlines, command sequences)
- **Path Traversal Protection** - File paths for state save/load are validated to prevent directory traversal
- **Raw SCPI Guard** - Direct SCPI command passthrough can be disabled via `SIGGEN_ALLOW_RAW_SCPI=false`
- **Safety Limits** - Configurable maximum power and frequency limits prevent accidental damage
- **Async Locks** - Thread-safe access to shared mutable state

See [SECURITY.md](SECURITY.md) for vulnerability reporting.

## Signal Templates

Built-in signal templates provide quick setup for common test scenarios:

| Template | Description |
|----------|-------------|
| `cw_1ghz` | 1 GHz CW at -10 dBm |
| `lte_10mhz` | LTE 10 MHz FDD |
| `lte_20mhz` | LTE 20 MHz FDD |
| `nr_100mhz` | 5G NR 100 MHz |
| `wlan_80mhz` | WLAN 802.11ac 80 MHz |
| `bluetooth_le` | Bluetooth Low Energy |
| `two_tone_1mhz` | Two-tone with 1 MHz spacing |
| `two_tone_10mhz` | Two-tone with 10 MHz spacing |
| `fm_broadcast` | FM broadcast signal |
| `am_test` | AM test signal |
| `pulse_radar` | Pulse radar signal |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

[Apache-2.0](LICENSE)
