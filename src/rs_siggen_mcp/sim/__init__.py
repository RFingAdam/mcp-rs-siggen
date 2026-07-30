"""Offline signal-generator simulator.

The engine lives in :mod:`scpi_core.sim` and is instrument-agnostic. All this
package holds is the node map that describes an R&S generator's command surface
plus the console-script wrapper that preselects it, so ``siggen-simulator`` needs
no ``--nodes`` argument.
"""

from pathlib import Path

#: Node map served when ``siggen-simulator`` is run without ``--nodes``.
NODE_MAP = Path(__file__).parent / "nodes" / "siggen.yaml"

__all__ = ["NODE_MAP"]
