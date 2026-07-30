"""Exception surface for signal generator operations.

The bodies moved to :mod:`scpi_core.exceptions` when the SCPI transport was
extracted into the shared library: none of them described anything specific to a
signal generator, and three servers carrying three diverged copies meant an
``except CommunicationError`` in one could not catch the other's failure.

This module stays because the names are part of this server's import surface --
``from ..exceptions import CommunicationError`` appears throughout ``tools/`` and
``driver/`` -- and because ``SignalGeneratorError`` is the name callers catch to
mean "anything this server raised". It is now an alias for
:class:`scpi_core.exceptions.InstrumentError`, so the whole hierarchy is shared
and cross-server handlers work.

``MeasurementError`` stayed here as a real class: it names a generator-side
failure (a waveform or signal-generation step that did not complete) and has no
counterpart in the shared library, which deliberately models only transport,
configuration and safety.
"""

from scpi_core.exceptions import (
    CommunicationError as CommunicationError,
)
from scpi_core.exceptions import (
    ConfigurationError as ConfigurationError,
)
from scpi_core.exceptions import (
    ConnectionError as ConnectionError,
)
from scpi_core.exceptions import (
    DesyncError as DesyncError,
)
from scpi_core.exceptions import (
    InstrumentError,
)
from scpi_core.exceptions import (
    SafetyError as SafetyError,
)
from scpi_core.exceptions import (
    TimeoutError as TimeoutError,
)

#: Historical base-exception name for this server. Every exception raised here
#: is still catchable as ``SignalGeneratorError``.
SignalGeneratorError = InstrumentError


class MeasurementError(InstrumentError):
    """Error during measurement or signal generation."""


__all__ = [
    "CommunicationError",
    "ConfigurationError",
    "ConnectionError",
    "DesyncError",
    "InstrumentError",
    "MeasurementError",
    "SafetyError",
    "SignalGeneratorError",
    "TimeoutError",
]
