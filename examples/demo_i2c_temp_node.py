#!/usr/bin/env python3
"""
I2C Temperature Node - End-to-End Demo

Demonstrates the complete embedded systems integration workflow.
"""

import json
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Note: pyyaml not installed, using JSON fallback for contracts")
    yaml = None


def print_step(step_num: int, title: str):
    """Print step header."""
    print(f"\n{'='*70}")
    print(f"STEP {step_num}: {title}")
    print(f"{'='*70}\n")


def run_command(cmd: list[str], description: str):
    """Run command and print result."""
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✓ Success")
        if result.stdout:
            print(f"Output:\n{result.stdout}")
        return True
    else:
        print(f"✗ Failed")
        print(f"Error:\n{result.stderr}")
        return False


def create_mock_circuit_ir(output_path: Path):
    """Create mock Circuit IR for demo."""
    circuit_ir = {
        "version": "1.0",
        "project_name": "temp_sensor_node",
        "mcu": {
            "part_number": "STM32F401RET6",
            "manufacturer": "STMicroelectronics",
            "package": "LQFP64",
        },
        "interfaces": [
            {
                "name": "I2C1",
                "type": "I2C",
                "pins": {
                    "SCL": "PB6",
                    "SDA": "PB7",
                },
                "config": {
                    "speed": "100kHz",
                    "pull_ups": "4.7k",
                },
            },
            {
                "name": "USB",
                "type": "USB",
                "pins": {
                    "DP": "PA12",
                    "DM": "PA11",
                },
                "config": {
                    "speed": "full_speed",
                },
            },
        ],
        "components": [
            {
                "designator": "U2",
                "part_number": "TMP102",
                "manufacturer": "Texas Instruments",
                "description": "I2C Temperature Sensor",
                "interface": "I2C1",
                "i2c_address": "0x48",
            },
        ],
        "power": {
            "input_voltage": "5V",
            "regulators": [
                {
                    "designator": "U1",
                    "output_voltage": "3.3V",
                    "max_current": "500mA",
                },
            ],
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(circuit_ir, f, indent=2)

    print(f"✓ Created mock Circuit IR: {output_path}")


def main():
    """Run end-to-end demo."""
    print("="*70)
    print("I2C TEMPERATURE NODE - END-TO-END DEMO")
    print("="*70)

    project_root = Path.cwd()
    demo_dir = project_root / "examples" / "temp_sensor_demo"

    # Step 1: Create mock PCB Circuit IR
    print_step(1, "Create PCB Circuit IR (Mock)")

    circuit_ir_path = demo_dir / "pcb" / "circuit_ir.json"
    create_mock_circuit_ir(circuit_ir_path)

    # Step 2: Generate hardware-firmware contract
    print_step(2, "Generate Hardware-Firmware Contract")

    contract_dir = demo_dir / ".agentic-agile-v" / "contracts"
    hw_fw_contract_path = contract_dir / "hardware_firmware_contract.yaml"

    # For demo, create contract manually
    hw_fw_contract = {
        "contract_version": "1.0",
        "mcu": {
            "part_number": "STM32F401RET6",
            "manufacturer": "STMicroelectronics",
        },
        "interfaces": [
            {
                "name": "I2C1",
                "type": "I2C",
                "pins": {"SCL": "PB6", "SDA": "PB7"},
                "speed": "100kHz",
            },
            {
                "name": "USB",
                "type": "USB",
                "pins": {"DP": "PA12", "DM": "PA11"},
            },
        ],
        "peripherals": [
            {
                "name": "TMP102",
                "type": "temperature_sensor",
                "interface": "I2C1",
                "address": "0x48",
            },
        ],
        "firmware_constraints": {
            "max_binary_size_kb": 512,
            "max_ram_kb": 96,
        },
    }

    contract_dir.mkdir(parents=True, exist_ok=True)
    if yaml:
        with open(hw_fw_contract_path, "w") as f:
            yaml.dump(hw_fw_contract, f, default_flow_style=False)
    else:
        # Fallback to JSON if yaml not available
        hw_fw_contract_path = contract_dir / "hardware_firmware_contract.json"
        with open(hw_fw_contract_path, "w") as f:
            json.dump(hw_fw_contract, f, indent=2)

    print(f"✓ Created hardware-firmware contract: {hw_fw_contract_path}")

    # Step 3: Generate firmware project structure
    print_step(3, "Generate Firmware Project Structure")

    firmware_dir = demo_dir / "firmware" / "temp_sensor"
    firmware_dir.mkdir(parents=True, exist_ok=True)

    # Create platformio.ini
    platformio_ini = """[env:nucleo_f401re]
platform = ststm32
board = nucleo_f401re
framework = arduino

build_flags = 
    -DTEMP_SENSOR_I2C_ADDR=0x48
    -DI2C1_SCL=PB6
    -DI2C1_SDA=PB7

lib_deps = 
    Wire
    ArduinoJson
"""

    (firmware_dir / "platformio.ini").write_text(platformio_ini)
    print(f"✓ Created: {firmware_dir / 'platformio.ini'}")

    # Create board_contract.h
    board_contract_h = """#ifndef BOARD_CONTRACT_H
#define BOARD_CONTRACT_H

// Auto-generated from hardware-firmware contract
// DO NOT EDIT MANUALLY

// I2C1 Interface
#define I2C1_SCL PB6
#define I2C1_SDA PB7

// TMP102 Temperature Sensor
#define TEMP_SENSOR_I2C_ADDR 0x48

// USB Interface
#define USB_DP PA12
#define USB_DM PA11

#endif // BOARD_CONTRACT_H
"""

    src_dir = firmware_dir / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "board_contract.h").write_text(board_contract_h)
    print(f"✓ Created: {src_dir / 'board_contract.h'}")

    # Step 4: Generate firmware-software contract
    print_step(4, "Generate Firmware-Software Contract")

    fw_sw_contract = {
        "contract_id": "FSC-001",
        "source_firmware_task": "TASK-123-firmware",
        "transport": "usb_cdc_serial",
        "protocol_version": 1,
        "commands": [
            {
                "name": "get_temperature",
                "request": {"type": "object", "fields": {}},
                "response": {
                    "type": "object",
                    "fields": {
                        "temperature_c": {"type": "number", "unit": "celsius"},
                        "timestamp_ms": {"type": "integer"},
                        "status": {"type": "string", "enum": ["ok", "sensor_missing", "bus_error"]},
                    },
                },
                "max_response_time_ms": 50,
            },
            {
                "name": "run_diagnostics",
                "request": {"type": "object", "fields": {}},
                "response": {
                    "type": "object",
                    "fields": {
                        "i2c_scan": {"type": "string", "enum": ["passed", "failed"]},
                        "self_test": {"type": "string", "enum": ["passed", "failed"]},
                        "firmware_version": {"type": "string"},
                    },
                },
                "max_response_time_ms": 200,
            },
        ],
        "error_codes": [
            {"code": "SENSOR_MISSING", "meaning": "Sensor not found at I2C address", "recoverable": False},
            {"code": "BUS_ERROR", "meaning": "I2C bus communication error", "recoverable": True},
            {"code": "NOT_READY", "meaning": "Firmware not initialized", "recoverable": True},
        ],
        "software_expectations": {
            "retries": {"max_attempts": 3, "backoff_ms": 100},
            "data_freshness_max_ms": 500,
        },
    }

    fw_sw_contract_path = contract_dir / "firmware_software_contract.yaml"
    if yaml:
        with open(fw_sw_contract_path, "w") as f:
            yaml.dump(fw_sw_contract, f, default_flow_style=False)
    else:
        # Fallback to JSON
        fw_sw_contract_path = contract_dir / "firmware_software_contract.json"
        with open(fw_sw_contract_path, "w") as f:
            json.dump(fw_sw_contract, f, indent=2)

    print(f"✓ Created firmware-software contract: {fw_sw_contract_path}")

    # Step 5: Generate software API
    print_step(5, "Generate Software API (Mock)")

    software_api = '''"""
Firmware API for FSC-001.

Auto-generated from firmware-software contract.
DO NOT EDIT MANUALLY.
"""

import json
import time
from typing import Any

# Mock implementation for demo
class FSC_001_API:
    """Firmware API client for FSC-001."""

    def __init__(self, port: str, baudrate: int = 115200):
        """Initialize API client."""
        self.port = port
        self.baudrate = baudrate
        print(f"[DEMO] Connected to {port} at {baudrate} baud")

    def connect(self) -> None:
        """Connect to firmware."""
        print(f"[DEMO] Connected to firmware")

    def disconnect(self) -> None:
        """Disconnect from firmware."""
        print(f"[DEMO] Disconnected from firmware")

    def get_temperature(self) -> dict[str, Any]:
        """Execute get_temperature command."""
        print(f"[DEMO] Executing get_temperature command...")
        return {
            "temperature_c": 23.5,
            "timestamp_ms": int(time.time() * 1000),
            "status": "ok",
        }

    def run_diagnostics(self) -> dict[str, Any]:
        """Execute run_diagnostics command."""
        print(f"[DEMO] Executing run_diagnostics command...")
        return {
            "i2c_scan": "passed",
            "self_test": "passed",
            "firmware_version": "1.0.0",
        }

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
'''

    software_dir = demo_dir / "software"
    software_dir.mkdir(parents=True, exist_ok=True)
    (software_dir / "temp_sensor_api.py").write_text(software_api)
    print(f"✓ Created software API: {software_dir / 'temp_sensor_api.py'}")

    # Step 6: Create application example
    print_step(6, "Create Application Example")

    app_code = '''#!/usr/bin/env python3
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
        print("\\nRunning diagnostics...")
        diag = api.run_diagnostics()
        print(f"  I2C Scan: {diag['i2c_scan']}")
        print(f"  Self Test: {diag['self_test']}")
        print(f"  Firmware Version: {diag['firmware_version']}")

        # Read temperature
        print("\\nReading temperature...")
        temp = api.get_temperature()
        print(f"  Temperature: {temp['temperature_c']}°C")
        print(f"  Status: {temp['status']}")
        print(f"  Timestamp: {temp['timestamp_ms']}ms")

if __name__ == "__main__":
    main()
'''

    (software_dir / "monitor.py").write_text(app_code)
    (software_dir / "monitor.py").chmod(0o755)
    print(f"✓ Created application: {software_dir / 'monitor.py'}")

    # Step 7: Run application demo
    print_step(7, "Run Application Demo")

    print("Executing: python software/monitor.py\n")
    result = subprocess.run(
        [sys.executable, str(software_dir / "monitor.py")],
        capture_output=True,
        text=True,
    )

    print(result.stdout)
    if result.stderr:
        print(result.stderr)

    # Step 8: Summary
    print_step(8, "Summary")

    print("✓ End-to-end workflow complete!")
    print(f"\nGenerated files:")
    print(f"  PCB:")
    print(f"    - {circuit_ir_path}")
    print(f"  Contracts:")
    print(f"    - {hw_fw_contract_path}")
    print(f"    - {fw_sw_contract_path}")
    print(f"  Firmware:")
    print(f"    - {firmware_dir / 'platformio.ini'}")
    print(f"    - {src_dir / 'board_contract.h'}")
    print(f"  Software:")
    print(f"    - {software_dir / 'temp_sensor_api.py'}")
    print(f"    - {software_dir / 'monitor.py'}")

    print(f"\nNext steps:")
    print(f"  1. Review generated contracts and code")
    print(f"  2. Run: cd {demo_dir}")
    print(f"  3. Build firmware: agilev firmware build --project firmware/temp_sensor")
    print(f"  4. Test firmware: agilev firmware test --project firmware/temp_sensor --host")
    print(f"  5. Verify contracts: agilev embedded verify --root {demo_dir}")

    print(f"\n{'='*70}")
    print(f"DEMO COMPLETE")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
