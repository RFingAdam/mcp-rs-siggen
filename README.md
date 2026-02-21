# R&S Signal Generator MCP Server

MCP (Model Context Protocol) server for Rohde & Schwarz signal generator automation via TCP/IP SCPI.

## Supported Instruments

- **SMW200A** - High-end vector signal generator (up to 67 GHz, 2 GHz IQ BW, MIMO)
- **SMBV100B** - Mid-range vector signal generator (up to 6 GHz, 1 GHz IQ BW)
- **SMM100A** - Mid-range vector signal generator (up to 44 GHz)
- **SMCV100B** - Mid-range vector signal generator (up to 7.125 GHz)
- **SGT100A** - Compact SGMA vector RF source (up to 6 GHz)
- **SGS100A** - CW-only SGMA RF source (up to 12.75 GHz)
- **SMA100B** - Analog signal generator, ultra-low phase noise (up to 67 GHz)
- **SMB100B** - Analog microwave signal generator (up to 40 GHz)

## Installation

```bash
pip install rs-siggen-mcp
```

Or for development:

```bash
git clone https://github.com/RFingAdam/mcp-rs-siggen.git
cd mcp-rs-siggen
pip install -e ".[dev]"
```

## Quick Start

```bash
# Set environment variables
export SIGGEN_DEFAULT_HOST=192.168.1.100
export SIGGEN_DEFAULT_PORT=5025

# Run the MCP server
rs-siggen-mcp
```

## Configuration

Copy `.env.example` to `.env` and adjust settings for your setup.

## License

Apache-2.0
