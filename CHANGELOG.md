# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - Unreleased

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
