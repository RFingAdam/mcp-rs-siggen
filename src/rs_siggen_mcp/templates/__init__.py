"""Signal configuration templates."""

from .base import SignalTemplate
from .cw import CWSignalTemplate
from .immunity import ImmunityTestTemplate
from .lte import LTEDownlinkTemplate
from .nr5g import NR5GTemplate
from .two_tone import TwoToneTemplate
from .wlan import WLANTemplate

__all__ = [
    "SignalTemplate",
    "CWSignalTemplate",
    "ImmunityTestTemplate",
    "LTEDownlinkTemplate",
    "NR5GTemplate",
    "TwoToneTemplate",
    "WLANTemplate",
]
