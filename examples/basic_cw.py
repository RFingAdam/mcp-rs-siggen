"""Basic CW signal generation example.

This example demonstrates how to use the R&S signal generator driver
directly (without MCP) to generate a simple CW tone.
"""

import asyncio

from rs_siggen_mcp.driver import RSSignalGeneratorDriver
from rs_siggen_mcp.safety.validators import SafetyLimits


async def main():
    """Generate a 1 GHz CW tone at -10 dBm."""

    # Create driver with custom safety limits
    limits = SafetyLimits(
        max_power_dbm=10.0,  # Limit to +10 dBm
        min_power_dbm=-60.0,
        max_frequency_hz=6e9,  # Limit to 6 GHz
        min_frequency_hz=100e3,
    )

    driver = RSSignalGeneratorDriver(
        host="192.168.1.100",
        port=5025,
        safety_limits=limits,
    )

    try:
        # Connect and identify instrument
        info = await driver.connect()
        print(f"Connected to: {info.manufacturer} {info.model}")
        print(f"Serial: {info.serial}")
        print(f"Firmware: {info.firmware}")
        print(f"Family: {info.family.value}")
        print(f"Max frequency: {info.family.max_frequency_hz / 1e9:.1f} GHz")
        print(f"IQ modulation: {info.family.has_iq_modulation}")

        # Configure CW signal
        await driver.set_frequency(1e9)   # 1 GHz
        await driver.set_power(-10.0)     # -10 dBm
        print("\nSignal configured: 1 GHz @ -10 dBm")

        # Enable output
        await driver.output_on()
        print("RF output: ON")

        # Wait a bit
        print("\nPress Ctrl+C to stop...")
        await asyncio.sleep(10)

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        # Always turn off output and disconnect
        await driver.output_off()
        print("RF output: OFF")
        await driver.disconnect()
        print("Disconnected")


if __name__ == "__main__":
    asyncio.run(main())
