#!/usr/bin/env python3
"""
Test Quality Validator for Agentic Agile-V

Validates that tests check external behavior, not just internal state.
Prevents the self-assessment gap where tests pass but hidden tests fail.

This validator catches tests that only check:
- Internal queues/buffers
- Private state
- Data structures
- Configuration

And ensures tests verify:
- External API calls (connection.send(), callbacks, etc.)
- Observable behavior
- User-facing outcomes
- Integration points

Usage:
    python scripts/validate_test_quality.py --tests test_module.py
    python scripts/validate_test_quality.py --task-id AAV-001

Exit codes:
    0: Tests verify external behavior
    1: Tests only check internal state (quality issue)
    2: Invalid input or usage error

Inspired by: Agile-V Skills quality-gates (Test Quality Gate)
"""

import argparse
import ast
import re
import sys
from pathlib import Path
from typing import Any

# Patterns that indicate external behavior checking
EXTERNAL_PATTERNS = [
    r'\.send\(',           # connection.send()
    r'\.recv\(',           # connection.recv()
    r'\.on_',              # event callbacks
    r'mock.*\.called',     # mock verification
    r'mock.*\.assert',     # mock assertions
    r'spy.*\.called',      # spy verification
    r'\.emit\(',           # event emission
    r'\.publish\(',        # message publishing
    r'\.dispatch\(',       # event dispatch
    r'\.invoke\(',         # method invocation
    r'\.execute\(',        # execution
    r'observable',         # observable behavior
    r'side_effect',        # side effects
    r'\.write\(',          # file/stream writes
    r'\.read\(',           # file/stream reads
]

# Patterns that indicate internal state checking (red flag)
INTERNAL_PATTERNS = [
    r'\._\w+',             # private attributes (_internal_queue)
    r'\.queue',            # direct queue access
    r'\.buffer',           # direct buffer access
    r'len\(.*\..*\)',      # checking collection sizes
    r'\.get\(',            # queue.get()
    r'\.qsize\(',          # queue.qsize()
    r'\.empty\(',          # queue.empty()
    r'in self\._',         # checking private collections
]


def parse_test_file(test_path: Path) -> list[dict[str, Any]]:
    """
    Parse test file to extract test functions and their assertions.
    
    Returns:
        list: [
            {
                'name': 'test_name',
                'asserts': ['assert x.send() was called', ...],
                'checks_external': bool,
                'checks_internal': bool
            }
        ]
    """
    if not test_path.exists():
        raise FileNotFoundError(f"Test file not found: {test_path}")
    
    with open(test_path) as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        raise ValueError(f"Cannot parse test file (syntax error): {e}")
    
    tests = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Check if it's a test function
            if not node.name.startswith('test_'):
                continue
            
            # Extract assertions and checks
            asserts = []
            checks_external = False
            checks_internal = False
            
            # Get source code of the function
            try:
                func_lines = content.splitlines()[node.lineno - 1:node.end_lineno]
                func_source = '\n'.join(func_lines)
                
                # Check for external patterns
                for pattern in EXTERNAL_PATTERNS:
                    if re.search(pattern, func_source):
                        checks_external = True
                        break
                
                # Check for internal patterns
                for pattern in INTERNAL_PATTERNS:
                    if re.search(pattern, func_source):
                        checks_internal = True
                        break
                
                # Extract assertions
                for subnode in ast.walk(node):
                    if isinstance(subnode, ast.Assert):
                        asserts.append(ast.unparse(subnode.test))
            
            except Exception:
                # If we can't parse, mark as unknown
                pass
            
            tests.append({
                'name': node.name,
                'asserts': asserts,
                'checks_external': checks_external,
                'checks_internal': checks_internal,
                'line': node.lineno
            })
    
    return tests


