"""Connection tool handlers (discover, connect, disconnect, identify, status)."""

import asyncio
import logging
from typing import Any

from mcp.types import CallToolResult

from ..config import get_settings
from ..models import InstrumentInfo
from . import _common

logger = logging.getLogger("rs_siggen_mcp.tools")


async def handle_discover(arguments: dict[str, Any]) -> CallToolResult:
    """Handle signal generator discovery."""
    settings = get_settings()
    host = arguments.get("host", settings.default_host)
    start_port = arguments.get("start_port", 5025)
    end_port = arguments.get("end_port", 5035)

    discovered = []

    for port in range(start_port, end_port + 1):
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=1.0,
            )
            # Send *IDN? query
            writer.write(b"*IDN?\n")
            await writer.drain()

            data = await asyncio.wait_for(reader.readline(), timeout=2.0)
            idn = data.decode().strip()

            writer.close()
            await writer.wait_closed()

            if idn:
                info = InstrumentInfo.from_idn(idn)
                discovered.append({
                    "host": host,
                    "port": port,
                    "idn": idn,
                    "instrument": info.to_dict(),
                })

        except (asyncio.TimeoutError, OSError) as e:
            logger.debug("Discovery: port %d not responding: %s", port, e)
            continue
        except (UnicodeDecodeError, ValueError) as e:
            logger.debug("Discovery: port %d returned invalid data: %s", port, e)
            continue

    return _common._format_result({
        "scanned": f"{host}:{start_port}-{end_port}",
        "found": len(discovered),
        "instruments": discovered,
    })


async def handle_connect(arguments: dict[str, Any], host, port) -> CallToolResult:
    """Handle connect to signal generator."""
    sg = await _common._get_siggen(host, port)
    return _common._format_result({
        "status": "connected",
        "address": sg.address,
        "instrument": sg.info.to_dict() if sg.info else None,
    })


async def handle_disconnect(arguments: dict[str, Any], host, port) -> CallToolResult:
    """Handle disconnect from signal generator."""
    settings = get_settings()
    h = host or settings.default_host
    p = port or settings.default_port
    success = await _common._close_siggen(h, p)
    return _common._format_result(
        {"status": "disconnected" if success else "not_connected"}
    )


async def handle_identify(arguments: dict[str, Any], host, port) -> CallToolResult:
    """Handle instrument identification."""
    sg = await _common._get_siggen(host, port)
    info = await sg.identify()
    return _common._format_result(info.to_dict())


async def handle_get_status(arguments: dict[str, Any], host, port) -> CallToolResult:
    """Handle get instrument status."""
    sg = await _common._get_siggen(host, port)
    status = sg.get_status()
    return _common._format_result(status)


async def handle_get_model_info(arguments: dict[str, Any], host, port) -> CallToolResult:
    """Handle get model info."""
    sg = await _common._get_siggen(host, port)
    if sg.info:
        return _common._format_result(sg.info.to_dict())
    return _common._format_result({"error": "No instrument info available"})


# Handler registry for this submodule
CONNECTION_HANDLERS = {
    "siggen_discover": handle_discover,
    "siggen_connect": handle_connect,
    "siggen_disconnect": handle_disconnect,
    "siggen_identify": handle_identify,
    "siggen_get_status": handle_get_status,
    "siggen_get_model_info": handle_get_model_info,
}
