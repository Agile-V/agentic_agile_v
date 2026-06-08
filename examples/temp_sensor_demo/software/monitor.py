#!/usr/bin/env python3
"""Temperature monitoring application."""

import sys
from pathlib import Path

# Add software dir to path
sys.path.insert(0, str(Path(__file__).parent))

from temp_sensor_api import FSC_001_API


def main():
    """Monitor temperature."""
    print("Temperature Monitoring Application")
    print("="*40)

    # Connect to device (mock for demo)
    with FSC_001_API('/dev/ttyUSB0') as api:
        # Run diagnostics
        print("\nRunning diagnostics...")
        diag = api.run_diagnostics()
        print(f"  I2C Scan: {diag['i2c_scan']}")
        print(f"  Self Test: {diag['self_test']}")
        print(f"  Firmware Version: {diag['firmware_version']}")

        # Read temperature
        print("\nReading temperature...")
        temp = api.get_temperature()
        print(f"  Temperature: {temp['temperature_c']}°C")
        print(f"  Status: {temp['status']}")
        print(f"  Timestamp: {temp['timestamp_ms']}ms")

if __name__ == "__main__":
    main()
