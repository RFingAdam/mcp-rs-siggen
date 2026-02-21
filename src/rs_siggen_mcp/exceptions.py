"""Custom exceptions for signal generator operations.

This module defines all exceptions at the package root level to avoid
circular import issues between driver and safety modules.
"""


class SignalGeneratorError(Exception):
    """Base exception for signal generator errors."""

    def __init__(self, message: str, address: str | None = None):
        self.message = message
        self.address = address
        super().__init__(f"{message}" + (f" (address: {address})" if address else ""))


class ConnectionError(SignalGeneratorError):
    """Error connecting to signal generator."""

    pass


class CommunicationError(SignalGeneratorError):
    """Error communicating with signal generator."""

    pass


class ConfigurationError(SignalGeneratorError):
    """Error configuring signal generator settings."""

    pass


class MeasurementError(SignalGeneratorError):
    """Error during measurement or signal generation."""

    pass


class SafetyError(SignalGeneratorError):
    """Safety limit violation."""

    def __init__(
        self,
        message: str,
        parameter: str,
        value: float,
        limit: float,
        address: str | None = None,
    ):
        self.parameter = parameter
        self.value = value
        self.limit = limit
        super().__init__(message, address)


class TimeoutError(SignalGeneratorError):
    """Operation timed out."""

    pass
