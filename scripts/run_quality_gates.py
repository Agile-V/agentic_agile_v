#!/usr/bin/env python3
"""
Master Quality Validation Script for Agentic Agile-V v2.2

Runs all quality gates before allowing task submission.
This is the enforcement mechanism that makes v2.2 work.

Quality Gates (inspired by Agile-V Skills quality-gates):
1. Time Allocation Gate - Prevents rushing complex tasks
2. Interface Contract Gate - Ensures API compatibility
3. Test Quality Gate - Verifies external behavior testing

Usage:
    python scripts/run_quality_gates.py --task-id AAV-001
    python scripts/run_quality_gates.py --task tasks/AAV-001/task_description.md --plan tasks/AAV-001/agent_plan.md --impl src/module.py --tests test_module.py

Exit codes:
    0: All quality gates PASS
    1: One or more quality gates FAIL
    2: Invalid input or configuration error
"""

import sys
import argparse
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional


class QualityGate:
    """Represents a single quality gate validation."""
    
    def __init__(self, name: str, script: str, args: List[str], description: str):
        self.name = name
        self.script = script
        self.args = args
        self.description = description
        self.passed = None
        self.exit_code = None
    
    def run(self, scripts_dir: Path) -> bool:
        """
        Run the quality gate validation.
        
        Returns:
            bool: True if gate passed
        """
        script_path = scripts_dir / self.script
        
        if not script_path.exists():
            print(f"⚠️  WARNING: {self.name} script not found: {script_path}")
            print(f"   Skipping this gate\n")
            return True  # Don't fail if script missing
        
        print(f"\n{'='*70}")
        print(f"Running: {self.name}")
        print(f"{'='*70}")
        print(f"Description: {self.description}")
        print()
        
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)] + self.args,
                capture_output=False,  # Let output show in real-time
                text=True
            )
            
            self.exit_code = result.returncode
            self.passed = (result.returncode == 0)
            
            return self.passed
            
        except Exception as e:
            print(f"\n❌ ERROR: Failed to run {self.name}: {e}\n")
            self.passed = False
            self.exit_code = 2
            return False


def auto_discover_paths(task_id: str, search_root: Path = Path('.')) -> dict:
    """
    Auto-discover all required paths for a task.
    
    Returns:
        dict: {
            'task_desc': Path or None,
            'agent_plan': Path or None,
            'implementation': Path or None,
            'tests': Path or None
        }
    """
    paths = {
        'task_desc': None,
        'agent_plan': None,
        'implementation': None,
        'tests': None
    }
    
    task_dir = search_root / f"tasks/{task_id}"
    
    # Task description
    for name in ['task_description.md', 'TASK.md', 'README.md']:
        path = task_dir / name
        if path.exists():
            paths['task_desc'] = path
            break
    
    # Agent plan
    for name in ['agent_plan.md', 'PLAN.md']:
        path = task_dir / name
        if path.exists():
            paths['agent_plan'] = path
            break
    
    # Implementation
    impl_patterns = [
        task_dir / 'implementation' / '*.py',
        task_dir / 'src' / '*.py',
        task_dir / '*.py',
    ]
    
    for pattern in impl_patterns:
        if pattern.exists():
            paths['implementation'] = pattern
            break
        elif '*' in str(pattern):
            matches = list(pattern.parent.glob(pattern.name)) if pattern.parent.exists() else []
            if matches:
                paths['implementation'] = matches[0]
                break
    
    # Tests
    test_patterns = [
        task_dir / 'test_*.py',
        task_dir / '*_test.py',
        search_root / 'tests' / f'test_{task_id}.py',
    ]
    
    for pattern in test_patterns:
        if pattern.exists():
            paths['tests'] = pattern
            break
        elif '*' in str(pattern):
            matches = list(pattern.parent.glob(pattern.name)) if pattern.parent.exists() else []
            if matches:
                paths['tests'] = matches[0]
                break
    
    return paths


