# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
