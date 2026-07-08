"""
PCB import for firmware integration.

Imports hardware-firmware contract data from PCB backend.
"""

import json
from pathlib import Path

import yaml


def generate_contract_from_pcb_export(
    pcb_export_path: Path,
    contract_id: str,
    board_name: str,
    pcb_revision: str,
    output_path: Path,
) -> None:
    """Generate hardware-firmware contract from PCB export.

    Args:
        pcb_export_path: Path to PCB firmware export JSON
        contract_id: Contract ID to use
        board_name: Board name
        pcb_revision: PCB revision
        output_path: Path to write contract YAML

    Raises:
        FileNotFoundError: If PCB export doesn't exist
        ValueError: If export is invalid
    """
    if not pcb_export_path.exists():
        raise FileNotFoundError(f"PCB export not found: {pcb_export_path}")

    # Load PCB export
    with open(pcb_export_path) as f:
        pcb_data = json.load(f)

    # Build contract
    contract = {
        "contract_id": contract_id,
        "board": board_name,
        "pcb_revision": pcb_revision,
        "source_pcb_task": pcb_data.get("task_id"),
        "source_pcb_candidate": pcb_data.get("candidate_id"),
    }

    # Copy MCU info
    if "mcu" in pcb_data:
        contract["mcu"] = pcb_data["mcu"]

    # Copy interfaces
    if "interfaces" in pcb_data:
        contract["interfaces"] = pcb_data["interfaces"]

    # Copy power
    if "power" in pcb_data:
        contract["power"] = pcb_data["power"]

    # Add firmware constraints (defaults)
    contract["firmware_constraints"] = {
        "boot_time_max_ms": 1500,
        "watchdog_required": True,
        "brownout_handling_required": True,
    }

    # Add diagnostics requirements
    contract["diagnostics"] = {
        "required_commands": [
            "i2c_scan",
            "self_test",
        ]
    }

    # Add required evidence
    contract["required_evidence"] = [
        "firmware_build",
        "host_unit_tests",
        "target_build",
        "static_analysis",
        "simulation_test",
        "hardware_in_loop_test",
        "independent_verification",
    ]

    # Write contract
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        yaml.dump(contract, f, default_flow_style=False, sort_keys=False)


def validate_hardware_firmware_contract_against_pcb(
    contract_path: Path, pcb_circuit_path: Path
) -> tuple[bool, list[str]]:
    """Validate hardware-firmware contract against PCB circuit.

    Args:
        contract_path: Path to hardware-firmware contract
        pcb_circuit_path: Path to PCB circuit IR

    Returns:
        Tuple of (is_valid, errors)
    """
    errors: list[str] = []

    # Load contract
    with open(contract_path) as f:
        contract = yaml.safe_load(f)

    # Load PCB circuit
    # TODO: Use actual circuit IR loader when available
    with open(pcb_circuit_path) as f:
        _circuit_data = json.load(f)  # noqa: F841

    # Validate MCU
    if "mcu" in contract:
        _mcu = contract["mcu"]  # noqa: F841
        # Check if MCU exists in circuit
        # TODO: Implement MCU validation

    # Validate interfaces
    if "interfaces" in contract:
        interfaces = contract["interfaces"]

        # Validate I2C
        if "i2c" in interfaces:
            for i2c in interfaces["i2c"]:
                # Check that SDA/SCL nets exist
                # TODO: Implement I2C net validation
                pass

        # Validate SPI
        if "spi" in interfaces:
            for spi in interfaces["spi"]:
                # Check that SPI nets exist
                # TODO: Implement SPI net validation
                pass

    # Validate power rails
    if "power" in contract:
        power = contract["power"]
        if "rails" in power:
            for rail in power["rails"]:
                # Check that power domain exists
                # TODO: Implement power domain validation
                pass

    return len(errors) == 0, errors