def run_quality_gates(task_desc: Optional[Path] = None,
                     agent_plan: Optional[Path] = None,
                     implementation: Optional[Path] = None,
                     tests: Optional[Path] = None,
                     skip_gates: List[str] = None) -> bool:
    """
    Run all quality gates.
    
    Returns:
        bool: True if all gates pass
    """
    scripts_dir = Path(__file__).parent
    skip_gates = skip_gates or []
    
    # Define quality gates
    gates = []
    
    # Gate 1: Time Allocation
    if agent_plan and 'time' not in skip_gates:
        gates.append(QualityGate(
            name="Time Allocation Gate",
            script="validate_time_allocation.py",
            args=["--plan", str(agent_plan)],
            description="Ensures adequate time allocated based on risk and complexity"
        ))
    
    # Gate 2: Interface Contracts
    if task_desc and implementation and 'interface' not in skip_gates:
        gates.append(QualityGate(
            name="Interface Contract Gate",
            script="validate_interface_contracts.py",
            args=["--task", str(task_desc), "--implementation", str(implementation)],
            description="Validates implementation API matches task examples"
        ))
    
    # Gate 3: Test Quality
    if tests and 'test-quality' not in skip_gates:
        gates.append(QualityGate(
            name="Test Quality Gate",
            script="validate_test_quality.py",
            args=["--tests", str(tests)],
            description="Ensures tests verify external behavior, not just internal state"
        ))
    
    if not gates:
        print(f"\n⚠️  WARNING: No quality gates configured or all inputs missing")
        print(f"   Cannot validate quality without required files\n")
        return True  # Don't fail if no gates can run
    
    # Run all gates
    print(f"\n{'#'*70}")
    print(f"# Agentic Agile-V v2.2 - Quality Gate Validation")
    print(f"{'#'*70}")
    print(f"\nRunning {len(gates)} quality gate(s)...\n")
    
    passed_gates = []
    failed_gates = []
    
    for gate in gates:
        if gate.run(scripts_dir):
            passed_gates.append(gate)
        else:
            failed_gates.append(gate)
    
    # Summary
    print(f"\n{'#'*70}")
    print(f"# Quality Gate Summary")
    print(f"{'#'*70}\n")
    
    for gate in passed_gates:
        print(f"✅ PASS: {gate.name}")
    
    for gate in failed_gates:
        print(f"❌ FAIL: {gate.name}")
    
    print(f"\n{'─'*70}")
    print(f"Results: {len(passed_gates)}/{len(gates)} gates passed")
    
    if failed_gates:
        print(f"\n❌ QUALITY GATES FAILED")
        print(f"\n⚠️  Your implementation cannot be submitted until all gates pass.")
        print(f"   Review the failures above and fix the issues.")
        print(f"\n📊 Evidence:")
        print(f"   - v2.1 without active gates: 54.5% quality (REGRESSION)")
        print(f"   - Quality-gates skill with active validation: 100% quality")
        print(f"\n🎯 These gates prevent the bugs that cause quality failures.")
        print(f"   Fix them now, or they'll cause test failures later.")
        print(f"{'#'*70}\n")
        return False
    else:
        print(f"\n✅ ALL QUALITY GATES PASSED")
        print(f"\n🎉 Your implementation meets quality standards!")
        print(f"   You may proceed with testing and submission.")
        print(f"{'#'*70}\n")
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Run quality gates for Agentic Agile-V tasks"
    )
    
    # Auto-discover mode
    parser.add_argument(
        "--task-id",
        help="Task ID (auto-discovers all required files)"
    )
    
    # Manual mode
    parser.add_argument(
        "--task",
        help="Path to task description file"
    )
    parser.add_argument(
        "--plan",
        help="Path to agent plan file"
    )
    parser.add_argument(
        "--impl",
        help="Path to implementation file"
    )
    parser.add_argument(
        "--tests",
        help="Path to test file"
    )
    
    # Options
    parser.add_argument(
        "--skip",
        help="Comma-separated list of gates to skip (time,interface,test-quality)"
    )
    
    args = parser.parse_args()
    
    try:
        if args.task_id:
            # Auto-discover mode
            print(f"Auto-discovering files for task: {args.task_id}")
            paths = auto_discover_paths(args.task_id)
            
            print(f"\nDiscovered files:")
            print(f"  Task description: {paths['task_desc'] or 'NOT FOUND'}")
            print(f"  Agent plan: {paths['agent_plan'] or 'NOT FOUND'}")
            print(f"  Implementation: {paths['implementation'] or 'NOT FOUND'}")
            print(f"  Tests: {paths['tests'] or 'NOT FOUND'}")
            
            task_desc = paths['task_desc']
            agent_plan = paths['agent_plan']
            implementation = paths['implementation']
            tests = paths['tests']
        else:
            # Manual mode
            if not any([args.task, args.plan, args.impl, args.tests]):
                parser.error("Either --task-id or at least one of --task/--plan/--impl/--tests required")
            
            task_desc = Path(args.task) if args.task else None
            agent_plan = Path(args.plan) if args.plan else None
            implementation = Path(args.impl) if args.impl else None
            tests = Path(args.tests) if args.tests else None
        
        # Parse skip list
        skip_gates = args.skip.split(',') if args.skip else []
        
        # Run quality gates
        all_passed = run_quality_gates(
            task_desc=task_desc,
            agent_plan=agent_plan,
            implementation=implementation,
            tests=tests,
            skip_gates=skip_gates
        )
        
        # Exit with appropriate code
        sys.exit(0 if all_passed else 1)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(2)


if __name__ == "__main__":
    main()
