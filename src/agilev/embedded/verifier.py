"""
Cross-domain verifier for embedded systems.

Validates consistency across PCB, firmware, and software domains.
"""

import json
from pathlib import Path
from typing import Any

import yaml


class CrossDomainVerifier:
    """Verifies consistency across PCB, firmware, and software."""

    def __init__(self, project_root: Path):
        """Initialize verifier.

        Args:
            project_root: Project root directory
        """
        self.project_root = project_root
        self.contracts_dir = project_root / ".agentic-agile-v" / "contracts"
        self.pcb_dir = project_root / "pcb"

    def load_circuit_ir(self) -> dict[str, Any] | None:
        """Load PCB circuit IR.

        Returns:
            Circuit IR dictionary or None
        """
        circuit_ir_path = self.pcb_dir / "circuit_ir.json"

        if not circuit_ir_path.exists():
            return None

        with open(circuit_ir_path) as f:
            return json.load(f)

    def load_hw_fw_contract(self) -> dict[str, Any] | None:
        """Load hardware-firmware contract.

        Returns:
            Contract dictionary or None
        """
        contract_path = self.contracts_dir / "hardware_firmware_contract.yaml"

        if not contract_path.exists():
            return None

        with open(contract_path) as f:
            return yaml.safe_load(f)

    def load_fw_sw_contract(self) -> dict[str, Any] | None:
        """Load firmware-software contract.

        Returns:
            Contract dictionary or None
        """
        contract_path = self.contracts_dir / "firmware_software_contract.yaml"

        if not contract_path.exists():
            return None

        with open(contract_path) as f:
            return yaml.safe_load(f)

    def verify_pcb_to_hw_fw_contract(
        self,
        circuit_ir: dict[str, Any],
        hw_fw_contract: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Verify PCB circuit IR matches hardware-firmware contract.

        Args:
            circuit_ir: PCB circuit IR
            hw_fw_contract: Hardware-firmware contract

        Returns:
            List of violations
        """
        violations = []

        # Check MCU match
        pcb_mcu = circuit_ir.get("mcu", {}).get("part_number")
        contract_mcu = hw_fw_contract.get("mcu", {}).get("part_number")

        if pcb_mcu != contract_mcu:
            violations.append(
                {
                    "domain": "pcb_to_firmware",
                    "severity": "error",
                    "message": f"MCU mismatch: PCB has {pcb_mcu}, contract has {contract_mcu}",
                    "pcb_value": pcb_mcu,
                    "contract_value": contract_mcu,
                }
            )

        # Check interfaces
        pcb_interfaces = {iface["name"]: iface for iface in circuit_ir.get("interfaces", [])}
        contract_interfaces = {
            iface["name"]: iface for iface in hw_fw_contract.get("interfaces", [])
        }

        # Check for missing interfaces in contract
        for iface_name, pcb_iface in pcb_interfaces.items():
            if iface_name not in contract_interfaces:
                violations.append(
                    {
                        "domain": "pcb_to_firmware",
                        "severity": "warning",
                        "message": f"Interface '{iface_name}' in PCB but not in contract",
                        "interface": iface_name,
                    }
                )
            else:
                # Verify interface details match
                contract_iface = contract_interfaces[iface_name]

                # Check type
                if pcb_iface.get("type") != contract_iface.get("type"):
                    violations.append(
                        {
                            "domain": "pcb_to_firmware",
                            "severity": "error",
                            "message": f"Interface '{iface_name}' type mismatch",
                            "pcb_type": pcb_iface.get("type"),
                            "contract_type": contract_iface.get("type"),
                        }
                    )

                # Check pins
                pcb_pins = pcb_iface.get("pins", {})
                contract_pins = contract_iface.get("pins", {})

                for pin_name, pcb_pin in pcb_pins.items():
                    if pin_name not in contract_pins:
                        violations.append(
                            {
                                "domain": "pcb_to_firmware",
                                "severity": "warning",
                                "message": (
                                    f"Pin '{pin_name}' in interface '{iface_name}' "
                                    "missing from contract"
                                ),
                                "interface": iface_name,
                                "pin": pin_name,
                            }
                        )
                    elif pcb_pin != contract_pins[pin_name]:
                        violations.append(
                            {
                                "domain": "pcb_to_firmware",
                                "severity": "error",
                                "message": f"Pin '{pin_name}' mismatch in interface '{iface_name}'",
                                "pcb_pin": pcb_pin,
                                "contract_pin": contract_pins[pin_name],
                            }
                        )

        # Check for contract interfaces not in PCB
        for iface_name in contract_interfaces:
            if iface_name not in pcb_interfaces:
                violations.append(
                    {
                        "domain": "pcb_to_firmware",
                        "severity": "error",
                        "message": (
                            f"Interface '{iface_name}' in contract but not in PCB "
                            "(firmware invented hardware!)"
                        ),
                        "interface": iface_name,
                    }
                )

        return violations

    def verify_fw_to_fw_sw_contract(
        self,
        hw_fw_contract: dict[str, Any],
        fw_sw_contract: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Verify firmware-software contract is achievable by firmware.

        Args:
            hw_fw_contract: Hardware-firmware contract
            fw_sw_contract: Firmware-software contract

        Returns:
            List of violations
        """
        violations = []

        # Check if firmware has necessary interfaces for software contract
        fw_interfaces = {iface["name"]: iface for iface in hw_fw_contract.get("interfaces", [])}

        # Check transport availability
        transport = fw_sw_contract.get("transport", "")

        if "usb" in transport.lower():
            if "USB" not in fw_interfaces:
                violations.append(
                    {
                        "domain": "firmware_to_software",
                        "severity": "error",
                        "message": (
                            f"Software contract requires {transport} but firmware has "
                            "no USB interface"
                        ),
                        "transport": transport,
                    }
                )

        elif "uart" in transport.lower() or "serial" in transport.lower():
            uart_found = any("UART" in name or "USART" in name for name in fw_interfaces)
            if not uart_found:
                violations.append(
                    {
                        "domain": "firmware_to_software",
                        "severity": "error",
                        "message": (
                            f"Software contract requires {transport} but firmware has "
                            "no UART interface"
                        ),
                        "transport": transport,
                    }
                )

        # Check if commands reference valid sensors/peripherals
        commands = fw_sw_contract.get("commands", [])

        for cmd in commands:
            cmd_name = cmd.get("name", "")

            # Check for temperature commands without temperature sensor
            if "temperature" in cmd_name.lower():
                i2c_interfaces = [name for name in fw_interfaces if "I2C" in name]
                if not i2c_interfaces:
                    violations.append(
                        {
                            "domain": "firmware_to_software",
                            "severity": "warning",
                            "message": (
                                f"Command '{cmd_name}' implies temperature sensor but "
                                "no I2C interface found"
                            ),
                            "command": cmd_name,
                        }
                    )

        return violations

    def verify_all(self) -> dict[str, Any]:
        """Verify all cross-domain contracts.

        Returns:
            Verification results
        """
        results = {
            "passed": True,
            "violations": [],
            "warnings": [],
            "errors": [],
        }

        # Load all artifacts
        circuit_ir = self.load_circuit_ir()
        hw_fw_contract = self.load_hw_fw_contract()
        fw_sw_contract = self.load_fw_sw_contract()

        # Track what's available
        availability = {
            "circuit_ir": circuit_ir is not None,
            "hw_fw_contract": hw_fw_contract is not None,
            "fw_sw_contract": fw_sw_contract is not None,
        }

        results["availability"] = availability

        # Verify PCB ↔ Firmware
        if circuit_ir and hw_fw_contract:
            pcb_fw_violations = self.verify_pcb_to_hw_fw_contract(circuit_ir, hw_fw_contract)
            results["violations"].extend(pcb_fw_violations)

        # Verify Firmware ↔ Software
        if hw_fw_contract and fw_sw_contract:
            fw_sw_violations = self.verify_fw_to_fw_sw_contract(hw_fw_contract, fw_sw_contract)
            results["violations"].extend(fw_sw_violations)

        # Categorize violations
        for violation in results["violations"]:
            if violation["severity"] == "error":
                results["errors"].append(violation)
                results["passed"] = False
            else:
                results["warnings"].append(violation)

        results["summary"] = {
            "total_violations": len(results["violations"]),
            "errors": len(results["errors"]),
            "warnings": len(results["warnings"]),
        }

        return results

    def save_results(self, results: dict[str, Any], output_path: Path) -> None:
        """Save verification results.

        Args:
            results: Verification results
            output_path: Output path
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)
