#!/usr/bin/env python3
"""Agentic Agile-V CLI - Unified command-line interface for evidence gates and validation."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import yaml

from agilev.openhands.event_ledger import EventLedger, EventType
from agilev.openhands.evidence_adapter import EvidenceAdapter
from agilev.openhands.github_actions import generate_github_actions
from agilev.openhands.reports import generate_handoff_report
from agilev.openhands.scaffold import OpenHandsScaffold
from agilev.openhands.session_manager import (
    AgentRole,
    BuilderVerifierWorkflow,
    OpenHandsSessionManager,
    SessionConfig,
)
from agilev.embedded.cli import build_embedded_parser
from agilev.firmware.cli import build_firmware_parser
from agilev.pcb.cli import build_pcb_parser
from agilev.software.cli import build_software_parser
from agilev.state import EventLogger, LockManager, TaskState
from agilev.task_context import TaskContextResolver


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return f"sha256:{sha256_hash.hexdigest()}"


def cmd_init(args: argparse.Namespace) -> int:
    """Initialize the repository with Agentic Agile-V structure."""
    repo = Path.cwd()

    # Create directory structure
    dirs = [
        ".agentic-agile-v",
        ".agentic-agile-v/state",
        ".agentic-agile-v/tasks",
        ".agentic-agile-v/policies",
        ".agentic-agile-v/schemas",
        ".agentic-agile-v/reports",
        ".agentic-agile-v/logs",
    ]

    for d in dirs:
        (repo / d).mkdir(parents=True, exist_ok=True)

    # Initialize state files
    state_dir = repo / ".agentic-agile-v" / "state"
    (state_dir / "events.jsonl").touch()

    # Initialize tasks.json
    tasks_file = state_dir / "tasks.json"
    if not tasks_file.exists():
        tasks_file.write_text(json.dumps({"tasks": {}}, indent=2))

    # Initialize locks.json
    locks_file = state_dir / "locks.json"
    if not locks_file.exists():
        locks_file.write_text(json.dumps({"locks": []}, indent=2))

    # Log initialization event
    event_logger = EventLogger()
    event_logger.log_event(
        event_type="IntentDeclared",
        actor="agilev-cli",
        summary="Initialized Agentic Agile-V repository structure",
        artifacts=[str(d) for d in dirs],
    )

    print("✅ Agentic Agile-V structure initialized")
    print("\nCreated directories:")
    for d in dirs:
        print(f"  - {d}/")
    print("\nInitialized state files:")
    print("  - .agentic-agile-v/state/events.jsonl")
    print("  - .agentic-agile-v/state/tasks.json")
    print("  - .agentic-agile-v/state/locks.json")

    print("\n📝 Next steps:")
    print("  1. Run: agilev new --title 'Your task name' --risk L1")
    print("  2. Create your task brief in the generated directory")
    print("  3. Run: agilev validate to check your work")

    return 0


def cmd_new(args: argparse.Namespace) -> int:
    """Create a new task."""
    repo = Path.cwd()
    task_state = TaskState()
    event_logger = EventLogger()

    # Generate task ID
    tasks = task_state.list_tasks()
    task_number = len(tasks) + 1
    task_id = f"AAV-{task_number:04d}"

    # Create task directory
    task_dir = repo / ".agentic-agile-v" / "tasks" / task_id
    task_dir.mkdir(parents=True, exist_ok=True)

    # Create task brief template
    brief = {
        "task_id": task_id,
        "title": args.title,
        "problem_statement": "TODO: Describe the problem to solve",
        "intended_outcome": "TODO: Describe the expected outcome",
        "scope": ["TODO: What is included in this task"],
        "non_goals": ["TODO: What is explicitly out of scope"],
        "requirements": [
            {"id": "REQ-0001", "description": "TODO: First requirement", "priority": "must"}
        ],
        "constraints": ["TODO: Technical or business constraints"],
        "acceptance_criteria": ["TODO: Criteria for acceptance"],
        "risk_level": args.risk,
        "affected_components": ["TODO: Components that will be changed"],
        "required_evidence": [],
        "human_approval_required": args.risk in ["L3", "L4"],
        "created_at": datetime.now(UTC).isoformat(),
        "created_by": "agilev-cli",
    }

    brief_path = task_dir / "brief.yaml"
    with open(brief_path, "w") as f:
        yaml.dump(brief, f, default_flow_style=False, sort_keys=False)

    # Create empty plan and evidence files
    (task_dir / "plan.md").write_text(
        f"# Implementation Plan: {task_id}\n\nTODO: Create implementation plan\n"
    )
    (task_dir / "impact.md").write_text(f"# Impact Analysis: {task_id}\n\nTODO: Analyze impact\n")
    (task_dir / "evidence.json").write_text(
        json.dumps(
            {
                "schema_version": "2.0.0",
                "task_id": task_id,
                "risk_level": args.risk,
                "requirements": [],
                "changed_files": [],
                "test_runs": [],
                "gate_results": [],
            },
            indent=2,
        )
    )

    # Update task state
    task_state.create_task(task_id, args.title, args.risk)

    # Log event
    event_logger.log_event(
        event_type="BriefCreated",
        actor="agilev-cli",
        task_id=task_id,
        summary=f"Created task brief for '{args.title}'",
        artifacts=[str(brief_path)],
        metadata={"risk_level": args.risk},
    )

    print(f"✅ Created task {task_id}: {args.title}")
    print(f"\nTask directory: .agentic-agile-v/tasks/{task_id}/")
    print(f"Risk level: {args.risk}")
    print("\nNext steps:")
    print(f"  1. Edit {brief_path} to complete the task brief")
    print(f"  2. Run: agilev brief {task_id} to validate the brief")
    print(f"  3. Run: agilev classify {task_id} to verify risk level")

    return 0


def cmd_brief(args: argparse.Namespace) -> int:
    """Validate or create a task brief."""
    task_dir = Path.cwd() / ".agentic-agile-v" / "tasks" / args.task_id
    brief_path = task_dir / "brief.yaml"

    if not brief_path.exists():
        print(f"❌ Task brief not found: {brief_path}")
        return 1

    # Load and validate brief
    with open(brief_path) as f:
        brief = yaml.safe_load(f)

    # Check required fields
    required_fields = [
        "task_id",
        "title",
        "problem_statement",
        "intended_outcome",
        "scope",
        "non_goals",
        "requirements",
        "constraints",
        "acceptance_criteria",
        "risk_level",
        "affected_components",
        "required_evidence",
        "human_approval_required",
    ]

    missing_fields = [field for field in required_fields if field not in brief or not brief[field]]

    if missing_fields:
        print("❌ Task brief validation FAILED")
        print("\nMissing or empty required fields:")
        for field in missing_fields:
            print(f"  - {field}")
        return 1

    # Log validation event
    event_logger = EventLogger()
    event_logger.log_event(
        event_type="BriefValidated",
        actor="agilev-cli",
        task_id=args.task_id,
        summary=f"Validated task brief for {args.task_id}",
    )

    print(f"✅ Task brief validated: {args.task_id}")
    print(f"\nRisk level: {brief['risk_level']}")
    print(f"Requirements: {len(brief['requirements'])}")
    print(f"Human approval required: {brief['human_approval_required']}")

    return 0


def cmd_classify(args: argparse.Namespace) -> int:
    """Assign or validate risk level for a task."""
    task_dir = Path.cwd() / ".agentic-agile-v" / "tasks" / args.task_id
    brief_path = task_dir / "brief.yaml"

    if not brief_path.exists():
        print(f"❌ Task brief not found: {brief_path}")
        return 1

    # Load brief
    with open(brief_path) as f:
        brief = yaml.safe_load(f)

    risk_level = brief.get("risk_level", "L1")

    # Load risk policy
    policy_path = Path.cwd() / ".agentic-agile-v" / "policies" / "rules.yaml"
    if policy_path.exists():
        with open(policy_path) as f:
            policy = yaml.safe_load(f)

        # Get evidence requirements for this risk level
        evidence_reqs = policy.get("evidence_by_level", {}).get(risk_level, {})

        print(f"📊 Risk Classification: {risk_level}")
        print("\nRequired evidence:")
        for req in evidence_reqs.get("required", []):
            print(f"  ✓ {req}")

        print("\nRequired gates:")
        for gate in evidence_reqs.get("gates", []):
            print(f"  ✓ {gate}")

        print(f"\nApproval required: {evidence_reqs.get('approval', False)}")
        print(f"Verification mode: {evidence_reqs.get('verification_mode', 'none')}")
    else:
        print("⚠️  Risk policy not found, using defaults")
        print(f"Risk level: {risk_level}")

    # Log event
    event_logger = EventLogger()
    event_logger.log_event(
        event_type="RiskClassAssigned",
        actor="agilev-cli",
        task_id=args.task_id,
        summary=f"Classified {args.task_id} as {risk_level}",
        metadata={"risk_level": risk_level},
    )

    return 0


def cmd_impact(args: argparse.Namespace) -> int:
    """Produce change-impact analysis."""
    task_dir = Path.cwd() / ".agentic-agile-v" / "tasks" / args.task_id
    impact_path = task_dir / "impact.md"

    print(f"📊 Creating impact analysis for {args.task_id}...")

    # Create impact analysis template
    impact_content = f"""# Impact Analysis: {args.task_id}

