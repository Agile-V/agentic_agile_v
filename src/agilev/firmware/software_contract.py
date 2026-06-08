"""
Firmware-software contract generator.

Generates firmware-software contracts from firmware implementations.
"""

from pathlib import Path
from typing import Any

import yaml


class FirmwareSoftwareContractGenerator:
    """Generates firmware-software contracts from firmware code."""

    def __init__(self, project_dir: Path):
        """Initialize generator.

        Args:
            project_dir: Firmware project directory
        """
        self.project_dir = project_dir

    def generate_contract(
        self,
        contract_id: str,
        firmware_task_id: str,
        transport: str = "usb_cdc_serial",
        protocol_version: int = 1,
    ) -> dict[str, Any]:
        """Generate firmware-software contract.

        Args:
            contract_id: Contract identifier (e.g., FSC-001)
            firmware_task_id: Source firmware task ID
            transport: Communication transport
            protocol_version: Protocol version number

        Returns:
            Firmware-software contract dictionary
        """
        contract = {
            "contract_id": contract_id,
            "source_firmware_task": firmware_task_id,
            "transport": transport,
            "protocol_version": protocol_version,
            "commands": [],
            "error_codes": [],
            "software_expectations": {
                "retries": {
                    "max_attempts": 3,
                    "backoff_ms": 100,
                    "backoff_strategy": "linear",
                },
                "data_freshness_max_ms": 500,
                "connection_timeout_ms": 1000,
            },
            "required_evidence": [
                "firmware_protocol_tests",
                "software_api_tests",
                "end_to_end_protocol_test",
            ],
        }

        # Extract commands from firmware (basic implementation)
        commands = self._extract_commands()
        if commands:
            contract["commands"] = commands

        # Extract error codes
        error_codes = self._extract_error_codes()
        if error_codes:
            contract["error_codes"] = error_codes

        return contract

    def _extract_commands(self) -> list[dict[str, Any]]:
        """Extract commands from firmware source.

        Returns:
            List of command definitions
        """
        # This is a basic implementation - in production, would parse firmware code
        commands = []

        # Look for common patterns in firmware code
        src_files = list((self.project_dir / "src").rglob("*.cpp")) if (
            self.project_dir / "src"
        ).exists() else []

        for src_file in src_files:
            try:
                content = src_file.read_text()

                # Look for command handlers (basic pattern matching)
                if "get_temperature" in content.lower():
                    commands.append(
                        {
                            "name": "get_temperature",
                            "request": {"type": "object", "fields": []},
                            "response": {
                                "type": "object",
                                "fields": {
                                    "temperature_c": {"type": "number", "unit": "celsius"},
                                    "timestamp_ms": {"type": "integer"},
                                    "status": {
                                        "type": "string",
                                        "enum": ["ok", "sensor_missing", "bus_error"],
                                    },
                                },
                            },
                            "max_response_time_ms": 50,
                        }
                    )

                if "diagnostic" in content.lower() or "self_test" in content.lower():
                    commands.append(
                        {
                            "name": "run_diagnostics",
                            "request": {"type": "object", "fields": []},
                            "response": {
                                "type": "object",
                                "fields": {
                                    "i2c_scan": {"type": "string", "enum": ["passed", "failed"]},
                                    "self_test": {"type": "string", "enum": ["passed", "failed"]},
                                    "firmware_version": {"type": "string"},
                                },
                            },
                            "max_response_time_ms": 200,
                        }
                    )

            except Exception:
                continue

        return commands

    def _extract_error_codes(self) -> list[dict[str, str]]:
        """Extract error codes from firmware.

        Returns:
            List of error code definitions
        """
        error_codes = [
            {
                "code": "SENSOR_MISSING",
                "meaning": "Sensor did not respond at expected address",
                "recoverable": False,
            },
            {
                "code": "BUS_ERROR",
                "meaning": "Communication bus transaction failed",
                "recoverable": True,
            },
            {
                "code": "NOT_READY",
                "meaning": "Firmware not yet initialized",
                "recoverable": True,
            },
        ]

        return error_codes

    def save_contract(self, contract: dict[str, Any], output_path: Path) -> None:
        """Save contract to YAML file.

        Args:
            contract: Contract dictionary
            output_path: Path to save contract
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            yaml.dump(contract, f, default_flow_style=False, sort_keys=False)
