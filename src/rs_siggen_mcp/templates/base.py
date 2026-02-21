"""Base signal configuration template class."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class SignalTemplate:
    """
    Base class for signal generator configuration templates.

    Templates define a complete signal configuration including frequency,
    power, modulation settings, etc. They can be saved to and loaded from
    JSON files for reuse.

    Attributes:
        name: Template name for identification
        description: Human-readable description
        frequency_hz: Carrier frequency in Hz
        power_dbm: Output power in dBm
        output_enabled: Whether to enable RF output
        modulation_config: Optional modulation settings
        created_at: Timestamp when template was created
        metadata: Optional additional metadata
    """

    name: str
    description: str
    frequency_hz: float
    power_dbm: float
    output_enabled: bool = True
    modulation_config: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert template to dictionary for serialization.

        Returns:
            Dictionary representation of the template
        """
        return {
            "name": self.name,
            "description": self.description,
            "frequency_hz": self.frequency_hz,
            "power_dbm": self.power_dbm,
            "output_enabled": self.output_enabled,
            "modulation_config": self.modulation_config,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
            "template_type": self.__class__.__name__,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SignalTemplate":
        """
        Create template from dictionary.

        Args:
            data: Dictionary representation of template

        Returns:
            SignalTemplate instance
        """
        created_at = datetime.now()
        if data.get("created_at"):
            try:
                created_at = datetime.fromisoformat(data["created_at"])
            except ValueError:
                pass

        return cls(
            name=data["name"],
            description=data["description"],
            frequency_hz=data["frequency_hz"],
            power_dbm=data["power_dbm"],
            output_enabled=data.get("output_enabled", True),
            modulation_config=data.get("modulation_config", {}),
            created_at=created_at,
            metadata=data.get("metadata", {}),
        )

    def save(self, filepath: str | Path) -> None:
        """
        Save template to JSON file.

        Args:
            filepath: Path to save the template

        Raises:
            IOError: If file cannot be written
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filepath: str | Path) -> "SignalTemplate":
        """
        Load template from JSON file.

        Args:
            filepath: Path to the template file

        Returns:
            Loaded template instance

        Raises:
            FileNotFoundError: If file does not exist
            json.JSONDecodeError: If file is not valid JSON
        """
        filepath = Path(filepath)

        with open(filepath) as f:
            data = json.load(f)

        # Check if this is a specialized template type
        template_type = data.get("template_type", "SignalTemplate")

        if template_type == "CWSignalTemplate":
            from .cw import CWSignalTemplate
            return CWSignalTemplate.from_dict(data)
        elif template_type == "ImmunityTestTemplate":
            from .immunity import ImmunityTestTemplate
            return ImmunityTestTemplate.from_dict(data)
        else:
            return cls.from_dict(data)

    def get_summary(self) -> dict[str, Any]:
        """
        Get a summary of the template configuration.

        Returns:
            Dictionary with key configuration parameters
        """
        return {
            "name": self.name,
            "description": self.description,
            "frequency_hz": self.frequency_hz,
            "power_dbm": self.power_dbm,
            "output_enabled": self.output_enabled,
            "has_modulation": bool(self.modulation_config),
            "template_type": self.__class__.__name__,
        }