## Summary

TODO: Provide a high-level summary of the impact

## Affected Requirements

TODO: List requirements addressed

## Affected Components

TODO: List system components that will change

## Affected Files

TODO: List files that will be modified

## Affected Interfaces

TODO: List public interfaces affected

## Affected Tests

TODO: List tests that need to be updated or created

## Required Regression Tests

TODO: List regression tests needed

## Risk Implications

TODO: Describe risks introduced or mitigated

## Required Evidence

TODO: List evidence that must be collected

## Open Questions

TODO: List unresolved questions
"""

    impact_path.write_text(impact_content)

    # Log event
    event_logger = EventLogger()
    event_logger.log_event(
        event_type="ImpactAnalyzed",
        actor="agilev-cli",
        task_id=args.task_id,
        summary=f"Created impact analysis for {args.task_id}",
        artifacts=[str(impact_path)],
    )

    print(f"✅ Impact analysis created: {impact_path}")
    print("\nPlease complete the impact analysis before proceeding to implementation.")

    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Run schema and policy checks."""
    print("🔍 Running validation checks...")

    failures = []
    warnings = []

    # Check if initialized
    if not (Path.cwd() / ".agentic-agile-v").exists():
        failures.append("Repository not initialized. Run 'agilev init' first.")
        print("❌ Validation FAILED")
        for failure in failures:
            print(f"  ERROR: {failure}")
        return 1

    # Validate event chain
    event_logger = EventLogger()
    chain_valid, chain_errors = event_logger.verify_chain()
    if not chain_valid:
        failures.extend([f"Event chain: {err}" for err in chain_errors])

    # Clean expired locks
    lock_manager = LockManager()
    cleaned = lock_manager.clean_expired_locks()
    if cleaned > 0:
        warnings.append(f"Cleaned {cleaned} expired locks")

    # Report results
    if failures:
        print("❌ Validation FAILED")
        for failure in failures:
            print(f"  ERROR: {failure}")
        return 1

    if warnings:
        print("⚠️  Validation passed with warnings")
        for warning in warnings:
            print(f"  WARNING: {warning}")
    else:
        print("✅ All validation checks passed")

    return 0


