"""Configuration management using Pydantic settings."""

import logging

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .safety.validators import SafetyLimits


class SiggenSettings(BaseSettings):
    """
    Signal Generator MCP server configuration.

    Settings can be configured via environment variables with SIGGEN_ prefix.
    """

    model_config = SettingsConfigDict(
        env_prefix="SIGGEN_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Connection defaults
    default_host: str = Field(default="192.168.1.100", description="Default signal generator host")
    default_port: int = Field(default=5025, description="Default signal generator port")
    connection_timeout: float = Field(default=5.0, description="Connection timeout in seconds")
    command_timeout: float = Field(default=30.0, description="Command timeout in seconds")

    # Safety limits
    max_power_dbm: float = Field(default=20.0, description="Maximum output power in dBm")
    min_power_dbm: float = Field(default=-140.0, description="Minimum output power in dBm")
    max_frequency_hz: float = Field(default=67e9, description="Maximum frequency in Hz")
    min_frequency_hz: float = Field(default=8e3, description="Minimum frequency in Hz")

    # Security
    allow_raw_scpi: bool = Field(
        default=True,
        description=(
            "Allow raw SCPI command execution via siggen_scpi_send/siggen_scpi_query. "
            "Set to False to disable raw SCPI access for security hardening. "
            "Default: True for backwards compatibility."
        ),
    )

    # Logging
    log_level: str = Field(default="INFO", description="Log level")

    def get_safety_limits(self) -> SafetyLimits:
        """Create SafetyLimits from settings."""
        return SafetyLimits(
            max_power_dbm=self.max_power_dbm,
            min_power_dbm=self.min_power_dbm,
            max_frequency_hz=self.max_frequency_hz,
            min_frequency_hz=self.min_frequency_hz,
        )

    def configure_logging(self) -> None:
        """Configure logging based on settings."""
        logging.basicConfig(
            level=getattr(logging, self.log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )


# Global settings instance
_settings: SiggenSettings | None = None


def get_settings() -> SiggenSettings:
    """Get or create settings instance."""
    global _settings
    if _settings is None:
        _settings = SiggenSettings()
    return _settings


def reload_settings() -> SiggenSettings:
    """Reload settings from environment."""
    global _settings
    _settings = SiggenSettings()
    return _settings
