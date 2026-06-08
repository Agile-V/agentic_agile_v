"""
System contract management for embedded systems integration.

Handles system contracts that link product requirements to PCB, firmware, and software tasks.
"""

import json
from pathlib import Path
from typing import Any

import yaml


class SystemContract:
    """System contract linking requirements to PCB/firmware/software."""

    def __init__(self, contract_data: dict[str, Any]):
        """Initialize system contract.

        Args:
            contract_data: Contract data dictionary
        """
        self.data = contract_data
        self.contract_id = contract_data["contract_id"]
        self.product = contract_data["product"]
        self.revision = contract_data["revision"]
        self.risk_level = contract_data["risk_level"]

    @classmethod
    def from_file(cls, path: Path) -> "SystemContract":
        """Load system contract from YAML file.

        Args:
            path: Path to contract YAML file

        Returns:
            SystemContract instance

        Raises:
            FileNotFoundError: If contract file doesn't exist
            ValueError: If contract is invalid
        """
        if not path.exists():
            raise FileNotFoundError(f"System contract not found: {path}")

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
        try:
            import jsonschema

            with open(schema_path) as f:
                schema = json.load(f)

            jsonschema.validate(instance=self.data, schema=schema)
            return True, []
        except jsonschema.ValidationError as e:
            return False, [str(e)]
        except Exception as e:
            return False, [f"Validation error: {e}"]

    def get_requirements(self) -> list[dict[str, str]]:
        """Get list of requirements from contract.

        Returns:
            List of requirement dictionaries
        """
        return self.data.get("requirements", [])

    def get_pcb_task(self) -> str | None:
        """Get PCB task ID.

        Returns:
            PCB task ID or None
        """
        pcb = self.data.get("pcb", {})
        return pcb.get("task_id")

    def get_firmware_task(self) -> str | None:
        """Get firmware task ID.

        Returns:
            Firmware task ID or None
        """
        firmware = self.data.get("firmware", {})
        return firmware.get("task_id")

    def get_software_task(self) -> str | None:
        """Get software task ID.

        Returns:
            Software task ID or None
        """
        software = self.data.get("software", {})
        return software.get("task_id")

    def get_required_evidence(self) -> list[str]:
        """Get list of required evidence types.

        Returns:
            List of evidence type identifiers
        """
        integration = self.data.get("integration", {})
        return integration.get("required_evidence", [])

    def check_completeness(self) -> tuple[bool, list[str]]:
        """Check if contract has all required sections.

        Returns:
            Tuple of (is_complete, missing_items)
        """
        missing = []

        if not self.get_requirements():
            missing.append("requirements")

        pcb = self.data.get("pcb")
        if not pcb:
            missing.append("pcb section")
        elif not pcb.get("task_id"):
            missing.append("pcb.task_id")

        firmware = self.data.get("firmware")
        if not firmware:
            missing.append("firmware section")
        elif not firmware.get("task_id"):
            missing.append("firmware.task_id")

        software = self.data.get("software")
        if not software:
            missing.append("software section")
        elif not software.get("task_id"):
            missing.append("software.task_id")

        return len(missing) == 0, missing
