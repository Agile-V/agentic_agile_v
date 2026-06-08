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
from agilev.firmware.hil import HILRunner
from agilev.firmware.pcb_import import generate_contract_from_pcb_export
from agilev.firmware.platformio_backend import PlatformIOBackend
from agilev.firmware.simulation import RenodeSimulator
from agilev.firmware.software_contract import FirmwareSoftwareContractGenerator


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
        print("\nNext steps:")
        print(f"  1. Review contract: {output_path}")
        print(f"  2. Validate: agilev firmware contract validate {output_path}")
        print("  3. Generate firmware: agilev firmware generate --task AAV-FW-XXX")

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
            print("✗ Cannot determine contract type. Use --type option.", file=sys.stderr)
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

                print("\nContract summary:")
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

                print("\nContract summary:")
                print(f"  Transport: {contract.transport}")
                print(f"  Protocol version: {contract.protocol_version}")
                print(f"  Commands: {len(commands)}")
                print(f"  Error codes: {len(errors)}")

                if args.verbose:
                    print("\n  Command list:")
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


def cmd_firmware_generate(args: argparse.Namespace) -> int:
    """Generate firmware project from contract.

    Args:
        args: Command arguments

    Returns:
        Exit code
    """
    contract_path = Path(args.contract)
    project_dir = Path(args.output)

    if not contract_path.exists():
        print(f"✗ Contract not found: {contract_path}", file=sys.stderr)
        return 1

    try:
        # Create backend
        backend = PlatformIOBackend(contract_path)

        print("Generating firmware project...")
        print(f"  Contract: {contract_path}")
        print(f"  Output: {project_dir}")
        print("  Backend: PlatformIO")

        # Initialize project
        backend.init_project(project_dir)
        print("✓ Initialized project structure")

        # Generate from contract
        backend.generate_from_contract(project_dir)
        print("✓ Generated firmware code from contract")

        print(f"\n✓ Firmware project created: {project_dir}")
        print("\nGenerated files:")
        print("  - platformio.ini")
        print("  - include/board_contract.h")
        print("  - src/main.cpp")
        print("  - src/diagnostics.cpp")

        print("\nNext steps:")
        print("  1. Review generated code")
        print(f"  2. Build: agilev firmware build --project {project_dir}")
        print(f"  3. Test: agilev firmware test --project {project_dir}")

        return 0

    except Exception as e:
        print(f"✗ Error generating firmware: {e}", file=sys.stderr)
        import traceback

        if args.verbose:
            traceback.print_exc()
        return 1


def cmd_firmware_build(args: argparse.Namespace) -> int:
    """Build firmware project.

    Args:
        args: Command arguments

    Returns:
        Exit code
    """
    project_dir = Path(args.project)
    contract_path = Path(args.contract) if args.contract else None

    if not project_dir.exists():
        print(f"✗ Project directory not found: {project_dir}", file=sys.stderr)
        return 1

    # Find contract if not specified
    if not contract_path:
        contract_path = project_dir.parent / "hardware_firmware_contract.yaml"
        if not contract_path.exists():
            contract_path = Path(".agentic-agile-v/contracts/hardware_firmware_contract.yaml")

    if not contract_path.exists():
        print("✗ Contract not found. Specify with --contract", file=sys.stderr)
        return 1

    try:
        backend = PlatformIOBackend(contract_path)

        print("Building firmware...")
        print(f"  Project: {project_dir}")
        print(f"  Contract: {contract_path}")

        success, output = backend.build(project_dir)

        if success:
            print("✓ Build succeeded")
            if args.verbose:
                print("\nBuild output:")
                print(output)
            return 0
        else:
            print("✗ Build failed", file=sys.stderr)
            print("\nBuild output:", file=sys.stderr)
            print(output, file=sys.stderr)
            return 1

    except Exception as e:
        print(f"✗ Error building firmware: {e}", file=sys.stderr)
        import traceback

        if args.verbose:
            traceback.print_exc()
        return 1


def cmd_firmware_test(args: argparse.Namespace) -> int:
    """Run firmware tests.

    Args:
        args: Command arguments

    Returns:
        Exit code
    """
    project_dir = Path(args.project)
    contract_path = Path(args.contract) if args.contract else None

    if not project_dir.exists():
        print(f"✗ Project directory not found: {project_dir}", file=sys.stderr)
        return 1

    # Find contract if not specified
    if not contract_path:
        contract_path = project_dir.parent / "hardware_firmware_contract.yaml"
        if not contract_path.exists():
            contract_path = Path(".agentic-agile-v/contracts/hardware_firmware_contract.yaml")

    if not contract_path.exists():
        print("✗ Contract not found. Specify with --contract", file=sys.stderr)
        return 1

    try:
        backend = PlatformIOBackend(contract_path)

        print("Running firmware tests...")
        print(f"  Project: {project_dir}")
        print(f"  Test type: {'host' if args.host else 'target'}")

        if args.host:
            success, output = backend.run_host_tests(project_dir)
        else:
            print("✗ Target tests not yet implemented", file=sys.stderr)
            return 1

        if success:
            print("✓ Tests passed")
            if args.verbose:
                print("\nTest output:")
                print(output)
            return 0
        else:
            print("✗ Tests failed", file=sys.stderr)
            print("\nTest output:", file=sys.stderr)
            print(output, file=sys.stderr)
            return 1

    except Exception as e:
        print(f"✗ Error running tests: {e}", file=sys.stderr)
        import traceback

        if args.verbose:
            traceback.print_exc()
        return 1


