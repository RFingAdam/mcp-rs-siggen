# Usage

A practical end-to-end walkthrough. For the full tool reference, see [Tools](tools.md).

---

## Scenario: 5G NR 100 MHz RX-sensitivity sweep

You're sweeping a 5G NR receiver's sensitivity at 3.5 GHz across a power
range from −110 dBm down to −60 dBm with a 1 dB step. You want to drive an
SMW200A with a NR 100 MHz signal while a sibling MCP captures BLER or RSSI.

## Setup

```bash
pip install rs-siggen-mcp
```

Register the MCP server with Claude Desktop:

```json
{
  "mcpServers": {
    "rs-siggen": {
      "command": "rs-siggen-mcp",
      "env": { "SIGGEN_DEFAULT_HOST": "192.168.1.100" }
    }
  }
}
```

Restart your MCP client.

## Step 1: connect

> *"Connect to the siggen and tell me its model."*

`siggen_connect`, then `siggen_identify` + `siggen_get_model_info`:

```json
{
  "model": "SMW200A",
  "max_frequency_hz": 67e9,
  "iq_bandwidth_hz": 2e9,
  "has_digital_standards": true
}
```

## Step 2: configure NR 100 MHz

> *"Set up 5G NR, 100 MHz channel, 3.5 GHz center, −110 dBm. Use the nr_100mhz template if it matches."*

```
siggen_load_template(name="nr_100mhz")
siggen_apply_template()
siggen_set_frequency(frequency_hz=3.5e9)
siggen_set_power(power_dbm=-110)
```

## Step 3: power sweep

> *"Configure a power sweep from −110 to −60 dBm, 1 dB step, dwell 100 ms."*

```
siggen_configure_power_sweep(
  start_dbm=-110, stop_dbm=-60, step_dbm=1, dwell_s=0.1
)
```

## Step 4: output on, run

> *"Turn the output on. The receiver MCP will measure BLER at each step."*

```
siggen_output_on()
```

The sweep runs automatically; the sibling receiver MCP fetches BLER per
step. When complete:

```
siggen_output_off()
```

## Step 5: snapshot

> *"Save state so I can replay this sweep tomorrow."*

```
siggen_save_state(path="nr100_sens_sweep.json")
```

---

## What just happened

Five plain-English turns set up a 5G NR 100 MHz reference signal, ran a
50-point power sweep, and snapshotted the configuration: without writing
a single SCPI line. The state file replays identically in the next agent
session, so the same sweep on the next DUT is one tool call away.

- For more tools: [Tool reference](tools.md)
- For how this fits in the suite: [Architecture](architecture.md)
- For sibling MCPs that compose with this one: [eng-mcp-suite catalog](https://github.com/RFingAdam/eng-mcp-suite#whats-included)
