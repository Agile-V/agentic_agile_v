"""
CLI commands for firmware integration.
"""

import argparse
import sys
from pathlib import Path

from agilev.firmware.contract import (
    FirmwareSoftwareContract,
    HardwareFirmwareContract,
)
from agilev.firmware.pcb_import import generate_contract_from_pcb_export


def cmd_firmware_contract_generate(args: argparse.Namespace) -> int:
    """Generate hardware-firmware contract from PCB export.

    Args:
        args: Command arguments

    Returns:
        Exit code
    """
    pcb_export_path = Path(args.from_pcb)
    output_path = Path(args.output)

    if not pcb_export_path.exists():
        print(f"✗ PCB export not found: {pcb_export_path}", file=sys.stderr)
        return 1

    try:
        # Generate contract
        generate_contract_from_pcb_export(
            pcb_export_path=pcb_export_path,
            contract_id=args.contract_id,
            board_name=args.board,
            pcb_revision=args.revision,
            output_path=output_path,
        )

        print(f"✓ Generated hardware-firmware contract: {output_path}")
        print(f"  Contract ID: {args.contract_id}")
        print(f"  Board: {args.board}")
        print(f"  PCB revision: {args.revision}")
        print(f"\nNext steps:")
        print(f"  1. Review contract: {output_path}")
        print(f"  2. Validate: agilev firmware contract validate {output_path}")
        print(f"  3. Generate firmware: agilev firmware generate --task AAV-FW-XXX")

        return 0

    except Exception as e:
        print(f"✗ Error generating contract: {e}", file=sys.stderr)
        import traceback

        if args.verbose:
            traceback.print_exc()
        return 1


def cmd_firmware_contract_validate(args: argparse.Namespace) -> int:
    """Validate firmware contract.

    Args:
        args: Command arguments

    Returns:
        Exit code
    """
    contract_path = Path(args.contract)

    if not contract_path.exists():
        print(f"✗ Contract not found: {contract_path}", file=sys.stderr)
        return 1

    try:
        # Determine contract type from filename or content
        if "hardware_firmware" in contract_path.name or args.type == "hardware-firmware":
            contract = HardwareFirmwareContract.from_file(contract_path)
            schema_name = "hardware_firmware_contract.schema.json"
            print(f"✓ Loaded hardware-firmware contract: {contract.contract_id}")
        elif "firmware_software" in contract_path.name or args.type == "firmware-software":
            contract = FirmwareSoftwareContract.from_file(contract_path)
            schema_name = "firmware_software_contract.schema.json"
            print(f"✓ Loaded firmware-software contract: {contract.contract_id}")
        else:
            print(f"✗ Cannot determine contract type. Use --type option.", file=sys.stderr)
            return 1

        # Find schema
        schema_path = Path(__file__).parent.parent.parent.parent / "schemas" / schema_name
        if not schema_path.exists():
            print(f"✗ Schema not found: {schema_path}", file=sys.stderr)
            return 1

        # Validate
        is_valid, errors = contract.validate(schema_path)

        if is_valid:
            print("✓ Contract is valid")

            # Show summary
            if isinstance(contract, HardwareFirmwareContract):
                mcu = contract.get_mcu()
                interfaces = contract.get_interfaces()
                rails = contract.get_power_rails()

                print(f"\nContract summary:")
                print(f"  Board: {contract.board}")
                print(f"  PCB revision: {contract.pcb_revision}")
                print(f"  MCU: {mcu.get('part_number', 'N/A')}")
                print(f"  Package: {mcu.get('package', 'N/A')}")
                print(f"  Voltage domain: {mcu.get('voltage_domain', 'N/A')}")
                print(f"  I2C buses: {len(interfaces.get('i2c', []))}")
                print(f"  SPI buses: {len(interfaces.get('spi', []))}")
                print(f"  UART buses: {len(interfaces.get('uart', []))}")
                print(f"  ADC channels: {len(interfaces.get('adc', []))}")
                print(f"  GPIO pins: {len(interfaces.get('gpio', []))}")
                print(f"  Power rails: {len(rails)}")

            elif isinstance(contract, FirmwareSoftwareContract):
                commands = contract.get_commands()
                errors = contract.get_error_codes()

                print(f"\nContract summary:")
                print(f"  Transport: {contract.transport}")
                print(f"  Protocol version: {contract.protocol_version}")
                print(f"  Commands: {len(commands)}")
                print(f"  Error codes: {len(errors)}")

                if args.verbose:
                    print(f"\n  Command list:")
                    for cmd in commands:
                        print(f"    - {cmd['name']}")

            return 0
        else:
            print("✗ Contract validation failed:", file=sys.stderr)
            for error in errors:
                print(f"  {error}", file=sys.stderr)
            return 1

    except Exception as e:
        print(f"✗ Error validating contract: {e}", file=sys.stderr)
        import traceback

        if args.verbose:
            traceback.print_exc()
        return 1


def build_firmware_parser(subparsers: argparse._SubParsersAction) -> None:
    """Build firmware CLI parser.

    Args:
        subparsers: Parent subparsers object
    """
    firmware_parser = subparsers.add_parser("firmware", help="Firmware integration commands")
    firmware_subparsers = firmware_parser.add_subparsers(dest="firmware_command")

    # firmware contract
    contract_parser = firmware_subparsers.add_parser("contract", help="Contract commands")
    contract_subparsers = contract_parser.add_subparsers(dest="contract_command")

    # firmware contract generate
    generate_parser = contract_subparsers.add_parser(
        "generate", help="Generate hardware-firmware contract from PCB"
    )
    generate_parser.add_argument(
        "--from-pcb", required=True, help="Path to PCB firmware export JSON"
    )
    generate_parser.add_argument("--contract-id", required=True, help="Contract ID (e.g., HFC-001)")
    generate_parser.add_argument("--board", required=True, help="Board name")
    generate_parser.add_argument("--revision", required=True, help="PCB revision (e.g., rev_a)")
    generate_parser.add_argument(
        "--output",
        default=".agentic-agile-v/contracts/hardware_firmware_contract.yaml",
        help="Output contract path",
    )
    generate_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed output"
    )
    generate_parser.set_defaults(func=cmd_firmware_contract_generate)

    # firmware contract validate
    validate_parser = contract_subparsers.add_parser("validate", help="Validate firmware contract")
    validate_parser.add_argument("contract", help="Path to contract file")
    validate_parser.add_argument(
        "--type",
        choices=["hardware-firmware", "firmware-software"],
        help="Contract type (auto-detected from filename if not specified)",
    )
    validate_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed output"
    )
    validate_parser.set_defaults(func=cmd_firmware_contract_validate)