def cmd_firmware_software_contract_generate(args: argparse.Namespace) -> int:
    """Generate firmware-software contract from firmware project.

    Args:
        args: Command arguments

    Returns:
        Exit code
    """
    project_dir = Path(args.project)
    output_path = Path(args.output)

    if not project_dir.exists():
        print(f"✗ Project directory not found: {project_dir}", file=sys.stderr)
        return 1

    try:
        generator = FirmwareSoftwareContractGenerator(project_dir)

        print("Generating firmware-software contract...")
        print(f"  Project: {project_dir}")
        print(f"  Contract ID: {args.contract_id}")

        contract = generator.generate_contract(
            contract_id=args.contract_id,
            firmware_task_id=args.task_id,
            transport=args.transport,
        )

        generator.save_contract(contract, output_path)

        print(f"✓ Generated firmware-software contract: {output_path}")
        print("\nContract summary:")
        print(f"  Contract ID: {contract['contract_id']}")
        print(f"  Transport: {contract['transport']}")
        print(f"  Protocol version: {contract['protocol_version']}")
        print(f"  Commands: {len(contract.get('commands', []))}")
        print(f"  Error codes: {len(contract.get('error_codes', []))}")

        print("\nNext steps:")
        print(f"  1. Review contract: {output_path}")
        print(f"  2. Validate: agilev firmware contract validate {output_path}")
        print("  3. Implement software against this contract")

        return 0

    except Exception as e:
        print(f"✗ Error generating contract: {e}", file=sys.stderr)
        import traceback

        if args.verbose:
            traceback.print_exc()
        return 1


def cmd_firmware_simulate(args: argparse.Namespace) -> int:
    """Run firmware in Renode simulator.

    Args:
        args: Command arguments

    Returns:
        Exit code
    """
    project_dir = Path(args.project)

    if not project_dir.exists():
        print(f"✗ Project directory not found: {project_dir}", file=sys.stderr)
        return 1

    try:
        simulator = RenodeSimulator(project_dir)

        # Check if Renode is installed
        if not simulator.check_renode_installed():
            print("✗ Renode not installed", file=sys.stderr)
            print("\nInstall Renode:", file=sys.stderr)
            print("  macOS: brew install renode", file=sys.stderr)
            print("  Linux: https://renode.io", file=sys.stderr)
            return 1

        print("Running simulation...")
        print(f"  Project: {project_dir}")

        # Find firmware ELF
        build_dir = project_dir / ".pio" / "build"
        elf_files = list(build_dir.rglob("*.elf")) if build_dir.exists() else []

        if not elf_files:
            print("✗ No firmware ELF found. Run 'agilev firmware build' first.", file=sys.stderr)
            return 1

        firmware_elf = elf_files[0]
        print(f"  Firmware: {firmware_elf}")

        # Create simulation config
        mcu = args.mcu or "STM32F401"
        print(f"  MCU: {mcu}")

        config_files = simulator.create_simulation_config(
            mcu=mcu,
            firmware_elf=firmware_elf,
        )

        print(f"  Platform script: {config_files['platform']}")

        # Run simulation
        success, output = simulator.run_simulation(
            script_path=config_files['platform'],
            timeout=args.timeout,
        )

        if success or args.verbose:
            print("\nSimulation output:")
            print(output)

        # Extract and save results
        results = simulator.extract_test_results(output)

        results_path = project_dir / "renode" / "results.json"
        simulator.save_results(results, results_path)

        if results["passed"]:
            print("\n✓ Simulation passed")
            print(f"  Tests run: {results['tests_run']}")
            print(f"  Tests passed: {results['tests_passed']}")
            print(f"  Results: {results_path}")
            return 0
        else:
            print("\n✗ Simulation failed", file=sys.stderr)
            print(f"  Tests run: {results['tests_run']}", file=sys.stderr)
            print(f"  Tests passed: {results['tests_passed']}", file=sys.stderr)
            print(f"  Tests failed: {results['tests_failed']}", file=sys.stderr)
            print(f"  Results: {results_path}", file=sys.stderr)
            return 1

    except Exception as e:
        print(f"✗ Error running simulation: {e}", file=sys.stderr)
        import traceback

        if args.verbose:
            traceback.print_exc()
        return 1


