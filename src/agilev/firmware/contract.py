"""
Firmware contract management.

Handles hardware-firmware and firmware-software contracts.
"""

import json
from pathlib import Path
from typing import Any

import yaml

try:
    import jsonschema as _jsonschema

    _JSONSCHEMA_AVAILABLE = True
except ImportError:
    _jsonschema = None  # type: ignore[assignment]
    _JSONSCHEMA_AVAILABLE = False


class HardwareFirmwareContract:
    """Hardware-firmware contract defining PCB capabilities for firmware."""

    def __init__(self, contract_data: dict[str, Any]):
        """Initialize hardware-firmware contract.

        Args:
            contract_data: Contract data dictionary
        """
        self.data = contract_data
        self.contract_id = contract_data["contract_id"]
        self.board = contract_data["board"]
        self.pcb_revision = contract_data["pcb_revision"]

    @classmethod
    def from_file(cls, path: Path) -> "HardwareFirmwareContract":
        """Load contract from YAML file.

        Args:
            path: Path to contract YAML file

        Returns:
            HardwareFirmwareContract instance
        """
        if not path.exists():
            raise FileNotFoundError(f"Hardware-firmware contract not found: {path}")

        with open(path) as f:
            data = yaml.safe_load(f)

        return cls(data)

    def validate(self, schema_path: Path) -> tuple[bool, list[str]]:
        """Validate contract against JSON schema.

        Args:
            schema_path: Path to JSON schema file

        Returns:
            Tuple of (is_valid, errors)
        """
        if not _JSONSCHEMA_AVAILABLE or _jsonschema is None:
            return False, ["jsonschema not installed"]
        try:
            with open(schema_path) as f:
                schema = json.load(f)

            _jsonschema.validate(instance=self.data, schema=schema)
            return True, []
        except _jsonschema.ValidationError as e:
            return False, [str(e)]
        except Exception as e:
            return False, [f"Validation error: {e}"]

    def get_mcu(self) -> dict[str, Any]:
        """Get MCU configuration.

        Returns:
            MCU configuration dictionary
        """
        return self.data.get("mcu", {})

    def get_interfaces(self) -> dict[str, Any]:
        """Get interface definitions (I2C, SPI, UART, etc.).

        Returns:
            Interfaces dictionary
        """
        return self.data.get("interfaces", {})

    def get_power_rails(self) -> list[dict[str, Any]]:
        """Get power rail definitions.

        Returns:
            List of power rail dictionaries
        """
        power = self.data.get("power", {})
        return power.get("rails", [])


class FirmwareSoftwareContract:
    """Firmware-software contract defining firmware API for software."""

    def __init__(self, contract_data: dict[str, Any]):
        """Initialize firmware-software contract.

        Args:
            contract_data: Contract data dictionary
        """
        self.data = contract_data
        self.contract_id = contract_data["contract_id"]
        self.transport = contract_data["transport"]
        self.protocol_version = contract_data["protocol_version"]

    @classmethod
    def from_file(cls, path: Path) -> "FirmwareSoftwareContract":
        """Load contract from YAML file.

        Args:
            path: Path to contract YAML file

        Returns:
            FirmwareSoftwareContract instance
        """
        if not path.exists():
            raise FileNotFoundError(f"Firmware-software contract not found: {path}")

        with open(path) as f:
            data = yaml.safe_load(f)

        return cls(data)

    def validate(self, schema_path: Path) -> tuple[bool, list[str]]:
        """Validate contract against JSON schema.

        Args:
            schema_path: Path to JSON schema file

        Returns:
            Tuple of (is_valid, errors)
        """
        if not _JSONSCHEMA_AVAILABLE or _jsonschema is None:
            return False, ["jsonschema not installed"]
        try:
            with open(schema_path) as f:
                schema = json.load(f)

            _jsonschema.validate(instance=self.data, schema=schema)
            return True, []
        except _jsonschema.ValidationError as e:
            return False, [str(e)]
        except Exception as e:
            return False, [f"Validation error: {e}"]

    def get_commands(self) -> list[dict[str, Any]]:
        """Get list of protocol commands.

        Returns:
            List of command dictionaries
        """
        return self.data.get("commands", [])

    def get_error_codes(self) -> list[dict[str, str]]:
        """Get list of error codes.

        Returns:
            List of error code dictionaries
        """
        return self.data.get("error_codes", [])
