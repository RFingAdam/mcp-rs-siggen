"""``siggen-simulator`` entry point.

A wrapper, not an implementation: the whole simulator is
:mod:`scpi_core.sim`, and this only pins the node map and the program name so the
generator can be started with one word. Every ``scpi-sim`` flag -- including the
fault injection that makes a client's desync handling testable
(``--drop-responses``, ``--close-after``, ``--slow-response-ms``) -- passes
straight through.
"""

import sys

from scpi_core.sim.__main__ import main as _sim_main

from . import NODE_MAP


def main(argv: list[str] | None = None) -> int:
    """Serve the R&S generator node map. Returns a process exit code."""
    return _sim_main(argv, prog="siggen-simulator", default_nodes=str(NODE_MAP))


if __name__ == "__main__":
    sys.exit(main())