def validate_test_quality(test_path: Path) -> bool:
    """
    Validate that tests check external behavior.
    
    Returns:
        bool: True if tests are adequate quality
    """
    print(f"\n{'='*70}")
    print("Test Quality Validation")
    print(f"{'='*70}")
    print(f"Test File: {test_path}")
    print(f"{'─'*70}\n")
    
    # Parse tests
    try:
        tests = parse_test_file(test_path)
        print(f"📋 Found {len(tests)} test function(s)\n")
    except Exception as e:
        print(f"❌ ERROR: Failed to parse test file: {e}\n", file=sys.stderr)
        return False
    
    if not tests:
        print("⚠️  WARNING: No test functions found (no functions starting with 'test_')")
        print("   Cannot validate test quality\n")
        return True  # Don't fail if no tests found
    
    # Analyze each test
    external_count = 0
    internal_only_count = 0
    neither_count = 0
    
    problematic_tests = []
    
    for test in tests:
        status = ""
        
        if test['checks_external']:
            status = "✅ Checks external behavior"
            external_count += 1
        elif test['checks_internal']:
            status = "⚠️  Only checks internal state"
            internal_only_count += 1
            problematic_tests.append(test)
        else:
            status = "❓ No clear external checks"
            neither_count += 1
        
        print(f"{status:40} {test['name']}")
    
    print(f"\n{'─'*70}")
    print("Test Quality Summary:")
    print(f"  ✅ External behavior: {external_count}/{len(tests)}")
    print(f"  ⚠️  Internal state only: {internal_only_count}/{len(tests)}")
    print(f"  ❓ Unclear: {neither_count}/{len(tests)}")
    
    # Calculate quality score
    quality_percentage = (external_count / len(tests)) * 100 if tests else 0
    
    # Pass criteria: at least 70% of tests check external behavior
    is_adequate = quality_percentage >= 70
    
    print(f"\n{'─'*70}")
    
    if is_adequate:
        print(f"✅ PASS: Test quality is adequate ({quality_percentage:.0f}% check external behavior)")
        print(f"{'='*70}\n")
        return True
    else:
        print(f"❌ FAIL: Test quality is inadequate ({quality_percentage:.0f}% check external behavior)")
        print("\n⚠️  CRITICAL: Tests that only check internal state create false confidence.")
        print("   Your tests may pass while hidden tests fail.")
        print("\n📊 Evidence from Agentic Agile-V v2.0:")
        print("   - Self tests: 100% pass (tests checked queue sizes)")
        print("   - Hidden tests: 68% pass (tests checked actual message delivery)")
        print("   - Gap: -32% self-assessment error")
        print("\n🔧 Problematic Tests:")
        
        for test in problematic_tests:
            print(f"   - {test['name']} (line {test['line']})")
            print("     Issue: Checking internal state (queues, buffers, private attrs)")
            print("     Fix: Verify external calls like connection.send(), callbacks, etc.")
        
        print("\n💡 How to Fix:")
        print("   1. Replace internal checks with external behavior verification")
        print("   2. Use mocks to verify method calls: mock_conn.send.assert_called()")
        print("   3. Check observable outputs, not internal queues")
        print("   4. Test what the USER sees, not what the CODE stores")
        print("\n✅ Good Example:")
        print("   # Instead of:")
        print("   assert len(router._message_queues[client_id]) == 1  # ❌ internal")
        print("   ")
        print("   # Do this:")
        print("   mock_connection.send.assert_called_once_with(message)  # ✅ external")
        print(f"{'='*70}\n")
        return False


def find_test_file(task_id: str, search_root: Path = Path('.')) -> Optional[Path]:
    """
    Auto-discover test file for a task ID.
    
    Returns:
        Path to test file or None if not found
    """
    test_patterns = [
        search_root / f"tasks/{task_id}/test_*.py",
        search_root / f"tasks/{task_id}/*_test.py",
        search_root / "tests/test_*.py",
        search_root / "test_*.py",
    ]
    
    for pattern in test_patterns:
        if '*' in str(pattern):
            matches = list(pattern.parent.glob(pattern.name))
            if matches:
                return matches[0]
        elif pattern.exists():
            return pattern
    
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Validate test quality for Agentic Agile-V tasks"
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--task-id",
        help="Task ID (auto-discovers test file)"
    )
    group.add_argument(
        "--tests",
        help="Path to test file"
    )
    
    args = parser.parse_args()
    
    try:
        if args.task_id:
            # Auto-discover test file
            test_path = find_test_file(args.task_id)
            
            if test_path is None:
                print(f"\n❌ ERROR: Could not find test file for {args.task_id}\n", file=sys.stderr)
                sys.exit(2)
        else:
            test_path = Path(args.tests)
        
        # Validate
        is_adequate = validate_test_quality(test_path)
        
        # Exit with appropriate code
        sys.exit(0 if is_adequate else 1)
        
    except (FileNotFoundError, ValueError) as e:
        print(f"\n❌ ERROR: {e}\n", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}\n", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(2)


if __name__ == "__main__":
    main()
