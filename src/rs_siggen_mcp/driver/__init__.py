"""Driver layer for R&S signal generator communication.

``SCPISocket`` used to live here. It now comes from :mod:`scpi_core.transport`,
which is shared with the other R&S servers and, unlike the copy this package
carried, holds a query's send and read under one lock and refuses to serve a
stream that a timed-out read may have left offset. It is re-exported so existing
``from ..driver import SCPISocket`` sites keep working.
"""

from scpi_core import SCPISocket

from .siggen_driver import RSSignalGeneratorDriver

__all__ = ["SCPISocket", "RSSignalGeneratorDriver"]
