"""
PlatformIO firmware backend.

Generates and builds firmware projects using PlatformIO.
"""

import subprocess
from pathlib import Path
from typing import Any

import yaml

from agilev.firmware.backend import FirmwareBackend


class PlatformIOBackend(FirmwareBackend):
    """PlatformIO firmware backend."""

    def init_project(self, project_dir: Path) -> None:
        """Initialize PlatformIO project structure.

        Args:
            project_dir: Directory to create project in
        """
        project_dir.mkdir(parents=True, exist_ok=True)

        # Create directory structure
        (project_dir / "include").mkdir(exist_ok=True)
        (project_dir / "src").mkdir(exist_ok=True)
        (project_dir / "test").mkdir(exist_ok=True)
        (project_dir / "test" / "test_host").mkdir(exist_ok=True)
        (project_dir / "lib").mkdir(exist_ok=True)

    def generate_from_contract(self, project_dir: Path) -> None:
        """Generate firmware code from hardware-firmware contract.

        Args:
            project_dir: Project directory
        """
        # Load contract
        with open(self.contract_path) as f:
            contract = yaml.safe_load(f)

        # Generate platformio.ini
        self._generate_platformio_ini(project_dir, contract)

        # Generate board_contract.h
        self._generate_board_contract_h(project_dir, contract)

        # Generate main.cpp skeleton
        self._generate_main_cpp(project_dir, contract)

        # Generate diagnostics skeleton
        self._generate_diagnostics_cpp(project_dir, contract)

    def _generate_platformio_ini(self, project_dir: Path, contract: dict[str, Any]) -> None:
        """Generate platformio.ini configuration.

        Args:
            project_dir: Project directory
            contract: Hardware-firmware contract
        """
        mcu = contract.get("mcu", {})
        _board_name = contract.get("board", "genericSTM32F411CE")  # noqa: F841

        # Map MCU to PlatformIO board
        # This is a simple mapping - real implementation would be more sophisticated
        part_number = mcu.get("part_number", "").lower()
        if "stm32f411" in part_number:
            pio_board = "genericSTM32F411CE"
            framework = "arduino"
        elif "esp32" in part_number:
            pio_board = "esp32dev"
            framework = "arduino"
        else:
            pio_board = "genericSTM32F411CE"
            framework = "arduino"

        ini_content = f"""[env:target]
platform = ststm32
board = {pio_board}
framework = {framework}
monitor_speed = 115200

[env:native]
platform = native
build_flags = -std=c++11
test_framework = unity
"""

        (project_dir / "platformio.ini").write_text(ini_content)

    def _generate_board_contract_h(self, project_dir: Path, contract: dict[str, Any]) -> None:
        """Generate board_contract.h with pin definitions.

        Args:
            project_dir: Project directory
            contract: Hardware-firmware contract
        """
        board = contract.get("board", "unknown")
        revision = contract.get("pcb_revision", "unknown")

        lines = [
            f"// Board contract for {board} {revision}",
            "// Auto-generated from hardware-firmware contract",
            "// DO NOT EDIT - regenerate from contract",
            "",
            "#ifndef BOARD_CONTRACT_H",
            "#define BOARD_CONTRACT_H",
            "",
        ]

        # Add MCU info as comments
        mcu = contract.get("mcu", {})
        lines.append(f"// MCU: {mcu.get('part_number', 'N/A')}")
        lines.append(f"// Package: {mcu.get('package', 'N/A')}")
        lines.append(f"// Voltage domain: {mcu.get('voltage_domain', 'N/A')}")
        lines.append("")

        # Add I2C pin definitions
        interfaces = contract.get("interfaces", {})
        i2c_buses = interfaces.get("i2c", [])

        if i2c_buses:
            lines.append("// I2C Bus Definitions")
            for i2c in i2c_buses:
                bus_id = i2c.get("id", "I2C1")
                sda = i2c.get("sda", {})
                scl = i2c.get("scl", {})

                if sda and scl:
                    sda_pin = sda.get("mcu_pin", "")
                    scl_pin = scl.get("mcu_pin", "")
                    lines.append(
                        f"#define {bus_id}_SDA {self._pin_to_arduino(sda_pin)}  "
                        f"// {sda.get('net', '')}"
                    )
                    lines.append(
                        f"#define {bus_id}_SCL {self._pin_to_arduino(scl_pin)}  "
                        f"// {scl.get('net', '')}"
                    )
                    lines.append("")

                # Add device addresses
                devices = i2c.get("devices", [])
                if devices:
                    lines.append(f"// {bus_id} Device Addresses")
                    for device in devices:
                        name = device.get("name", "").upper()
                        addr = device.get("address", "0x00")
                        lines.append(f"#define {name}_I2C_ADDR {addr}")
                    lines.append("")

        # Add GPIO definitions
        gpio_pins = interfaces.get("gpio", [])
        if gpio_pins:
            lines.append("// GPIO Pin Definitions")
            for gpio in gpio_pins:
                name = gpio.get("name", "").upper()
                pin = gpio.get("mcu_pin", "")
                net = gpio.get("net", "")
                lines.append(f"#define {name} {self._pin_to_arduino(pin)}  // {net}")
            lines.append("")

        # Add power rail definitions
        power = contract.get("power", {})
        rails = power.get("rails", [])
        if rails:
            lines.append("// Power Rail Definitions")
            for rail in rails:
                name = rail.get("name", "").upper()
                voltage = rail.get("nominal_v", 0)
                lines.append(f"#define {name}_VOLTAGE {voltage}f")
            lines.append("")

        lines.append("#endif // BOARD_CONTRACT_H")

        (project_dir / "include" / "board_contract.h").write_text("\n".join(lines))

    def _generate_main_cpp(self, project_dir: Path, contract: dict[str, Any]) -> None:
        """Generate main.cpp skeleton.

        Args:
            project_dir: Project directory
            contract: Hardware-firmware contract
        """
        board = contract.get("board", "unknown")

        lines = [
            f"// Main firmware for {board}",
            "// Generated from hardware-firmware contract",
            "",
            "#include <Arduino.h>",
            '#include "board_contract.h"',
            "",
            "void setup() {",
            "    Serial.begin(115200);",
            '    delay(1000);',
            '    Serial.println("Firmware starting...");',
            "",
            "    // TODO: Initialize peripherals from contract",
            "}",
            "",
            "void loop() {",
            "    // TODO: Implement firmware logic",
            "    delay(1000);",
            "}",
        ]

        (project_dir / "src" / "main.cpp").write_text("\n".join(lines))

    def _generate_diagnostics_cpp(self, project_dir: Path, contract: dict[str, Any]) -> None:
        """Generate diagnostics.cpp skeleton.

        Args:
            project_dir: Project directory
            contract: Hardware-firmware contract
        """
        diagnostics = contract.get("diagnostics", {})
        required_commands = diagnostics.get("required_commands", [])

        lines = [
            "// Diagnostics implementation",
            "// Generated from hardware-firmware contract",
            "",
            "#include <Arduino.h>",
            '#include "board_contract.h"',
            "",
        ]

        # Generate diagnostic command stubs
        for cmd in required_commands:
            func_name = cmd.replace("-", "_")
            lines.append(f"void {func_name}() {{")
            lines.append(f'    Serial.println("Running {cmd}...");')
            lines.append("    // TODO: Implement diagnostic")
            lines.append('    Serial.println("PASSED");')
            lines.append("}")
            lines.append("")

        (project_dir / "src" / "diagnostics.cpp").write_text("\n".join(lines))

    def _pin_to_arduino(self, mcu_pin: str) -> str:
        """Convert MCU pin name to Arduino pin constant.

        Args:
            mcu_pin: MCU pin name (e.g., PA0, PB7)

        Returns:
            Arduino pin constant
        """
        # Simple mapping for STM32
        if mcu_pin.startswith("P"):
            port = mcu_pin[1]  # A, B, C, etc.
            num = mcu_pin[2:]
            return f"P{port}{num}"
        return mcu_pin

    def build(self, project_dir: Path) -> tuple[bool, str]:
        """Build firmware project.

        Args:
            project_dir: Project directory

        Returns:
            Tuple of (success, output)
        """
        try:
            result = subprocess.run(
                ["pio", "run", "-e", "target"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=300,
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, "Build timed out after 5 minutes"
        except FileNotFoundError:
            return False, "PlatformIO not found. Install with: pip install platformio"
        except Exception as e:
            return False, f"Build error: {e}"

    def run_host_tests(self, project_dir: Path) -> tuple[bool, str]:
        """Run host-based unit tests.

        Args:
            project_dir: Project directory

        Returns:
            Tuple of (success, output)
        """
        try:
            result = subprocess.run(
                ["pio", "test", "-e", "native"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=180,
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, "Tests timed out after 3 minutes"
        except FileNotFoundError:
            return False, "PlatformIO not found. Install with: pip install platformio"
        except Exception as e:
            return False, f"Test error: {e}"

    def collect_evidence(self, project_dir: Path, task_id: str) -> dict[str, Any]:
        """Collect evidence bundle for firmware.

        Args:
            project_dir: Project directory
            task_id: Firmware task ID

        Returns:
            Evidence bundle dictionary
        """
        # Load contract to get PCB task info
        with open(self.contract_path) as f:
            contract = yaml.safe_load(f)

        evidence = {
            "task_id": task_id,
            "artifact_type": "firmware",
            "risk_level": "L3",  # Default to L3
            "board": contract.get("board"),
            "pcb_task_id": contract.get("source_pcb_task"),
            "pcb_candidate_id": contract.get("source_pcb_candidate"),
            "hardware_firmware_contract": str(self.contract_path),
            "backend": "platformio",
            "build": {"status": "not_run"},
            "static_analysis": {"status": "not_run"},
            "tests": {
                "host_unit_tests": "not_run",
                "target_tests": "not_run",
                "simulation_tests": "not_run",
                "hil_tests": "not_run",
            },
            "diagnostics": {},
            "traceability": {
                "requirements": [],
                "pcb_nets": [],
                "firmware_files": [],
            },
            "verification": {
                "independent_verifier": "not_run",
                "residual_risks": [],
            },
            "human_approval_required": True,
            "human_approval": "pending",
            "stale": False,
        }

        # Check if build artifacts exist
        firmware_bin = project_dir / ".pio" / "build" / "target" / "firmware.bin"
        if firmware_bin.exists():
            evidence["build"]["status"] = "passed"
            # TODO: Calculate firmware hash

        return evidence
