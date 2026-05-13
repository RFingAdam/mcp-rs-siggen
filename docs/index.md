# mcp-rs-siggen

**Drive Rohde & Schwarz signal generators from any MCP-compatible AI client.**
**TCP/IP SCPI — 53 tools across CW / analog / IQ / ARB / digital-standard (LTE, 5G NR, WLAN, Bluetooth).**

---

## What it is

`mcp-rs-siggen` is a [Model Context Protocol](https://modelcontextprotocol.io)
server that automates R&S signal generators via direct TCP/IP SCPI. The
generator family covers vector (SMW200A, SMBV100B, SMM100A, SMCV100B), SGMA
RF sources (SGT100A, SGS100A), and analog/microwave generators (SMA100B,
SMB100B) — frequencies up to 67 GHz, IQ bandwidths up to 2 GHz.

CW output, AM/FM/PM/Pulse, IQ with impairments, ARB playback, baseband
digital standards (LTE / 5G NR / WLAN / Bluetooth), and sweeps — all exposed
as MCP tools.

## Install

```bash
pip install rs-siggen-mcp
```

## First call

=== "MCP"

    Add to `claude_desktop_config.json`:

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

    Then ask your assistant:

    > *"Set up a 5G NR 100 MHz signal at 3.5 GHz, −20 dBm, and turn the output on."*

=== "Python"

    ```python
    import asyncio
    from rs_siggen_mcp.driver import SiggenDriver

    async def main():
        async with SiggenDriver("192.168.1.100", 5025) as sg:
            await sg.set_frequency(1e9)
            await sg.set_power(-10)
            await sg.output_on()

    asyncio.run(main())
    ```

## Where to next

- [Tool reference](tools.md) — every MCP tool with arguments
- [Usage examples](usage.md) — an RX-sensitivity sweep walkthrough
- [Architecture](architecture.md) — how this MCP fits inside eng-mcp-suite

---

!!! note "Part of eng-mcp-suite"
    This MCP server is part of [eng-mcp-suite](https://github.com/RFingAdam/eng-mcp-suite) —
    an umbrella of engineering MCP servers across RF, EMC, PCB, signal
    integrity, EM simulation, and lab test.
