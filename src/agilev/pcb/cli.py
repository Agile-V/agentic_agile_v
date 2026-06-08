"""
PCB CLI Commands

Command-line interface for PCB development tasks.
Extends the main agilev CLI with PCB-specific commands.
"""

import argparse
from pathlib import Path

from .circuit_ir import CircuitIR
from .component_index import ComponentIndex
from .kicad_cli import KiCadCLI
from .validators import generate_validation_report, validate_circuit


def cmd_pcb_validate(args: argparse.Namespace) -> int:
    """Validate a PCB candidate."""
    task_id = args.task
    candidate_id = args.candidate or "candidate_001"

    # Load circuit IR
    circuit_path = Path(
        f".agentic-agile-v/tasks/{task_id}/candidates/{candidate_id}/circuit_ir.json"
    )

    if not circuit_path.exists():
        print(f"❌ Circuit IR not found: {circuit_path}")
        return 1

    print(f"📋 Loading circuit IR from {circuit_path}")
    circuit = CircuitIR.load(circuit_path)

    # Validate circuit structure
    print("\n🔍 Validating circuit structure...")
    connection_errors = circuit.validate_connections()

    if connection_errors:
        print(f"❌ Found {len(connection_errors)} connection errors:")
        for error in connection_errors:
            print(f"  - {error}")
        return 1
    else:
        print("✅ Circuit structure valid")

    # Run semantic validators
    print("\n🔍 Running semantic validators...")
    validation_results = validate_circuit(circuit)

    # Generate report
    report = generate_validation_report(validation_results)

    # Save report
    report_path = circuit_path.parent / "validation" / "semantic_validation.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report)

    print(f"\n{report}")
    print(f"\n💾 Report saved to: {report_path}")

    # Check if validation passed
    total_errors = sum(len(r.errors) for r in validation_results.values())

    if total_errors > 0:
        print(f"\n❌ Validation failed with {total_errors} errors")
        return 1
    else:
        print("\n✅ Validation passed")
        return 0


def cmd_pcb_export_kicad(args: argparse.Namespace) -> int:
    """Export circuit IR to KiCad format."""
    task_id = args.task
    candidate_id = args.candidate or "candidate_001"

    # Load circuit IR
    circuit_path = Path(
        f".agentic-agile-v/tasks/{task_id}/candidates/{candidate_id}/circuit_ir.json"
    )

    if not circuit_path.exists():
        print(f"❌ Circuit IR not found: {circuit_path}")
        return 1

    print(f"📋 Loading circuit IR from {circuit_path}")
    CircuitIR.load(circuit_path)

    # Export to KiCad
    # This is a placeholder - actual implementation would convert Circuit IR to KiCad format
    print("\n⚠️  KiCad export not yet implemented")
    print("   Circuit IR → KiCad conversion requires:")
    print("   - Symbol library mapping")
    print("   - Footprint assignment")
    print("   - .kicad_sch file generation")
    print("\n   For now, use KiCad manually with the circuit IR as reference")

    return 1


def cmd_pcb_run_erc(args: argparse.Namespace) -> int:
    """Run Electrical Rule Check on KiCad schematic."""
    task_id = args.task
    candidate_id = args.candidate or "candidate_001"

    # Find KiCad schematic
    kicad_dir = Path(f".agentic-agile-v/tasks/{task_id}/candidates/{candidate_id}/kicad")

    if not kicad_dir.exists():
        print(f"❌ KiCad directory not found: {kicad_dir}")
        return 1

    # Find .kicad_sch file
    schematics = list(kicad_dir.glob("*.kicad_sch"))

    if not schematics:
        print(f"❌ No KiCad schematic found in {kicad_dir}")
        return 1

    schematic_path = schematics[0]
    print(f"🔍 Running ERC on {schematic_path.name}")

    # Run ERC
    kicad = KiCadCLI()

    erc_output = kicad_dir / "validation" / "erc_report.txt"
    erc_output.parent.mkdir(parents=True, exist_ok=True)

    result = kicad.run_erc(schematic_path, erc_output)

    print(f"\n{result.output}")

    if result.success:
        print(f"\n✅ ERC passed (0 errors, {result.warnings} warnings)")
        print(f"💾 Report saved to: {erc_output}")
        return 0
    else:
        print(f"\n❌ ERC failed ({result.errors} errors, {result.warnings} warnings)")
        print(f"💾 Report saved to: {erc_output}")
        return 1


def cmd_pcb_components(args: argparse.Namespace) -> int:
    """Manage component index."""
    index_file = Path(".agentic-agile-v/pcb/component_index.json")

    index = ComponentIndex(index_file if index_file.exists() else None)

    if args.list:
        components = (
            index.find_approved() if args.approved_only else list(index.components.values())
        )

        if not components:
            print("No components in index")
            return 0

        print(f"{'Part Number':<20} {'Manufacturer':<20} {'Description':<40} {'Approved':<10}")
        print("=" * 100)

        for comp in components:
            approved = "✓" if comp.approved else ""
            print(
                f"{comp.part_number:<20} {comp.manufacturer:<20} {comp.description[:40]:<40} {approved:<10}"
            )

        print(f"\nTotal: {len(components)} components")

    return 0


def build_pcb_parser(subparsers) -> None:
    """Build PCB CLI parser."""
    pcb_parser = subparsers.add_parser("pcb", help="PCB development commands")
    pcb_subparsers = pcb_parser.add_subparsers(dest="pcb_command", required=True)

    # pcb validate
    validate_parser = pcb_subparsers.add_parser("validate", help="Validate PCB design")
    validate_parser.add_argument("--task", required=True, help="Task ID")
    validate_parser.add_argument("--candidate", help="Candidate ID (default: candidate_001)")
    validate_parser.set_defaults(func=cmd_pcb_validate)

    # pcb export
    export_parser = pcb_subparsers.add_parser("export", help="Export to KiCad")
    export_parser.add_argument("--task", required=True, help="Task ID")
    export_parser.add_argument("--candidate", help="Candidate ID")
    export_parser.set_defaults(func=cmd_pcb_export_kicad)

    # pcb erc
    erc_parser = pcb_subparsers.add_parser("erc", help="Run Electrical Rule Check")
    erc_parser.add_argument("--task", required=True, help="Task ID")
    erc_parser.add_argument("--candidate", help="Candidate ID")
    erc_parser.set_defaults(func=cmd_pcb_run_erc)

    # pcb components
    comp_parser = pcb_subparsers.add_parser("components", help="Manage component index")
    comp_parser.add_argument("--list", action="store_true", help="List components")
    comp_parser.add_argument(
        "--approved-only", action="store_true", help="Show only approved components"
    )
    comp_parser.set_defaults(func=cmd_pcb_components)
