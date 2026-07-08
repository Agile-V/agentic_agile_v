"""
Renode simulation backend for firmware testing.

Provides virtual hardware testing before deploying to physical devices.
"""

import json
import subprocess
from pathlib import Path
from typing import Any


class RenodeSimulator:
    """Renode simulation runner for firmware."""

    def __init__(self, project_dir: Path):
        """Initialize simulator.

        Args:
            project_dir: Firmware project directory
        """
        self.project_dir = project_dir
        self.renode_config_dir = project_dir / "renode"

    def check_renode_installed(self) -> bool:
        """Check if Renode is installed.

        Returns:
            True if Renode is available
        """
        try:
            result = subprocess.run(
                ["renode", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def generate_platform_script(
        self,
        mcu: str,
        firmware_elf: Path,
    ) -> str:
        """Generate Renode platform script.

        Args:
            mcu: MCU model (e.g., STM32F401, STM32F103)
            firmware_elf: Path to firmware ELF file

        Returns:
            Renode script content
        """
        # Map MCU to Renode platform
        platform_map = {
            "STM32F401": "platforms/cpus/stm32f4.repl",
            "STM32F103": "platforms/cpus/stm32f103.repl",
            "STM32L476": "platforms/cpus/stm32l4.repl",
        }

        platform = platform_map.get(mcu, "platforms/cpus/stm32f4.repl")

        script = f"""# Renode platform script for {mcu}
# Auto-generated - do not edit manually

using sysbus

# Load platform definition
mach create
machine LoadPlatformDescription @{platform}

# Load firmware
sysbus LoadELF @{firmware_elf.absolute()}

# Configure UART for logging
showAnalyzer sysbus.usart2

# Start simulation
start
"""
        return script

    def generate_test_script(
        self,
        platform_script: Path,
        test_commands: list[str],
    ) -> str:
        """Generate Renode test script.

        Args:
            platform_script: Path to platform script
            test_commands: Test commands to execute

        Returns:
            Renode test script content
        """
        script = f"""# Renode test script
# Auto-generated - do not edit manually

# Load platform
i @{platform_script.absolute()}

# Run test commands
"""
        for cmd in test_commands:
            script += f"{cmd}\n"

        script += """
# Quit
quit
"""
        return script

    def create_simulation_config(
        self,
        mcu: str,
        firmware_elf: Path,
        test_commands: list[str] | None = None,
    ) -> dict[str, Path]:
        """Create simulation configuration files.

        Args:
            mcu: MCU model
            firmware_elf: Path to firmware ELF
            test_commands: Optional test commands

        Returns:
            Dictionary of generated file paths
        """
        self.renode_config_dir.mkdir(parents=True, exist_ok=True)

        # Generate platform script
        platform_script_path = self.renode_config_dir / "platform.resc"
        platform_script = self.generate_platform_script(mcu, firmware_elf)
        platform_script_path.write_text(platform_script)

        files = {"platform": platform_script_path}

        # Generate test script if commands provided
        if test_commands:
            test_script_path = self.renode_config_dir / "test.resc"
            test_script = self.generate_test_script(platform_script_path, test_commands)
            test_script_path.write_text(test_script)
            files["test"] = test_script_path

        return files

    def run_simulation(
        self,
        script_path: Path,
        timeout: int = 30,
    ) -> tuple[bool, str]:
        """Run Renode simulation.

        Args:
            script_path: Path to Renode script
            timeout: Timeout in seconds

        Returns:
            Tuple of (success, output)
        """
        if not self.check_renode_installed():
            return False, "Renode not installed. Install from https://renode.io"

        try:
            result = subprocess.run(
                ["renode", "--disable-xwt", "--console", str(script_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.project_dir,
            )

            success = result.returncode == 0
            output = result.stdout + result.stderr

            return success, output

        except subprocess.TimeoutExpired:
            return False, f"Simulation timed out after {timeout}s"
        except Exception as e:
            return False, f"Simulation failed: {e}"

    def extract_test_results(self, output: str) -> dict[str, Any]:
        """Extract test results from simulation output.

        Args:
            output: Simulation output

        Returns:
            Test results dictionary
        """
        results: dict[str, Any] = {
            "passed": False,
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "output": output,
        }

        # Look for common test patterns
        lines = output.split("\n")
        for line in lines:
            # Unity test framework
            if "Tests:" in line:
                # Format: "Tests: 5 Failures: 0 Ignored: 0"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "Tests:" and i + 1 < len(parts):
                        results["tests_run"] = int(parts[i + 1])
                    elif part == "Failures:" and i + 1 < len(parts):
                        results["tests_failed"] = int(parts[i + 1])

                results["tests_passed"] = results["tests_run"] - results["tests_failed"]
                results["passed"] = results["tests_failed"] == 0

            # Custom test markers
            elif "TEST_PASSED" in line:
                results["tests_passed"] += 1
                results["tests_run"] += 1
            elif "TEST_FAILED" in line:
                results["tests_failed"] += 1
                results["tests_run"] += 1

        # If no explicit test results, check for successful execution
        if results["tests_run"] == 0:
            # Look for "ready" or "initialized" messages
            if any(keyword in output.lower() for keyword in ["ready", "initialized", "started"]):
                results["passed"] = True
                results["tests_run"] = 1
                results["tests_passed"] = 1

        return results

    def save_results(
        self,
        results: dict[str, Any],
        output_path: Path,
    ) -> None:
        """Save simulation results.

        Args:
            results: Results dictionary
            output_path: Path to save results
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)
