#!/usr/bin/env python3
"""Agentic Agile-V CLI - Command-line interface for evidence gates and validation."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def cmd_doctor(args: argparse.Namespace) -> int:
    """Check repository health and required files."""
    repo = Path.cwd()
    required = [
        Path("schemas/evidence_bundle.schema.json"),
        Path("templates/evidence_bundle.json"),
        Path("scripts/validate_evidence.py"),
        Path("scripts/new_task.py"),
        Path("scripts/risk_assessment.py"),
    ]
    
    missing = [str(p) for p in required if not (repo / p).exists()]
    
    if missing:
        print("❌ Agentic Agile-V repository health check FAILED\n")
        print("Missing required files:")
        for path in missing:
            print(f"  - {path}")
        return 1
    
    print("✅ Agentic Agile-V repository health: OK")
    print(f"\nRepository root: {repo}")
    print(f"Required files: {len(required)} / {len(required)} present")
    return 0


def cmd_evidence_validate(args: argparse.Namespace) -> int:
    """Validate evidence bundles."""
    # Import the existing validation script
    scripts_dir = Path(__file__).parent.parent.parent / "scripts"
    sys.path.insert(0, str(scripts_dir))
    
    try:
        from validate_evidence import validate_bundle  # type: ignore
        
        repo = Path.cwd()
        
        if args.bundle:
            bundle_path = Path(args.bundle)
            if not bundle_path.exists():
                print(f"❌ Bundle not found: {bundle_path}")
                return 1
            
            errors, warnings = validate_bundle(bundle_path, repo)
            
            if errors:
                print(f"❌ {bundle_path}:")
                for err in errors:
                    print(f"  ERROR: {err}")
            if warnings:
                for warn in warnings:
                    print(f"  WARNING: {warn}")
            
            return 1 if errors else 0
        
        elif args.root:
            root_path = Path(args.root)
            if not root_path.exists():
                print(f"❌ Evidence root not found: {root_path}")
                return 1
            
            bundles = list(root_path.rglob("*evidence_bundle.json"))
            if not bundles:
                print(f"⚠️  No evidence bundles found in {root_path}")
                return 0
            
            total_errors = 0
            total_warnings = 0
            
            for bundle_path in bundles:
                errors, warnings = validate_bundle(bundle_path, repo)
                if errors or warnings:
                    print(f"\n{bundle_path}:")
                    for err in errors:
                        print(f"  ERROR: {err}")
                    for warn in warnings:
                        print(f"  WARNING: {warn}")
                total_errors += len(errors)
                total_warnings += len(warnings)
            
            print(f"\n{'='*60}")
            print(f"Validated {len(bundles)} evidence bundles")
            print(f"Errors: {total_errors}, Warnings: {total_warnings}")
            
            return 1 if total_errors > 0 else 0
        
        else:
            print("❌ Either --bundle or --root must be specified")
            return 1
            
    except ImportError as e:
        print(f"❌ Cannot import validation module: {e}")
        return 1


def cmd_init(args: argparse.Namespace) -> int:
    """Initialize Agentic Agile-V structure in current repository."""
    repo = Path.cwd()
    
    # Create directory structure
    dirs = [
        ".agile-v",
        "tasks",
        "evidence",
        "config",
    ]
    
    for d in dirs:
        (repo / d).mkdir(exist_ok=True)
    
    # Create basic .gitignore for .agile-v if it doesn't exist
    gitignore_path = repo / ".agile-v" / ".gitignore"
    if not gitignore_path.exists():
        gitignore_path.write_text("*.log\n*.tmp\n")
    
    print("✅ Agentic Agile-V structure initialized")
    print(f"\nCreated directories:")
    for d in dirs:
        print(f"  - {d}/")
    
    return 0


def cmd_task_new(args: argparse.Namespace) -> int:
    """Create a new task package."""
    # Call the existing new_task.py script
    scripts_dir = Path(__file__).parent.parent.parent / "scripts"
    sys.path.insert(0, str(scripts_dir))
    
    try:
        from new_task import main as new_task_main  # type: ignore
        
        # Build argv for the old script
        argv = [
            "--type", args.type,
            "--id", args.id,
            "--title", args.title,
        ]
        
        return new_task_main(argv)
    except ImportError as e:
        print(f"❌ Cannot import new_task module: {e}")
        return 1


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="agilev",
        description="Agentic Agile-V - Evidence-controlled acceptance gates",
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # doctor command
    doctor = subparsers.add_parser(
        "doctor",
        help="Check repository health and required files",
    )
    doctor.set_defaults(func=cmd_doctor)
    
    # init command
    init = subparsers.add_parser(
        "init",
        help="Initialize Agentic Agile-V structure in current repository",
    )
    init.set_defaults(func=cmd_init)
    
    # task new command
    task = subparsers.add_parser(
        "task",
        help="Task management commands",
    )
    task_sub = task.add_subparsers(dest="task_command", required=True)
    
    task_new = task_sub.add_parser("new", help="Create a new task package")
    task_new.add_argument("--type", required=True, choices=["feature", "bug", "hardware"],
                          help="Task type")
    task_new.add_argument("--id", required=True, help="Task ID (e.g., AAV-001)")
    task_new.add_argument("--title", required=True, help="Task title")
    task_new.set_defaults(func=cmd_task_new)
    
    # evidence validate command
    evidence = subparsers.add_parser(
        "evidence",
        help="Evidence bundle commands",
    )
    evidence_sub = evidence.add_subparsers(dest="evidence_command", required=True)
    
    evidence_validate = evidence_sub.add_parser("validate", help="Validate evidence bundles")
    evidence_validate.add_argument("--bundle", help="Path to single evidence bundle JSON file")
    evidence_validate.add_argument("--root", help="Path to evidence root directory")
    evidence_validate.set_defaults(func=cmd_evidence_validate)
    
    return parser


def main(argv: list[str] | None = None) -> int:
    """Main CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
