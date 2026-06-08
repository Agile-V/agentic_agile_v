"""
CLI commands for software integration.
"""

import argparse
import sys
from pathlib import Path

from agilev.software.firmware_api import FirmwareAPIGenerator


def cmd_software_generate_api(args: argparse.Namespace) -> int:
    """Generate software API from firmware-software contract.

    Args:
        args: Command arguments

    Returns:
        Exit code
    """
    contract_path = Path(args.contract)
    output_path = Path(args.output)

    if not contract_path.exists():
        print(f"✗ Contract not found: {contract_path}", file=sys.stderr)
        return 1

    try:
        generator = FirmwareAPIGenerator(contract_path)

        print(f"Generating software API...")
        print(f"  Contract: {contract_path}")
        print(f"  Output: {output_path}")

        generator.save_api(output_path)

        print(f"✓ Generated API: {output_path}")
        print(f"\nNext steps:")
        print(f"  1. Review generated API")
        print(f"  2. Install dependencies: pip install pyserial")
        print(f"  3. Use API in your application:")
        print(f"")
        print(f"     from {output_path.stem} import *")
        print(f"     with FSC_001_API('/dev/ttyUSB0') as api:")
        print(f"         result = api.get_temperature()")
        print(f"         print(result)")

        return 0

    except Exception as e:
        print(f"✗ Error generating API: {e}", file=sys.stderr)
        import traceback

        if args.verbose:
            traceback.print_exc()
        return 1


def build_software_parser(subparsers: argparse._SubParsersAction) -> None:
    """Build software CLI parser.

    Args:
        subparsers: Parent subparsers object
    """
    software_parser = subparsers.add_parser("software", help="Software integration commands")
    software_subparsers = software_parser.add_subparsers(dest="software_command")

    # software generate-api
    gen_api_parser = software_subparsers.add_parser(
        "generate-api", help="Generate API from firmware-software contract"
    )
    gen_api_parser.add_argument(
        "--contract",
        required=True,
        help="Path to firmware-software contract",
    )
    gen_api_parser.add_argument(
        "--output",
        default="software/firmware_api.py",
        help="Output Python file path",
    )
    gen_api_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed output"
    )
    gen_api_parser.set_defaults(func=cmd_software_generate_api)