def cmd_evidence(args: argparse.Namespace) -> int:
    """Manage evidence bundles."""
    task_dir = Path.cwd() / ".agentic-agile-v" / "tasks" / args.task_id
    evidence_path = task_dir / "evidence.json"

    if not evidence_path.exists():
        print(f"❌ Evidence bundle not found: {evidence_path}")
        return 1

    # Load evidence bundle
    with open(evidence_path) as f:
        evidence = json.load(f)

    if args.add_file:
        # Add a changed file with hash
        file_path = Path(args.add_file)
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            return 1

        file_hash = compute_file_hash(file_path)

        changed_file = {
            "path": str(file_path),
            "sha256": file_hash,
            "change_type": "modify",
            "requirement_ids": [],
        }

        evidence["changed_files"].append(changed_file)

        # Save updated evidence
        with open(evidence_path, "w") as f:
            json.dump(evidence, f, indent=2)

        print(f"✅ Added file to evidence: {file_path}")
        print(f"   Hash: {file_hash}")

    # Log event
    event_logger = EventLogger()
    event_logger.log_event(
        event_type="EvidenceAdded",
        actor="agilev-cli",
        task_id=args.task_id,
        summary=f"Updated evidence bundle for {args.task_id}",
    )

    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Show current process status."""
    print("📊 Agentic Agile-V Status\n")

    # Task status
    task_state = TaskState()
    all_tasks = task_state.list_tasks()

    print("Tasks:")
    print(f"  Total: {len(all_tasks)}")

    by_status: dict[str, int] = {}
    by_risk: dict[str, int] = {}
    for task in all_tasks:
        status = task.get("status", "unknown")
        risk = task.get("risk_level", "unknown")
        by_status[status] = by_status.get(status, 0) + 1
        by_risk[risk] = by_risk.get(risk, 0) + 1

    print("\n  By status:")
    for status, count in sorted(by_status.items()):
        print(f"    {status}: {count}")

    print("\n  By risk level:")
    for risk, count in sorted(by_risk.items()):
        print(f"    {risk}: {count}")

    # Active locks
    lock_manager = LockManager()
    active_locks = lock_manager.get_active_locks()

    print(f"\nActive Locks: {len(active_locks)}")
    for lock in active_locks:
        print(f"  - Task {lock['task_id']} by {lock['actor']}")
        print(f"    Files: {', '.join(lock['files'][:3])}{'...' if len(lock['files']) > 3 else ''}")

    # Event log status
    event_logger = EventLogger()
    if event_logger.log_path.exists():
        with open(event_logger.log_path) as f:
            event_count = sum(1 for _ in f)
        print(f"\nEvent Log: {event_count} events recorded")

    return 0


def cmd_handoff(args: argparse.Namespace) -> int:
    """Create a rehydration document for the next agent or human."""
    task_dir = Path.cwd() / ".agentic-agile-v" / "tasks" / args.task_id
    handoff_path = task_dir / "handoff.md"

    # Load task brief
    brief_path = task_dir / "brief.yaml"
    if not brief_path.exists():
        print(f"❌ Task brief not found: {brief_path}")
        return 1

    with open(brief_path) as f:
        brief = yaml.safe_load(f)

    # Create handoff document
    handoff_content = f"""# Handoff: {args.task_id}

## Current Objective

{brief.get("title", "No title")}

## Current Status

TODO: Update with current status

## Risk Level

{brief.get("risk_level", "Unknown")}

## Key Requirements

"""

    for req in brief.get("requirements", []):
        handoff_content += f"- {req.get('id')}: {req.get('description')}\n"

    handoff_content += """
## Constraints

"""
    for constraint in brief.get("constraints", []):
        handoff_content += f"- {constraint}\n"

    handoff_content += """
## Decisions Made

TODO: Document key decisions

## Files Changed

TODO: List changed files

## Tests Added or Changed

TODO: List test changes

## Evidence Collected

TODO: List evidence artifacts

## Failed Checks or Unresolved Issues

TODO: List any failures or blockers

## Open Questions

TODO: List open questions

## Recommended Next Action

