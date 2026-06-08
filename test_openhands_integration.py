#!/usr/bin/env python3
"""Test script for OpenHands integration."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agilev.openhands.scaffold import OpenHandsScaffold
from agilev.task_context import TaskContextResolver

def test_scaffold():
    """Test OpenHandsScaffold."""
    print("Testing OpenHandsScaffold...")
    
    scaffold = OpenHandsScaffold()
    
    # Test doctor (before init)
    checks = scaffold.doctor()
    print(f"  Doctor checks (before init): {sum(checks.values())}/{len(checks)} passed")
    
    # Test init
    print("  Running init...")
    created = scaffold.init(force=True)
    print(f"  Created {len(created)} files")
    
    # Test doctor (after init)
    checks = scaffold.doctor()
    passed = sum(checks.values())
    total = len(checks)
    print(f"  Doctor checks (after init): {passed}/{total} passed")
    
    if passed == total:
        print("  ✅ All checks passed!")
    else:
        failed_checks = [k for k, v in checks.items() if not v]
        print(f"  ❌ Failed checks: {failed_checks}")
    
    return passed == total

def test_task_context():
    """Test TaskContextResolver."""
    print("\nTesting TaskContextResolver...")
    
    resolver = TaskContextResolver()
    
    # Test explicit task ID
    task_id = resolver.resolve(explicit_task_id="AAV-001")
    print(f"  Explicit AAV-001 -> {task_id}")
    assert task_id == "AAV-0001", f"Expected AAV-0001, got {task_id}"
    
    # Test normalization
    task_id = resolver.resolve(explicit_task_id="aav-42")
    print(f"  Normalized aav-42 -> {task_id}")
    assert task_id == "AAV-0042", f"Expected AAV-0042, got {task_id}"
    
    print("  ✅ Task context resolver works!")
    return True

def main():
    """Run tests."""
    print("="* 60)
    print("OpenHands Integration Test")
    print("="* 60)
    
    success = True
    
    success &= test_scaffold()
    success &= test_task_context()
    
    print("\n" + "="* 60)
    if success:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
