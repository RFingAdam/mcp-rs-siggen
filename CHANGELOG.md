# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- **Concurrent queries could return each other's answers.** The local SCPI
  transport took its `asyncio.Lock` separately for the send and the read of a
  query, so two overlapping tool calls crossed responses — silently, with
  plausible-looking values. The shared `scpi-core` transport holds both halves
  under one task-reentrant lock.
- **A single read timeout served stale readings forever.** After a timed-out
  read the instrument may still send that response later, leaving the stream
  offset by one; the old transport had no notion of this and every subsequent
  query returned the *previous* query's value with no error. The stream is now
  marked desynced and refuses further use, and because a desynced transport
  reports `is_connected == False` the connection registry reconnects it on the
  next tool call.
- **RF-output commands were blindly retried.** Retry is now decided by an
  explicit `Idempotency` on every SCPI call site: RF output on/off, `*RST`,
  `SYSTem:PRESet`, subsystem presets, trigger-execute and sweep starts are
  ACTION and are never re-sent; value assignments are SETTING; reads are QUERY.
- **An idle connection could be dropped while still radiating.** Connections
  now live in `scpi_core.ConnectionRegistry` with an idle TTL, and its evict
  hook sends `OUTPut1:STATe OFF` before any handle is released.

### Added
- **Offline simulator** (`siggen-simulator`): serves the generator's SCPI
  command surface from `sim/nodes/siggen.yaml` so the tool surface can be
  exercised with no hardware attached. Includes the fault injection that makes
  timeout and desync handling testable (`--drop-responses`, `--close-after`,
  `--slow-response-ms`). Nodes not confirmed against hardware are marked and
  listable with `--list-unverified`.
- `sim` extra (`pyyaml`) for the simulator.

### Changed
- **Depends on `scpi-core`** for the SCPI transport, connection registry,
  exception hierarchy and injection/path validators, replacing local copies
  that had diverged from the other two R&S servers. `driver/scpi_socket.py` is
  gone; `SCPISocket` is re-exported from `driver/` for existing imports.
- `exceptions.py` is a re-export shim over `scpi_core.exceptions`, with
  `SignalGeneratorError` aliased to `InstrumentError` so cross-server handlers
  work. Every previously exported name is still importable.
- `safety/validators.py` keeps `sanitize_scpi_param` / `validate_safe_path` as
  adapters over `scpi_core.safety`, preserving this server's exact refusal
  wording. `SafetyLimits` and `SafetyValidator` are unchanged.

## [0.2.0] — 2026-05-13

### Changed
- **License: Apache-2.0 → AGPL-3.0-or-later.** Aligns with the
  eng-mcp-suite toolkit-wide AGPL move. R&S hardware and proprietary
  client software are independent of this wrapper.

### Added
- **Limit line tools** (Issue #14): 7 new MCP tools (`siggen_limit_create`, `siggen_limit_list`, `siggen_limit_remove`, `siggen_limit_check`, `siggen_limit_get_status`, `siggen_limit_save`, `siggen_limit_load`) for pass/fail testing against frequency-dependent limit lines
- **CI pipeline**: GitHub Actions workflow with Python 3.10-3.13 test matrix, ruff linting, mypy type checking, and pytest with coverage
- **Community files**: CONTRIBUTING.md, SECURITY.md, issue templates, PR template
- **PEP 561 marker**: `py.typed` file for type checker support
- **Pre-commit config**: ruff and mypy hooks via `.pre-commit-config.yaml`
- Coverage configuration in pyproject.toml (70% threshold)
- Python 3.13 classifier

### Changed
- **Modular tool architecture** (Issue #5): Decomposed monolithic `tools.py` (1,673 lines) into 14 focused handler submodules under `tools/` package with centralized error handling in `__init__.py`
- **MCP version pinned**: `mcp>=1.0.0,<2.0.0` (Issue #12)
- **README rewritten** (Issue #10): Comprehensive documentation with architecture diagram, full tool reference (53 tools), configuration reference, integration guides, and security model

### Fixed
- Test naming conventions: renamed `isError` test method names to snake_case (`is_error`)
- Line-length violations in test_security.py
- Unused imports cleaned up across test files

## [0.1.0] - 2025-02-20

### Added
- Initial release
- MCP server for Rohde & Schwarz signal generator automation
- Support for SMW200A, SMBV100B, SMM100A, SMCV100B, SGT100A, SGS100A, SMA100B, SMB100B
- SCPI socket transport layer
- Safety validation for power and frequency limits
- RF output control (frequency, power, on/off, phase)
- Analog modulation (AM, FM, PM, pulse)
- IQ modulation control
- ARB waveform generator control
- Digital standard configuration (LTE, 5G NR, WLAN, Bluetooth)
- Frequency and power sweep modes
- Reference oscillator control
- Calibration management
- Raw SCPI send/query
- Signal templates (CW, immunity testing)
- State save/restore
- Limit line testing
- Connection pooling for multiple instruments
