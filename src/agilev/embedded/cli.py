"""
CLI commands for embedded systems integration.
"""

import argparse
import sys
from pathlib import Path

from agilev.embedded.system_contract import SystemContract


def cmd_embedded_init(args: argparse.Namespace) -> int:
    """Initialize embedded systems structure.

    Args:
        args: Command arguments

    Returns:
        Exit code
    """
    print("Initializing embedded systems structure...")

    # Create directory structure
    base_path = Path.cwd()
    contracts_dir = base_path / ".agentic-agile-v" / "contracts"
    contracts_dir.mkdir(parents=True, exist_ok=True)

    print(f"✓ Created contracts directory: {contracts_dir}")

    # Copy template if requested
    if args.template:
        import shutil

        template_path = Path(__file__).parent.parent.parent.parent / "templates" / "embedded"
        if template_path.exists():
            for template_file in template_path.glob("*.yaml"):
                dest = contracts_dir / template_file.name
                if not dest.exists():
                    shutil.copy(template_file, dest)
                    print(f"✓ Created template: {dest.name}")

    print("\n✓ Embedded systems structure initialized")
    return 0


def cmd_embedded_contract_validate(args: argparse.Namespace) -> int:
    """Validate system contract.

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
        contract = SystemContract.from_file(contract_path)
        print(f"✓ Loaded contract: {contract.contract_id}")

        # Find schema
        schema_path = Path(__file__).parent.parent.parent.parent / "schemas" / "system_contract.schema.json"
        if not schema_path.exists():
            print(f"✗ Schema not found: {schema_path}", file=sys.stderr)
            return 1

        # Validate
        is_valid, errors = contract.validate(schema_path)

        if is_valid:
            print("✓ Contract is valid")

            # Check completeness
            is_complete, missing = contract.check_completeness()
            if is_complete:
                print("✓ Contract is complete")
            else:
                print(f"⚠ Contract is missing: {', '.join(missing)}")
                return 1

            # Show summary
            requirements = contract.get_requirements()
            print(f"\nContract summary:")
            print(f"  Product: {contract.product}")
            print(f"  Revision: {contract.revision}")
            print(f"  Risk level: {contract.risk_level}")
            print(f"  Requirements: {len(requirements)}")
            print(f"  PCB task: {contract.get_pcb_task()}")
            print(f"  Firmware task: {contract.get_firmware_task()}")
            print(f"  Software task: {contract.get_software_task()}")

            return 0
        else:
            print("✗ Contract validation failed:", file=sys.stderr)
            for error in errors:
                print(f"  {error}", file=sys.stderr)
            return 1

    except Exception as e:
        print(f"✗ Error validating contract: {e}", file=sys.stderr)
        return 1


def cmd_embedded_doctor(args: argparse.Namespace) -> int:
    """Check embedded systems environment.

    Args:
        args: Command arguments

    Returns:
        Exit code
    """
    print("Checking embedded systems environment...\n")

    issues = []

    # Check for contracts directory
    contracts_dir = Path.cwd() / ".agentic-agile-v" / "contracts"
    if contracts_dir.exists():
        print(f"✓ Contracts directory exists: {contracts_dir}")
    else:
        print(f"✗ Contracts directory missing: {contracts_dir}")
        issues.append("Run 'agilev embedded init' to create structure")

    # Check for schemas
    schema_dir = Path(__file__).parent.parent.parent.parent / "schemas"
    required_schemas = [
        "system_contract.schema.json",
        "hardware_firmware_contract.schema.json",
        "firmware_software_contract.schema.json",
        "firmware_evidence_bundle.schema.json",
    ]

    for schema_name in required_schemas:
        schema_path = schema_dir / schema_name
        if schema_path.exists():
            print(f"✓ Schema exists: {schema_name}")
        else:
            print(f"✗ Schema missing: {schema_name}")
            issues.append(f"Schema not found: {schema_name}")

    # Check Python dependencies
    try:
        import jsonschema  # noqa: F401

        print("✓ jsonschema available")
    except ImportError:
        print("✗ jsonschema not installed")
        issues.append("Install with: pip install jsonschema")

    try:
        import yaml  # noqa: F401

        print("✓ pyyaml available")
    except ImportError:
        print("✗ pyyaml not installed")
        issues.append("Install with: pip install pyyaml")

    if issues:
        print("\n⚠ Issues found:")
        for issue in issues:
            print(f"  - {issue}")
        return 1
    else:
        print("\n✓ All checks passed")
        return 0


def build_embedded_parser(subparsers: argparse._SubParsersAction) -> None:
    """Build embedded systems CLI parser.

    Args:
        subparsers: Parent subparsers object
    """
    embedded_parser = subparsers.add_parser(
        "embedded", help="Embedded systems integration commands"
    )
    embedded_subparsers = embedded_parser.add_subparsers(dest="embedded_command")

    # embedded init
    init_parser = embedded_subparsers.add_parser("init", help="Initialize embedded systems structure")
    init_parser.add_argument(
        "--template", action="store_true", help="Copy contract templates"
    )
    init_parser.set_defaults(func=cmd_embedded_init)

    # embedded doctor
    doctor_parser = embedded_subparsers.add_parser(
        "doctor", help="Check embedded systems environment"
    )
    doctor_parser.set_defaults(func=cmd_embedded_doctor)

    # embedded contract validate
    contract_parser = embedded_subparsers.add_parser("contract", help="Contract commands")
    contract_subparsers = contract_parser.add_subparsers(dest="contract_command")

    validate_parser = contract_subparsers.add_parser("validate", help="Validate system contract")
    validate_parser.add_argument(
        "--contract",
        default=".agentic-agile-v/contracts/system_contract.yaml",
        help="Path to contract file",
    )
    validate_parser.set_defaults(func=cmd_embedded_contract_validate)
