"""
CLI commands for embedded systems integration.
"""

import argparse
import sys
from pathlib import Path

from agilev.embedded.release_gate import EmbeddedReleaseGate
from agilev.embedded.system_contract import SystemContract
from agilev.embedded.verifier import CrossDomainVerifier


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
        schema_path = (
            Path(__file__).parent.parent.parent.parent
            / "schemas"
            / "system_contract.schema.json"
        )
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
            print("\nContract summary:")
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


def cmd_embedded_verify(args: argparse.Namespace) -> int:
    """Verify cross-domain contract consistency.

    Args:
        args: Command arguments

    Returns:
        Exit code
    """
    project_root = Path(args.root) if args.root else Path.cwd()

    try:
        verifier = CrossDomainVerifier(project_root)

        print("Verifying cross-domain contracts...")
        print(f"  Project: {project_root}")

        results = verifier.verify_all()

        # Print availability
        print("\nArtifact availability:")
        for artifact, available in results["availability"].items():
            status = "✓" if available else "✗"
            print(f"  {status} {artifact}")

        # Print violations
        if results["violations"]:
            print(f"\n⚠ Found {len(results['violations'])} violations:")

            if results["errors"]:
                print(f"\nErrors ({len(results['errors'])}):")
                for error in results["errors"]:
                    print(f"  ✗ [{error['domain']}] {error['message']}")

            if results["warnings"]:
                print(f"\nWarnings ({len(results['warnings'])}):")
                for warning in results["warnings"]:
                    print(f"  ⚠ [{warning['domain']}] {warning['message']}")

        # Save results
        results_path = project_root / ".agentic-agile-v" / "verification" / "cross_domain.json"
        verifier.save_results(results, results_path)
        print(f"\nResults saved: {results_path}")

        if results["passed"]:
            print("\n✓ Cross-domain verification passed")
            return 0
        else:
            print("\n✗ Cross-domain verification failed", file=sys.stderr)
            print(f"  Errors: {results['summary']['errors']}", file=sys.stderr)
            print(f"  Warnings: {results['summary']['warnings']}", file=sys.stderr)
            return 1

    except Exception as e:
        print(f"✗ Verification failed: {e}", file=sys.stderr)
        import traceback

        if args.verbose:
            traceback.print_exc()
        return 1


def cmd_embedded_gate(args: argparse.Namespace) -> int:
    """Check embedded release gate.

    Args:
        args: Command arguments

    Returns:
        Exit code
    """
    project_root = Path(args.root) if args.root else Path.cwd()

    try:
        gate = EmbeddedReleaseGate(project_root)

        print("Checking release gate...")
        print(f"  Project: {project_root}")
        print(f"  Task: {args.task_id}")
        print(f"  Risk level: {args.risk_level}")

        results = gate.check_gate(
            task_id=args.task_id,
            risk_level=args.risk_level,
            firmware_task_id=args.firmware_task,
        )

        # Print checks
        print("\nGate checks:")
        for check in results["checks"]:
            status = "✓" if check["passed"] else "✗"
            print(f"  {status} {check['name']}: {check['message']}")

        # Print blockers
        if results["blockers"]:
            print(f"\n🚫 Blockers ({len(results['blockers'])}):")
            for blocker in results["blockers"]:
                print(f"  - {blocker}")

        # Print warnings
        if results["warnings"]:
            print(f"\n⚠ Warnings ({len(results['warnings'])}):")
            for warning in results["warnings"]:
                print(f"  - {warning}")

        # Save results
        results_path = project_root / ".agentic-agile-v" / "gates" / f"{args.task_id}_gate.json"
        gate.save_gate_results(results, results_path)
        print(f"\nResults saved: {results_path}")

        if results["passed"]:
            print("\n✓ Release gate PASSED - task may proceed")
            return 0
        else:
            print("\n✗ Release gate FAILED - task is BLOCKED", file=sys.stderr)
            print(f"  Blockers: {len(results['blockers'])}", file=sys.stderr)
            return 1

    except Exception as e:
        print(f"✗ Gate check failed: {e}", file=sys.stderr)
        import traceback

        if args.verbose:
            traceback.print_exc()
        return 1


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
    init_parser = embedded_subparsers.add_parser(
        "init", help="Initialize embedded systems structure"
    )
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

    # embedded verify
    verify_parser = embedded_subparsers.add_parser(
        "verify", help="Verify cross-domain contract consistency"
    )
    verify_parser.add_argument("--root", help="Project root directory (default: current dir)")
    verify_parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    verify_parser.set_defaults(func=cmd_embedded_verify)

    # embedded gate
    gate_parser = embedded_subparsers.add_parser(
        "gate", help="Check embedded release gate"
    )
    gate_parser.add_argument("--task-id", required=True, help="Task identifier")
    gate_parser.add_argument(
        "--risk-level",
        required=True,
        choices=["L0", "L1", "L2", "L3", "L4"],
        help="Risk level",
    )
    gate_parser.add_argument("--firmware-task", help="Firmware task ID (optional)")
    gate_parser.add_argument("--root", help="Project root directory (default: current dir)")
    gate_parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    gate_parser.set_defaults(func=cmd_embedded_gate)