TODO: Specify next recommended action
"""

    handoff_path.write_text(handoff_content)

    # Log event
    event_logger = EventLogger()
    event_logger.log_event(
        event_type="HandoffCreated",
        actor="agilev-cli",
        task_id=args.task_id,
        summary=f"Created handoff document for {args.task_id}",
        artifacts=[str(handoff_path)],
    )

    print(f"✅ Handoff document created: {handoff_path}")
    print("\nPlease complete the handoff document with current context.")

    return 0


def cmd_lock(args: argparse.Namespace) -> int:
    """Acquire a lock on files for a task."""
    lock_manager = LockManager()

    files = args.files.split(",")

    success = lock_manager.acquire_lock(
        task_id=args.task_id, actor=args.actor, files=files, intent=args.intent, ttl_hours=args.ttl
    )

    if success:
        print(f"✅ Lock acquired for task {args.task_id}")
        print(f"   Actor: {args.actor}")
        print(f"   Files: {', '.join(files)}")
        print(f"   TTL: {args.ttl} hours")
    else:
        print("❌ Lock conflict: One or more files are already locked")
        print("\nCheck active locks with: agilev status")
        return 1

    return 0


def cmd_unlock(args: argparse.Namespace) -> int:
    """Release locks for a task."""
    lock_manager = LockManager()

    lock_manager.release_lock(args.task_id, args.actor)

    print(f"✅ Locks released for task {args.task_id} by {args.actor}")

    return 0


# OpenHands commands


def cmd_openhands_init(args: argparse.Namespace) -> int:
    """Initialize OpenHands integration."""
    scaffold = OpenHandsScaffold()

    print("🔧 Initializing OpenHands integration...")

    try:
        created_files = scaffold.init(force=args.force)

        print("\n✅ OpenHands integration initialized")
        print(f"\nCreated {len(created_files)} files:")

        # Group by category
        skills = {k: v for k, v in created_files.items() if k.startswith("skill_")}
        hooks = {k: v for k, v in created_files.items() if k.startswith("hook_")}
        policies = {k: v for k, v in created_files.items() if k.startswith("policy_")}
        other = {
            k: v
            for k, v in created_files.items()
            if not (k.startswith("skill_") or k.startswith("hook_") or k.startswith("policy_"))
        }

        if skills:
            print("\n📚 Skills:")
            for name, path in skills.items():
                print(f"  ✓ {path.relative_to(Path.cwd())}")

        if hooks:
            print("\n🪝 Hooks:")
            for name, path in hooks.items():
                print(f"  ✓ {path.relative_to(Path.cwd())}")

        if policies:
            print("\n📋 Policies:")
            for name, path in policies.items():
                print(f"  ✓ {path.relative_to(Path.cwd())}")

        if other:
            print("\n⚙️  Other:")
            for name, path in other.items():
                print(f"  ✓ {path.relative_to(Path.cwd())}")

        print("\n📝 Next steps:")
        print("  1. Run: agilev openhands doctor")
        print("  2. Create a task: agilev new --title 'Task name' --risk L1")
        print("  3. Run OpenHands with Agile-V skills and hooks active")

        return 0
    except Exception as e:
        print(f"❌ Error initializing OpenHands integration: {e}")
        return 1


def cmd_openhands_doctor(args: argparse.Namespace) -> int:
    """Validate OpenHands integration setup."""
    scaffold = OpenHandsScaffold()

    print("🔍 Checking OpenHands integration setup...\n")

    checks = scaffold.doctor()

    passed = 0
    failed = 0

    # Group checks
    core_checks = ["agents_md", "setup_script", "hooks_config", "openhands_config"]
    skill_checks = [k for k in checks if k.startswith("skill_")]
    hook_checks = [k for k in checks if k.startswith("hook_")]
    policy_checks = [k for k in checks if k.startswith("policy_")]

    def print_checks(title: str, check_keys: list[str]) -> None:
        nonlocal passed, failed
        if not check_keys:
            return
        print(f"{title}:")
        for key in check_keys:
            status = checks.get(key, False)
            if status:
                print(f"  ✅ {key}")
                passed += 1
            else:
                print(f"  ❌ {key}")
                failed += 1
        print()

    print_checks("Core Files", core_checks)
    print_checks("Skills", skill_checks)
    print_checks("Hooks", hook_checks)
    print_checks("Policies", policy_checks)

    print(f"Results: {passed} passed, {failed} failed")

    if failed > 0:
        print("\n💡 Fix missing files with: agilev openhands init --force")
        return 1
    else:
        print("\n✅ OpenHands integration ready")
        return 0


def cmd_openhands_scaffold(args: argparse.Namespace) -> int:
    """Regenerate OpenHands integration files."""
    return cmd_openhands_init(args)


def cmd_openhands_validate(args: argparse.Namespace) -> int:
    """Validate OpenHands session for a task."""
    resolver = TaskContextResolver()

    try:
        task_id = resolver.resolve(explicit_task_id=args.task, fail_on_ambiguous=True)

        if not task_id:
            print("❌ No task ID found. Specify with --task AAV-XXXX or set AGILEV_TASK_ID")
            return 1

        if not resolver.validate_task_exists(task_id):
            print(f"❌ Task {task_id} not found")
            return 1

        print(f"🔍 Validating OpenHands session for task {task_id}...")

        task_dir = resolver.get_task_dir(task_id)

        # Check evidence bundle exists
        evidence_bundle = task_dir / "evidence_bundle.json"
        if not evidence_bundle.exists():
            print(f"❌ Evidence bundle not found at {evidence_bundle.relative_to(Path.cwd())}")
            return 1

        # Check for OpenHands session data
        session_file = task_dir / "logs/openhands_session.json"
        tool_log = task_dir / "logs/openhands_tool_log.jsonl"

        if session_file.exists():
            print("  ✅ OpenHands session metadata found")
        else:
            print("  ⚠️  OpenHands session metadata not found")

        if tool_log.exists():
            # Count tool events
            with open(tool_log) as f:
                event_count = sum(1 for _ in f)
            print(f"  ✅ OpenHands tool log found ({event_count} events)")
        else:
            print("  ⚠️  OpenHands tool log not found")

        # Scope validation if requested
        if args.scope:
            print("\n🎯 Validating scope...")
            # TODO: Implement scope validation
            print("  ⚠️  Scope validation not yet implemented (MVP)")

        print(f"\n✅ Validation complete for task {task_id}")
        return 0

    except ValueError as e:
        print(f"❌ {e}")
        return 1
    except Exception as e:
        print(f"❌ Error validating OpenHands session: {e}")
        return 1


def cmd_openhands_handoff(args: argparse.Namespace) -> int:
    """Generate handoff report for a task."""
    resolver = TaskContextResolver()

    try:
        task_id = resolver.resolve(explicit_task_id=args.task, fail_on_ambiguous=True)

        if not task_id:
            print("❌ No task ID found. Specify with --task AAV-XXXX or set AGILEV_TASK_ID")
            return 1

        repo = Path.cwd()
        agilev_dir = repo / ".agentic-agile-v"

        # Generate enhanced handoff report
        print(f"📋 Generating handoff report for task {task_id}...")

        report_md = generate_handoff_report(task_id, repo, agilev_dir)

        # Save to file
        task_dir = resolver.get_task_dir(task_id)
        handoff_file = task_dir / "handoff_report.md"
        handoff_file.write_text(report_md)

        # Display report
        print(report_md)

        print(f"\n💾 Handoff report saved to: {handoff_file.relative_to(repo)}")

        return 0

    except ValueError as e:
        print(f"❌ {e}")
        return 1
    except Exception as e:
        print(f"❌ Error generating handoff: {e}")
        import traceback

        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"❌ Error reading handoff report: {e}")
        return 1


def cmd_openhands_run(args: argparse.Namespace) -> int:
    """Run OpenHands session for a task."""
    resolver = TaskContextResolver()

    try:
        task_id = resolver.resolve(explicit_task_id=args.task, fail_on_ambiguous=True)

        if not task_id:
            print("❌ No task ID found. Specify with --task AAV-XXXX or set AGILEV_TASK_ID")
            return 1

        if not resolver.validate_task_exists(task_id):
            print(f"❌ Task {task_id} not found")
            return 1

        repo = Path.cwd()
        agilev_dir = repo / ".agentic-agile-v"

        # Initialize session manager
        session_manager = OpenHandsSessionManager(repo, agilev_dir)

        # Determine mode
        if args.builder_verifier:
            print(f"🚀 Starting builder/verifier workflow for task {task_id}...")
            workflow = BuilderVerifierWorkflow(session_manager)

            # Get prompt from args or task brief
            if args.prompt:
                prompt = args.prompt
            else:
                # Read from task brief
                task_brief = agilev_dir / "tasks" / task_id / "task_brief.md"
                if not task_brief.exists():
                    print(f"❌ Task brief not found at {task_brief}")
                    print("   Specify prompt with --prompt or create task brief")
                    return 1

                # Extract title from task brief
                content = task_brief.read_text()
                lines = content.split("\n")
                for line in lines:
                    if line.startswith("# "):
                        prompt = line[2:].strip()
                        break
                else:
                    prompt = f"Implement task {task_id}"

            results = workflow.run(task_id, prompt)

            # Display results
            print(f"\n{'=' * 60}")
            print("Builder/Verifier Workflow Complete")
            print(f"{'=' * 60}")
            print(f"Task: {task_id}")
            print(f"Cycles: {len(results['cycles'])}")
            print(f"Final state: {results['final_state']}")
            print(f"Approved: {'✅ Yes' if results['approved'] else '❌ No'}")

            for i, cycle in enumerate(results["cycles"], 1):
                print(f"\nCycle {i}:")
                print(f"  Builder: {cycle['builder']}")
                print(f"  Verifier: {cycle['verifier']}")
                if "approved" in cycle:
                    print(f"  Approved: {'✅' if cycle['approved'] else '❌'}")

            if results["approved"]:
                print("\n✅ Implementation approved! Ready for review.")
                return 0
            else:
                print("\n⚠️  Implementation not approved. See session logs for details.")
                return 1

        else:
            print(f"🚀 Starting OpenHands session for task {task_id}...")

            # Create session config
            config = SessionConfig(
                task_id=task_id,
                role=AgentRole.STANDALONE,
                workspace_dir=repo,
                max_iterations=args.max_iterations,
                timeout_seconds=args.timeout,
                model=args.model,
            )

            # Get prompt
            if not args.prompt:
                print("❌ --prompt required in standalone mode")
                return 1

            session_id = session_manager.create_session(config)
            print(f"Created session: {session_id}")

            session_manager.start_session(session_id, args.prompt)

            metadata = session_manager.get_session(session_id)

            print("\nSession completed:")
            print(f"  State: {metadata.state.value}")
            print(f"  Iterations: {metadata.iterations}")
            print(f"  Tool calls: {metadata.tool_calls}")
            print(f"  Files modified: {metadata.files_modified}")

            if metadata.state.value == "completed":
                print("\n✅ Session completed successfully")
                return 0
            else:
                print(f"\n❌ Session failed: {metadata.error_message}")
                return 1

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


def cmd_openhands_sessions(args: argparse.Namespace) -> int:
    """List OpenHands sessions."""
    repo = Path.cwd()
    agilev_dir = repo / ".agentic-agile-v"

    session_manager = OpenHandsSessionManager(repo, agilev_dir)

    # Filter by task if specified
    resolver = TaskContextResolver()
    task_id = None
    if args.task:
        task_id = resolver.resolve(explicit_task_id=args.task, fail_on_ambiguous=True)

    sessions = session_manager.list_sessions(task_id=task_id)

    if not sessions:
        print("No sessions found")
        return 0

    print(f"{'Session ID':<40} {'Task':<12} {'Role':<10} {'State':<12} {'Created':<20}")
    print("=" * 100)

    for session in sessions:
        created = session.created_at.strftime("%Y-%m-%d %H:%M:%S")
        print(
            f"{session.session_id:<40} {session.task_id:<12} {session.role.value:<10} {session.state.value:<12} {created:<20}"
        )

    return 0


def cmd_openhands_session_show(args: argparse.Namespace) -> int:
    """Show details of a session."""
    repo = Path.cwd()
    agilev_dir = repo / ".agentic-agile-v"

    session_manager = OpenHandsSessionManager(repo, agilev_dir)

    try:
        metadata = session_manager.get_session(args.session_id)

        print(f"Session: {metadata.session_id}")
        print(f"Task: {metadata.task_id}")
        print(f"Role: {metadata.role.value}")
        print(f"State: {metadata.state.value}")
        print("\nTimestamps:")
        print(f"  Created: {metadata.created_at}")
        if metadata.started_at:
            print(f"  Started: {metadata.started_at}")
        if metadata.completed_at:
            print(f"  Completed: {metadata.completed_at}")
            if metadata.started_at:
                duration = (metadata.completed_at - metadata.started_at).total_seconds()
                print(f"  Duration: {duration:.1f}s")

        print("\nMetrics:")
        print(f"  Iterations: {metadata.iterations}")
        print(f"  Tool calls: {metadata.tool_calls}")
        print(f"  Files modified: {metadata.files_modified}")

        if metadata.exit_code is not None:
            print(f"\nExit code: {metadata.exit_code}")

        if metadata.error_message:
            print(f"\nError: {metadata.error_message}")

        if metadata.log_file and metadata.log_file.exists():
            print(f"\nLog file: {metadata.log_file}")
            print("\nRecent log entries:")
            lines = metadata.log_file.read_text().split("\n")
            for line in lines[-10:]:
                if line.strip():
                    print(f"  {line}")

        return 0

    except ValueError as e:
        print(f"❌ {e}")
        return 1


def cmd_openhands_events(args: argparse.Namespace) -> int:
    """Show events from the event ledger."""
    repo = Path.cwd()
    agilev_dir = repo / ".agentic-agile-v"
    ledger_file = agilev_dir / "openhands" / "events.jsonl"

    if not ledger_file.exists():
        print("No events found")
        return 0

    ledger = EventLedger(ledger_file)

    # Get task ID filter if specified
    task_id = None
    if args.task:
        resolver = TaskContextResolver()
        task_id = resolver.resolve(explicit_task_id=args.task, fail_on_ambiguous=True)

    # Get event type filter
    event_type = EventType(args.type) if args.type else None

    # Get events
    events = ledger.get_events(task_id=task_id, event_type=event_type)

    if not events:
        print("No matching events found")
        return 0

    # Display events
    print(f"{'Event ID':<15} {'Type':<25} {'Task':<12} {'Actor':<20} {'Timestamp':<20}")
    print("=" * 100)

    for event in events[-args.limit :]:  # Show last N events
        timestamp = event.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        print(
            f"{event.event_id:<15} {event.event_type.value:<25} {event.task_id or 'N/A':<12} {event.actor:<20} {timestamp:<20}"
        )
        if args.verbose:
            print(f"  Summary: {event.summary}")
            if event.details:
                print(f"  Details: {json.dumps(event.details, indent=4)}")
            print()

    return 0


def cmd_openhands_verify_chain(args: argparse.Namespace) -> int:
    """Verify the integrity of the event chain."""
    repo = Path.cwd()
    agilev_dir = repo / ".agentic-agile-v"
    ledger_file = agilev_dir / "openhands" / "events.jsonl"

    if not ledger_file.exists():
        print("No event ledger found")
        return 0

    ledger = EventLedger(ledger_file)

    print("🔍 Verifying event chain integrity...")

    is_valid, errors = ledger.verify_chain()

    if is_valid:
        print("✅ Event chain is valid!")

        # Show summary
        summary = ledger.get_chain_summary()
        print("\nChain summary:")
        print(f"  Total events: {summary['event_count']}")
        if summary["first_event"]:
            print(
                f"  First event: {summary['first_event']['id']} ({summary['first_event']['timestamp']})"
            )
        if summary["last_event"]:
            print(
                f"  Last event: {summary['last_event']['id']} ({summary['last_event']['timestamp']})"
            )
        print(f"  Head hash: {summary['head_hash'][:16]}...")
        print(f"  Tail hash: {summary['tail_hash'][:16]}...")

        return 0
    else:
        print("❌ Event chain validation failed!")
        print(f"\nFound {len(errors)} error(s):")
        for error in errors:
            print(f"  - {error}")

        return 1


def cmd_openhands_timeline(args: argparse.Namespace) -> int:
    """Show timeline of events for a task."""
    resolver = TaskContextResolver()

    try:
        task_id = resolver.resolve(explicit_task_id=args.task, fail_on_ambiguous=True)

        if not task_id:
            print("❌ No task ID found")
            return 1

        repo = Path.cwd()
        agilev_dir = repo / ".agentic-agile-v"
        ledger_file = agilev_dir / "openhands" / "events.jsonl"

        if not ledger_file.exists():
            print("No events found")
            return 0

        ledger = EventLedger(ledger_file)
        timeline = ledger.export_task_timeline(task_id)

        if not timeline:
            print(f"No events found for task {task_id}")
            return 0

        print(f"Timeline for task {task_id}:")
        print("=" * 80)

        for event_data in timeline:
            timestamp = datetime.fromisoformat(event_data["timestamp"]).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            print(f"\n[{timestamp}] {event_data['event_id']}")
            print(f"  Type: {event_data['event_type']}")
            print(f"  Actor: {event_data['actor']}")
            print(f"  Summary: {event_data['summary']}")
            if event_data.get("details"):
                print(f"  Details: {json.dumps(event_data['details'], indent=4)}")

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


def cmd_openhands_github_actions(args: argparse.Namespace) -> int:
    """Generate GitHub Actions workflows for Agile-V."""
    repo = Path.cwd()

    try:
        generate_github_actions(repo)

        print("\n📋 Workflows generated in .github/workflows/")
        print("\nThese workflows provide:")
        print("  • PR validation (task brief + scope checking)")
        print("  • Evidence collection (on merge to main)")
        print("  • Handoff generation (on PR updates)")
        print("  • Scope compliance checks (on every push)")

        print("\n⚠️  Important:")
        print("  1. Review the generated workflows before committing")
        print("  2. Adjust branch names if you use different main branch")
        print("  3. Configure repository secrets if needed")
        print("  4. Ensure GitHub Actions has appropriate permissions")

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


def cmd_openhands_evidence_collect(args: argparse.Namespace) -> int:
    """Collect evidence from OpenHands session."""
    resolver = TaskContextResolver()

    try:
        task_id = resolver.resolve(explicit_task_id=args.task, fail_on_ambiguous=True)

        if not task_id:
            print("❌ No task ID found. Specify with --task AAV-XXXX or set AGILEV_TASK_ID")
            return 1

        if not resolver.validate_task_exists(task_id):
            print(f"❌ Task {task_id} not found")
            return 1

        print(f"📊 Collecting evidence for task {task_id}...")

        adapter = EvidenceAdapter()

        # Collect evidence from various sources
        evidence = adapter.collect_evidence(task_id)

        # Display collected evidence
        print("\n✅ Evidence collected:")

        if "agent_execution" in evidence:
            print("  🤖 Agent execution:")
            ae = evidence["agent_execution"]
            print(f"     Engine: {ae.get('engine', 'unknown')}")
            print(f"     Mode: {ae.get('mode', 'unknown')}")
            print(f"     Session: {ae.get('session_id', 'unknown')}")

        if "changed_files" in evidence:
            files = evidence["changed_files"]
            print(f"  📁 Changed files: {len(files)}")
            for file in files[:5]:  # Show first 5
                print(f"     - {file}")
            if len(files) > 5:
                print(f"     ... and {len(files) - 5} more")

        if "scope_control" in evidence:
            sc = evidence["scope_control"]
            deps = sc.get("dependency_changes", [])
            if deps:
                print(f"  ⚠️  Dependency changes: {len(deps)}")
                for dep in deps:
                    print(f"     - {dep}")

        if "tests" in evidence:
            tests = evidence["tests"]
            print(f"  🧪 Test results: {len(tests)}")
            passed = sum(1 for t in tests if t.get("status") == "passed")
            failed = sum(1 for t in tests if t.get("status") == "failed")
            print(f"     Passed: {passed}, Failed: {failed}")

        if "checks" in evidence:
            checks = evidence["checks"]
            print(f"  ✓ Checks: {len(checks)}")
            passed = sum(1 for c in checks if c.get("status") == "passed")
            failed = sum(1 for c in checks if c.get("status") == "failed")
            print(f"     Passed: {passed}, Failed: {failed}")

        # Update evidence bundle
        adapter.update_evidence_bundle(task_id, evidence)

        bundle_path = resolver.get_task_dir(task_id) / "evidence_bundle.json"
        print(f"\n✅ Evidence bundle updated: {bundle_path.relative_to(Path.cwd())}")

        return 0

    except FileNotFoundError as e:
        print(f"❌ {e}")
        return 1
    except ValueError as e:
        print(f"❌ {e}")
        return 1
    except Exception as e:
        print(f"❌ Error collecting evidence: {e}")
        import traceback

        traceback.print_exc()
        return 1


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="agilev",
        description="Agentic Agile-V - Evidence-controlled acceptance gates",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # init command
    init_parser = subparsers.add_parser("init", help="Initialize Agentic Agile-V structure")
    init_parser.set_defaults(func=cmd_init)

    # new command
    new_parser = subparsers.add_parser("new", help="Create a new task")
    new_parser.add_argument("--title", required=True, help="Task title")
    new_parser.add_argument(
        "--risk",
        choices=["L0", "L1", "L2", "L3", "L4"],
        default="L1",
        help="Risk level (default: L1)",
    )
    new_parser.set_defaults(func=cmd_new)

    # brief command
    brief_parser = subparsers.add_parser("brief", help="Validate task brief")
    brief_parser.add_argument("task_id", help="Task ID (e.g., AAV-0001)")
    brief_parser.set_defaults(func=cmd_brief)

    # classify command
    classify_parser = subparsers.add_parser("classify", help="Classify task risk level")
    classify_parser.add_argument("task_id", help="Task ID")
    classify_parser.set_defaults(func=cmd_classify)

    # impact command
    impact_parser = subparsers.add_parser("impact", help="Create impact analysis")
    impact_parser.add_argument("task_id", help="Task ID")
    impact_parser.set_defaults(func=cmd_impact)

    # validate command
    validate_parser = subparsers.add_parser("validate", help="Run validation checks")
    validate_parser.set_defaults(func=cmd_validate)

    # evidence command
    evidence_parser = subparsers.add_parser("evidence", help="Manage evidence bundles")
    evidence_parser.add_argument("task_id", help="Task ID")
    evidence_parser.add_argument("--add-file", help="Add a file to the evidence bundle")
    evidence_parser.set_defaults(func=cmd_evidence)

    # status command
    status_parser = subparsers.add_parser("status", help="Show current process status")
    status_parser.set_defaults(func=cmd_status)

    # handoff command
    handoff_parser = subparsers.add_parser("handoff", help="Create handoff document")
    handoff_parser.add_argument("task_id", help="Task ID")
    handoff_parser.set_defaults(func=cmd_handoff)

    # lock command
    lock_parser = subparsers.add_parser("lock", help="Acquire lock on files")
    lock_parser.add_argument("task_id", help="Task ID")
    lock_parser.add_argument("--actor", required=True, help="Actor name")
    lock_parser.add_argument("--files", required=True, help="Comma-separated file paths")
    lock_parser.add_argument("--intent", required=True, help="Description of intended changes")
    lock_parser.add_argument("--ttl", type=int, default=2, help="Lock TTL in hours (default: 2)")
    lock_parser.set_defaults(func=cmd_lock)

    # unlock command
    unlock_parser = subparsers.add_parser("unlock", help="Release locks")
    unlock_parser.add_argument("task_id", help="Task ID")
    unlock_parser.add_argument("--actor", required=True, help="Actor name")
    unlock_parser.set_defaults(func=cmd_unlock)

    # openhands command group
    openhands_parser = subparsers.add_parser("openhands", help="OpenHands integration commands")
    openhands_subparsers = openhands_parser.add_subparsers(dest="openhands_command", required=True)

    # openhands init
    oh_init_parser = openhands_subparsers.add_parser(
        "init", help="Initialize OpenHands integration"
    )
    oh_init_parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    oh_init_parser.set_defaults(func=cmd_openhands_init)

    # openhands doctor
    oh_doctor_parser = openhands_subparsers.add_parser("doctor", help="Validate OpenHands setup")
    oh_doctor_parser.set_defaults(func=cmd_openhands_doctor)

    # openhands scaffold
    oh_scaffold_parser = openhands_subparsers.add_parser(
        "scaffold", help="Regenerate integration files"
    )
    oh_scaffold_parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    oh_scaffold_parser.set_defaults(func=cmd_openhands_scaffold)

    # openhands validate
    oh_validate_parser = openhands_subparsers.add_parser(
        "validate", help="Validate OpenHands session"
    )
    oh_validate_parser.add_argument("--task", help="Task ID (e.g., AAV-0001)")
    oh_validate_parser.add_argument("--scope", action="store_true", help="Validate scope control")
    oh_validate_parser.set_defaults(func=cmd_openhands_validate)

    # openhands evidence collect
    oh_evidence_parser = openhands_subparsers.add_parser(
        "evidence", help="Collect evidence from OpenHands session"
    )
    oh_evidence_subparsers = oh_evidence_parser.add_subparsers(
        dest="evidence_command", required=True
    )

    oh_evidence_collect_parser = oh_evidence_subparsers.add_parser(
        "collect", help="Collect evidence"
    )
    oh_evidence_collect_parser.add_argument("--task", help="Task ID (e.g., AAV-0001)")
    oh_evidence_collect_parser.set_defaults(func=cmd_openhands_evidence_collect)

    # openhands handoff
    oh_handoff_parser = openhands_subparsers.add_parser("handoff", help="Show handoff report")
    oh_handoff_parser.add_argument("--task", help="Task ID (e.g., AAV-0001)")
    oh_handoff_parser.set_defaults(func=cmd_openhands_handoff)

    # openhands run
    oh_run_parser = openhands_subparsers.add_parser("run", help="Run OpenHands session")
    oh_run_parser.add_argument("--task", help="Task ID (e.g., AAV-0001)")
    oh_run_parser.add_argument("--prompt", help="Prompt for the agent")
    oh_run_parser.add_argument(
        "--builder-verifier", action="store_true", help="Use builder/verifier workflow"
    )
    oh_run_parser.add_argument(
        "--max-iterations", type=int, default=50, help="Maximum iterations (default: 50)"
    )
    oh_run_parser.add_argument(
        "--timeout", type=int, default=3600, help="Timeout in seconds (default: 3600)"
    )
    oh_run_parser.add_argument("--model", default="gpt-4", help="Model to use (default: gpt-4)")
    oh_run_parser.set_defaults(func=cmd_openhands_run)

    # openhands sessions
    oh_sessions_parser = openhands_subparsers.add_parser("sessions", help="List OpenHands sessions")
    oh_sessions_parser.add_argument("--task", help="Filter by task ID")
    oh_sessions_parser.set_defaults(func=cmd_openhands_sessions)

    # openhands session
    oh_session_parser = openhands_subparsers.add_parser("session", help="Show session details")
    oh_session_parser.add_argument("session_id", help="Session ID")
    oh_session_parser.set_defaults(func=cmd_openhands_session_show)

    # openhands github-actions
    oh_gh_parser = openhands_subparsers.add_parser(
        "github-actions", help="Generate GitHub Actions workflows"
    )
    oh_gh_parser.set_defaults(func=cmd_openhands_github_actions)

    # openhands events
    oh_events_parser = openhands_subparsers.add_parser("events", help="Show event ledger")
    oh_events_parser.add_argument("--task", help="Filter by task ID")
    oh_events_parser.add_argument("--type", help="Filter by event type")
    oh_events_parser.add_argument(
        "--limit", type=int, default=50, help="Max events to show (default: 50)"
    )
    oh_events_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show full event details"
    )
    oh_events_parser.set_defaults(func=cmd_openhands_events)

    # openhands verify-chain
    oh_verify_parser = openhands_subparsers.add_parser(
        "verify-chain", help="Verify event chain integrity"
    )
    oh_verify_parser.set_defaults(func=cmd_openhands_verify_chain)

    # openhands timeline
    oh_timeline_parser = openhands_subparsers.add_parser("timeline", help="Show task timeline")
    oh_timeline_parser.add_argument("--task", help="Task ID")
    oh_timeline_parser.set_defaults(func=cmd_openhands_timeline)

    # PCB commands
    build_pcb_parser(subparsers)

    # Embedded systems commands
    build_embedded_parser(subparsers)

    # Firmware commands
    build_firmware_parser(subparsers)

    # Software commands
    build_software_parser(subparsers)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Main CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
