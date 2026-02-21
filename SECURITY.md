# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do not** open a public GitHub issue
2. Email security concerns to **adam@rfingadam.com**
3. Include a description of the vulnerability, steps to reproduce, and potential impact
4. You will receive a response within 48 hours

## Security Features

This MCP server includes several security measures:

- **SCPI Input Sanitization**: All user-provided SCPI parameters are validated against injection patterns
- **Path Traversal Protection**: File paths for state save/load are validated to prevent directory traversal
- **Raw SCPI Guard**: Direct SCPI command access is disabled by default (`SIGGEN_ALLOW_RAW_SCPI=false`)
- **Safety Limits**: Configurable maximum power and frequency limits prevent accidental damage to equipment or DUTs
- **Async Locks**: Thread-safe access to shared mutable state (connections, templates, limits)

## Configuration

Security-relevant environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `SIGGEN_ALLOW_RAW_SCPI` | `false` | Enable/disable raw SCPI command passthrough |
| `SIGGEN_MAX_POWER_DBM` | `20.0` | Maximum allowed output power (dBm) |
| `SIGGEN_MAX_FREQUENCY_HZ` | `6e9` | Maximum allowed frequency (Hz) |
