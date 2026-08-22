# Tools

This page documents the 53 MCP tools the server exposes. Tools are registered
under the `rs-siggen` namespace when the server is loaded by an MCP client.

## Tool index

### Connection (6)

| Tool | Purpose |
| ---- | ------- |
| `siggen_discover` | Scan for R&S signal generators on the network |
| `siggen_connect` | Connect to a signal generator |
| `siggen_disconnect` | Disconnect (turns off RF output first) |
| `siggen_identify` | Get instrument identification (`*IDN?`) |
| `siggen_get_status` | Get connection and configuration status |
| `siggen_get_model_info` | Get model capabilities (max freq, IQ BW, …) |

### RF Output (5)

| Tool | Purpose |
| ---- | ------- |
| `siggen_set_frequency` | Set output frequency |
| `siggen_set_power` | Set output power level |
| `siggen_output_on` | Enable RF output |
| `siggen_output_off` | Disable RF output |
| `siggen_set_phase` | Set output phase |

### Analog Modulation (5)

| Tool | Purpose |
| ---- | ------- |
| `siggen_configure_am` | Configure amplitude modulation |
| `siggen_configure_fm` | Configure frequency modulation |
| `siggen_configure_pm` | Configure phase modulation |
| `siggen_configure_pulse` | Configure pulse modulation |
| `siggen_modulation_all_off` | Disable all modulation |

### IQ Modulation (3)

| Tool | Purpose |
| ---- | ------- |
| `siggen_iq_on` | Enable IQ modulation |
| `siggen_iq_off` | Disable IQ modulation |
| `siggen_configure_iq_impairments` | Set IQ gain / offset / skew impairments |

### ARB Waveforms (5)

| Tool | Purpose |
| ---- | ------- |
| `siggen_load_waveform` | Load a waveform file |
| `siggen_arb_on` | Enable ARB generator |
| `siggen_arb_off` | Disable ARB generator |
| `siggen_set_arb_clock` | Set ARB clock rate |
| `siggen_list_waveforms` | List available waveform files |

### Digital Standards (5)

| Tool | Purpose |
| ---- | ------- |
| `siggen_configure_lte` | Configure LTE signal |
| `siggen_configure_5gnr` | Configure 5G NR signal |
| `siggen_configure_wlan` | Configure WLAN signal |
| `siggen_configure_bluetooth` | Configure Bluetooth signal |
| `siggen_generate_waveform` | Generate baseband waveform |

### Sweep (3)

| Tool | Purpose |
| ---- | ------- |
| `siggen_configure_freq_sweep` | Configure frequency sweep |
| `siggen_configure_power_sweep` | Configure power sweep |
| `siggen_configure_list_mode` | Configure list mode sweep |

### Reference (2)

| Tool | Purpose |
| ---- | ------- |
| `siggen_set_reference_source` | Set reference oscillator source |
| `siggen_get_reference_status` | Get reference oscillator status |

### Calibration (2)

| Tool | Purpose |
| ---- | ------- |
| `siggen_run_calibration` | Run internal calibration |
| `siggen_get_calibration_status` | Get calibration status |

### SCPI (4)

| Tool | Purpose |
| ---- | ------- |
| `siggen_scpi_send` | Send raw SCPI command |
| `siggen_scpi_query` | Send SCPI query and get response |
| `siggen_reset` | Reset instrument (`*RST`) |
| `siggen_preset` | Preset instrument |

### Signal Templates (3)

| Tool | Purpose |
| ---- | ------- |
| `siggen_list_templates` | List available signal templates |
| `siggen_load_template` | Load a signal template |
| `siggen_apply_template` | Apply loaded template to instrument |

### State (3)

| Tool | Purpose |
| ---- | ------- |
| `siggen_save_state` | Save instrument state to file |
| `siggen_load_state` | Load instrument state from file |
| `siggen_get_full_state` | Get complete instrument state |

### Limit Lines (7)

| Tool | Purpose |
| ---- | ------- |
| `siggen_limit_create` | Create a limit line (flat or segmented) |
| `siggen_limit_list` | List all active limit lines |
| `siggen_limit_remove` | Remove a limit line by name |
| `siggen_limit_check` | Check measurements against a limit |
| `siggen_limit_get_status` | Get overall pass/fail across all limits |
| `siggen_limit_save` | Save a limit line to JSON |
| `siggen_limit_load` | Load a limit line from JSON |

---

## Source of truth

Tool definitions live in
[`src/rs_siggen_mcp/tools/`](../src/rs_siggen_mcp/tools/), one module per
category. Each tool has a complete JSON-Schema `inputSchema` declared at
registration: arguments, defaults, and units are documented inline there.