def cmd_firmware_hil_test(args: argparse.Namespace) -> int:
    """Run Hardware-in-the-Loop tests.

    Args:
        args: Command arguments

    Returns:
        Exit code
    """
    project_dir = Path(args.project)

    if not project_dir.exists():
        print(f"✗ Project directory not found: {project_dir}", file=sys.stderr)
        return 1

    try:
        runner = HILRunner(project_dir)

        print("Running HIL tests...")
        print(f"  Project: {project_dir}")
        print(f"  Port: {args.port}")

        if args.flash:
            print("  Flashing firmware first...")

        # Run HIL test
        success, results = runner.run_hil_test(
            port=args.port,
            config_path=Path(args.config) if args.config else None,
            flash_first=args.flash,
        )

        # Save results
        results_path = project_dir / "hil" / "results.json"
        if "results" in results:
            runner.save_results(results["results"], results_path)

        if success:
            print("\n✓ HIL tests passed")
            print(f"  Total: {results.get('total', 0)}")
            print(f"  Results: {results_path}")

            if args.verbose and "results" in results:
                print("\nTest details:")
                for result in results["results"]:
                    status = "✓" if result["passed"] else "✗"
                    print(f"  {status} {result['name']}: {result['response']}")

            return 0
        else:
            print("\n✗ HIL tests failed", file=sys.stderr)

            if "error" in results:
                print(f"  Error: {results['error']}", file=sys.stderr)
            else:
                passed = sum(1 for r in results.get("results", []) if r["passed"])
                total = results.get("total", 0)
                print(f"  Passed: {passed}/{total}", file=sys.stderr)
                print(f"  Results: {results_path}", file=sys.stderr)

                if args.verbose and "results" in results:
                    print("\nTest details:", file=sys.stderr)
                    for result in results["results"]:
                        status = "✓" if result["passed"] else "✗"
                        print(f"  {status} {result['name']}: {result['response']}", file=sys.stderr)

            return 1

    except Exception as e:
        print(f"✗ Error running HIL tests: {e}", file=sys.stderr)
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

    # firmware software-contract generate
    sw_contract_parser = contract_subparsers.add_parser(
        "generate-software", help="Generate firmware-software contract from firmware"
    )
    sw_contract_parser.add_argument("--project", required=True, help="Firmware project directory")
    sw_contract_parser.add_argument(
        "--contract-id", required=True, help="Contract ID (e.g., FSC-001)"
    )
    sw_contract_parser.add_argument("--task-id", required=True, help="Firmware task ID")
    sw_contract_parser.add_argument(
        "--transport", default="usb_cdc_serial", help="Communication transport"
    )
    sw_contract_parser.add_argument(
        "--output",
        default=".agentic-agile-v/contracts/firmware_software_contract.yaml",
        help="Output contract path",
    )
    sw_contract_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed output"
    )
    sw_contract_parser.set_defaults(func=cmd_firmware_software_contract_generate)

    # firmware generate
    gen_firmware_parser = firmware_subparsers.add_parser(
        "generate", help="Generate firmware project from contract"
    )
    gen_firmware_parser.add_argument(
        "--contract",
        default=".agentic-agile-v/contracts/hardware_firmware_contract.yaml",
        help="Path to hardware-firmware contract",
    )
    gen_firmware_parser.add_argument(
        "--output", default="firmware/platformio", help="Output project directory"
    )
    gen_firmware_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed output"
    )
    gen_firmware_parser.set_defaults(func=cmd_firmware_generate)

    # firmware build
    build_parser = firmware_subparsers.add_parser("build", help="Build firmware project")
    build_parser.add_argument("--project", required=True, help="Firmware project directory")
    build_parser.add_argument("--contract", help="Path to hardware-firmware contract")
    build_parser.add_argument("--verbose", "-v", action="store_true", help="Show build output")
    build_parser.set_defaults(func=cmd_firmware_build)

    # firmware test
    test_parser = firmware_subparsers.add_parser("test", help="Run firmware tests")
    test_parser.add_argument("--project", required=True, help="Firmware project directory")
    test_parser.add_argument("--contract", help="Path to hardware-firmware contract")
    test_parser.add_argument(
        "--host", action="store_true", help="Run host tests (default: target tests)"
    )
    test_parser.add_argument("--verbose", "-v", action="store_true", help="Show test output")
    test_parser.set_defaults(func=cmd_firmware_test)

    # firmware simulate
    simulate_parser = firmware_subparsers.add_parser(
        "simulate", help="Run firmware in Renode simulator"
    )
    simulate_parser.add_argument("--project", required=True, help="Firmware project directory")
    simulate_parser.add_argument("--mcu", help="MCU model (e.g., STM32F401, STM32F103)")
    simulate_parser.add_argument(
        "--timeout", type=int, default=30, help="Simulation timeout in seconds"
    )
    simulate_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed output"
    )
    simulate_parser.set_defaults(func=cmd_firmware_simulate)

    # firmware hil-test
    hil_parser = firmware_subparsers.add_parser("hil-test", help="Run Hardware-in-the-Loop tests")
    hil_parser.add_argument("--project", required=True, help="Firmware project directory")
    hil_parser.add_argument("--port", required=True, help="Serial port (e.g., /dev/ttyUSB0, COM3)")
    hil_parser.add_argument("--config", help="HIL test config path")
    hil_parser.add_argument("--flash", action="store_true", help="Flash firmware before testing")
    hil_parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    hil_parser.set_defaults(func=cmd_firmware_hil_test)
