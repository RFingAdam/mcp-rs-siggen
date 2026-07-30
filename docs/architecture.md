# Architecture

## Internal layout

```
┌──────────────────────────────────────────────────────────────────┐
│  User-facing surfaces                                            │
│  ┌────────────────────┐              ┌────────────────────────┐  │
│  │  MCP server        │              │  Python API:           │  │
│  │  (stdio transport) │              │  import rs_siggen_mcp  │  │
│  └────────────────────┘              └────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                              │
┌──────────────────────────────────────────────────────────────────┐
│  Orchestration — tools/ (53 tools, 13 categories)                │
│  • _connection · _rf_output · _modulation · _iq · _arb           │
│  • _digital_standards · _sweep · _reference · _calibration       │
│  • _scpi · _templates · _state · _limits · _common               │
└──────────────────────────────────────────────────────────────────┘
                              │
┌──────────────────────────────────────────────────────────────────┐
│  Driver / transport                                              │
│  • driver/siggen_driver.py — SCPI command layer                  │
│  • scpi_core.transport     — async TCP/IP or VISA transport       │
│  • scpi_core.registry      — live connections, idle TTL, RF-off   │
│  • safety/validators.py    — power / freq clamps + SCPI sanitize │
└──────────────────────────────────────────────────────────────────┘
                              │
                  TCP/IP SCPI (default port 5025)
                              │
                              ▼
                  R&S signal generator (SMW / SMBV / SGT / SMA / …)
```

The driver is asyncio-native. The transport comes from the shared `scpi-core`
package, which the three R&S servers now have in common instead of three
diverged copies. Two of its guarantees are load-bearing here:

- **A query is atomic.** Its send and its matching read are held under one
  task-reentrant lock. The copy this server used to carry took the lock
  separately for each half, so two concurrent tool calls could each receive the
  other's answer.
- **A read timeout poisons the stream.** The instrument may still send that
  response later, leaving every subsequent reply offset by one. The transport
  marks itself desynced and refuses further use until proven clean; because a
  desynced transport reports `is_connected == False`, the connection registry
  reconnects it on the next tool call. Previously a single timeout meant every
  later query silently returned the *previous* query's value.

Every SCPI call site states an `Idempotency` (QUERY / SETTING / ACTION) which
decides whether the transport may re-send after a transport failure. RF output
on/off, `*RST`, `SYSTem:PRESet`, sweep starts and calibration are ACTION and are
never retried.

Connections are cached by `scpi_core.ConnectionRegistry` with an idle TTL. Its
evict hook sends `OUTPut1:STATe OFF` before any handle is dropped: forgetting a
connection does not stop a carrier.

## Source layout

```
mcp-rs-siggen/
├── src/rs_siggen_mcp/
│   ├── server.py           # MCP server (stdio transport)
│   ├── config.py           # pydantic-settings
│   ├── exceptions.py       # re-export shim over scpi_core.exceptions
│   ├── driver/
│   ├── models/
│   ├── tools/              # 53 MCP tool definitions
│   │   ├── _connection.py
│   │   ├── _rf_output.py
│   │   ├── _modulation.py
│   │   ├── _iq.py
│   │   ├── _arb.py
│   │   ├── _digital_standards.py
│   │   ├── _sweep.py
│   │   ├── _reference.py
│   │   ├── _calibration.py
│   │   ├── _scpi.py
│   │   ├── _templates.py
│   │   ├── _state.py
│   │   └── _limits.py
│   ├── templates/          # Built-in signal templates
│   ├── safety/             # Power/freq validators + SCPI sanitize
│   ├── sim/                # Node map + `siggen-simulator` (no hardware needed)
│   └── state.py
├── tests/
└── docs/
```

## Position in eng-mcp-suite

`mcp-rs-siggen` sits in the **lab-gear** layer — it generates physical RF
under SCPI control.

```
        ┌─────────────────────────────────────┐
        │   AI agent (Claude Code / Desktop)  │
        └──────┬──────────────┬───────────────┘
               │ via MCP      │ via MCP
       ┌───────▼──────────┐ ┌─▼──────────────────────┐
       │ mcp-rs-siggen    │ │ siblings: vna, spectrum-analyzer, cmw500 │
       └───────┬──────────┘ └────────────────────────┘
               │ stimulus (CW / NR / LTE / WLAN / BT)
               ▼
            DUT under test
```

### Feeds (this MCP produces output that)…

- **mcp-rs-spectrum-analyzer** — coordinated stimulus during EVM /
  spectrum-flatness testing.
- **mcp-rs-cmw500** — stimulus paired with the CMW500 analyzer for
  vendor-independent RX sweeps.

### Consumes (this MCP accepts input from)…

- **Operator / AI agent** — frequency, power, modulation type, digital
  standard.

### Workflow bundles that include this MCP

| Bundle              | Role of this MCP                                  |
| ------------------- | ------------------------------------------------- |
| `lab-automation`    | Signal-generator stimulus leg                     |
| `rx-sensitivity`    | Controlled level/standard sweep for RX testing    |

---

## Design decisions

- **Direct TCP/IP SCPI.** No NI-VISA install on the MCP host; the generator's
  socket server is reachable from any network-connected client.
- **One tool per digital standard.** `siggen_configure_lte`,
  `siggen_configure_5gnr`, `siggen_configure_wlan`,
  `siggen_configure_bluetooth` each have sensible defaults so an agent
  doesn't have to thread 20 SCPI parameters to get a usable signal.
- **Disconnect turns RF off first.** Belt-and-braces safety — closing the
  connection always emits `OUTP OFF` before disconnect, so a dropped
  session never leaves the generator unexpectedly radiating.
