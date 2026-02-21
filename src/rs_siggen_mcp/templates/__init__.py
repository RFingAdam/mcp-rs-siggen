"""Signal configuration templates."""

from .base import SignalTemplate
from .cw import CWSignalTemplate
from .immunity import ImmunityTestTemplate

__all__ = ["SignalTemplate", "CWSignalTemplate", "ImmunityTestTemplate"]
