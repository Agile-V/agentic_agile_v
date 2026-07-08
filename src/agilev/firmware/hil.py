"""
Hardware-in-the-Loop (HIL) test runner.

Executes firmware tests on real hardware with automated validation.
"""

import json
import subprocess
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import serial


class HILRunner:
    """Hardware-in-the-Loop test runner."""

    def __init__(self, project_dir: Path):
        """Initialize HIL runner.

        Args:
            project_dir: Firmware project directory
        """
        self.project_dir = project_dir
        self.hil_config_dir = project_dir / "hil"

    def flash_firmware(
        self,
        port: str,
        firmware_path: Path | None = None,
    ) -> tuple[bool, str]:
        """Flash firmware to hardware.

        Args:
            port: Serial port for flashing
            firmware_path: Path to firmware binary (auto-detected if None)

        Returns:
            Tuple of (success, output)
        """
        if firmware_path is None:
            # Find firmware binary
            build_dir = self.project_dir / ".pio" / "build"
            bin_files = list(build_dir.rglob("*.bin")) if build_dir.exists() else []

            if not bin_files:
                return False, "No firmware binary found. Run 'agilev firmware build' first."

            firmware_path = bin_files[0]

        try:
            # Use platformio to flash
            result = subprocess.run(
                ["pio", "run", "--target", "upload", "--upload-port", port],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.project_dir,
            )

            success = result.returncode == 0
            output = result.stdout + result.stderr

            return success, output

        except subprocess.TimeoutExpired:
            return False, "Flash timeout after 60s"
        except FileNotFoundError:
            return False, "PlatformIO not found. Install with: pip install platformio"
        except Exception as e:
            return False, f"Flash failed: {e}"

    def connect_serial(
        self,
        port: str,
        baudrate: int = 115200,
        timeout: float = 1.0,
    ) -> "serial.Serial":
        """Connect to hardware serial port.

        Args:
            port: Serial port
            baudrate: Baud rate
            timeout: Read timeout in seconds

        Returns:
            Serial connection
        """
        try:
            import serial as _serial  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError(
                "pyserial is required for HIL tests. Install with: pip install pyserial"
            ) from exc
        return _serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=timeout,
        )

    def wait_for_ready(
        self,
        ser: "serial.Serial",
        timeout: float = 5.0,
        ready_marker: str = "READY",
    ) -> bool:
        """Wait for firmware ready signal.

        Args:
            ser: Serial connection
            timeout: Timeout in seconds
            ready_marker: Ready marker string

        Returns:
            True if ready signal received
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            if ser.in_waiting:
                line = ser.readline().decode(errors="ignore").strip()
                if ready_marker in line:
                    return True

            time.sleep(0.1)

        return False

    def send_command(
        self,
        ser: "serial.Serial",
        command: str,
        timeout: float = 1.0,
    ) -> str | None:
        """Send command to firmware.

        Args:
            ser: Serial connection
            command: Command string
            timeout: Response timeout

        Returns:
            Response string or None
        """
        # Send command
        ser.write(f"{command}\n".encode())
        ser.flush()

        # Wait for response
        start_time = time.time()
        response_lines = []

        while time.time() - start_time < timeout:
            if ser.in_waiting:
                line = ser.readline().decode(errors="ignore").strip()
                if line:
                    response_lines.append(line)

                    # Check for end marker
                    if line.endswith("OK") or line.endswith("ERROR"):
                        break

            time.sleep(0.01)

        return "\n".join(response_lines) if response_lines else None

    def run_test_sequence(
        self,
        ser: "serial.Serial",
        test_sequence: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Run test sequence.

        Args:
            ser: Serial connection
            test_sequence: List of test steps

        Returns:
            List of test results
        """
        results = []

        for step in test_sequence:
            step_name = step["name"]
            command = step["command"]
            expected = step.get("expected", None)
            timeout = step.get("timeout", 1.0)

            # Send command
            response = self.send_command(ser, command, timeout)

            # Check result
            passed = True
            if expected:
                if isinstance(expected, str):
                    passed = expected in response if response else False
                elif isinstance(expected, list):
                    passed = all(exp in response for exp in expected) if response else False

            result = {
                "name": step_name,
                "command": command,
                "response": response,
                "expected": expected,
                "passed": passed,
            }

            results.append(result)

            # Stop on failure if configured
            if not passed and step.get("stop_on_failure", False):
                break

        return results

    def load_test_config(self, config_path: Path) -> dict[str, Any]:
        """Load HIL test configuration.

        Args:
            config_path: Path to test config JSON

        Returns:
            Test configuration dictionary
        """
        with open(config_path) as f:
            return json.load(f)

    def save_results(
        self,
        results: list[dict[str, Any]],
        output_path: Path,
    ) -> None:
        """Save HIL test results.

        Args:
            results: Test results
            output_path: Output path
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        summary = {
            "total": len(results),
            "passed": sum(1 for r in results if r["passed"]),
            "failed": sum(1 for r in results if not r["passed"]),
            "results": results,
        }

        with open(output_path, "w") as f:
            json.dump(summary, f, indent=2)

    def run_hil_test(
        self,
        port: str,
        config_path: Path | None = None,
        flash_first: bool = True,
    ) -> tuple[bool, dict[str, Any]]:
        """Run complete HIL test.

        Args:
            port: Serial port
            config_path: Path to test config (optional)
            flash_first: Flash firmware before testing

        Returns:
            Tuple of (success, results)
        """
        # Flash firmware if requested
        if flash_first:
            flash_success, flash_output = self.flash_firmware(port)
            if not flash_success:
                return False, {"error": "Flash failed", "output": flash_output}

            # Wait for device to restart
            time.sleep(2)

        # Load test config
        if config_path is None:
            config_path = self.hil_config_dir / "test_config.json"

        if not config_path.exists():
            return False, {"error": f"Test config not found: {config_path}"}

        config = self.load_test_config(config_path)

        # Connect to device
        try:
            ser = self.connect_serial(
                port=port,
                baudrate=config.get("baudrate", 115200),
            )
        except Exception as e:
            return False, {"error": f"Serial connection failed: {e}"}

        try:
            # Wait for ready signal
            ready_marker = config.get("ready_marker", "READY")
            ready_timeout = config.get("ready_timeout", 5.0)

            if not self.wait_for_ready(ser, ready_timeout, ready_marker):
                return False, {"error": f"Device not ready after {ready_timeout}s"}

            # Run test sequence
            test_sequence = config.get("test_sequence", [])
            results = self.run_test_sequence(ser, test_sequence)

            # Check overall success
            all_passed = all(r["passed"] for r in results)

            return all_passed, {
                "passed": all_passed,
                "total": len(results),
                "results": results,
            }

        finally:
            ser.close()
