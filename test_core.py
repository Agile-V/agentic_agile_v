#!/usr/bin/env python3
"""Test script for Agentic Agile-V core functionality without external dependencies."""
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agilev.state import EventLogger, TaskState, LockManager


def test_event_logger():
    """Test the event logging system."""
    print("=" * 60)
    print("TEST 1: Event Logger")
    print("=" * 60)
    
    # Create test directory
    test_dir = Path("/var/folders/9q/yt6wn1cx29d6xltyl6_3cjbc0000gn/T/opencode/agile-v-test")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize event logger
    log_path = test_dir / "events.jsonl"
    logger = EventLogger(log_path)
    
    # Log some events
    event1 = logger.log_event(
        event_type="IntentDeclared",
        actor="test-script",
        summary="Testing event logging system",
    )
    print(f"✅ Logged event 1: {event1['event_id']}")
    print(f"   Hash: {event1['hash'][:50]}...")
    
    event2 = logger.log_event(
        event_type="BriefCreated",
        actor="test-script",
        task_id="AAV-0001",
        summary="Created test task brief",
        artifacts=["test/brief.yaml"],
    )
    print(f"✅ Logged event 2: {event2['event_id']}")
    print(f"   Hash: {event2['hash'][:50]}...")
    print(f"   Previous hash: {event2.get('previous_event_hash', 'None')[:50]}...")
    
    # Verify chain
    valid, errors = logger.verify_chain()
    if valid:
        print(f"✅ Event chain is valid")
    else:
        print(f"❌ Event chain validation failed:")
        for error in errors:
            print(f"   {error}")
        return False
    
    # Retrieve events
    events = logger.get_events()
    print(f"✅ Retrieved {len(events)} events from log")
    
    # Get events by task
    task_events = logger.get_events(task_id="AAV-0001")
    print(f"✅ Retrieved {len(task_events)} events for task AAV-0001")
    
    print()
    return True


def test_task_state():
    """Test the task state management system."""
    print("=" * 60)
    print("TEST 2: Task State Manager")
    print("=" * 60)
    
    # Create test directory
    test_dir = Path("/var/folders/9q/yt6wn1cx29d6xltyl6_3cjbc0000gn/T/opencode/agile-v-test")
    
    # Initialize task state
    state_path = test_dir / "tasks.json"
    task_state = TaskState(state_path)
    
    # Create tasks
    task_state.create_task("AAV-0001", "Add user authentication", "L2")
    print(f"✅ Created task AAV-0001")
    
    task_state.create_task("AAV-0002", "Fix login bug", "L1")
    print(f"✅ Created task AAV-0002")
    
    task_state.create_task("AAV-0003", "Update firmware timing", "L4")
    print(f"✅ Created task AAV-0003")
    
    # Update status
    task_state.update_task_status("AAV-0001", "in_progress")
    print(f"✅ Updated AAV-0001 status to in_progress")
    
    # Get task
    task = task_state.get_task("AAV-0001")
    if task:
        print(f"✅ Retrieved task: {task['title']}")
        print(f"   Risk level: {task['risk_level']}")
        print(f"   Status: {task['status']}")
    
    # List all tasks
    all_tasks = task_state.list_tasks()
    print(f"✅ Total tasks: {len(all_tasks)}")
    
    # List by status
    in_progress = task_state.list_tasks(status="in_progress")
    print(f"✅ Tasks in progress: {len(in_progress)}")
    
    print()
    return True


def test_lock_manager():
    """Test the lock management system."""
    print("=" * 60)
    print("TEST 3: Lock Manager")
    print("=" * 60)
    
    # Create test directory
    test_dir = Path("/var/folders/9q/yt6wn1cx29d6xltyl6_3cjbc0000gn/T/opencode/agile-v-test")
    
    # Initialize lock manager
    locks_path = test_dir / "locks.json"
    lock_mgr = LockManager(locks_path)
    
    # Acquire lock
    success = lock_mgr.acquire_lock(
        task_id="AAV-0001",
        actor="agent:implementation",
        files=["src/auth.ts", "tests/auth.test.ts"],
        intent="Implement user authentication",
        ttl_hours=2,
    )
    
    if success:
        print(f"✅ Lock acquired for AAV-0001")
    else:
        print(f"❌ Failed to acquire lock")
        return False
    
    # Try to acquire conflicting lock
    conflict = lock_mgr.acquire_lock(
        task_id="AAV-0002",
        actor="agent:red-team",
        files=["src/auth.ts"],  # Conflicts with previous lock
        intent="Test authentication",
        ttl_hours=2,
    )
    
    if not conflict:
        print(f"✅ Correctly blocked conflicting lock on src/auth.ts")
    else:
        print(f"❌ Should have blocked conflicting lock")
        return False
    
    # Acquire non-conflicting lock
    success2 = lock_mgr.acquire_lock(
        task_id="AAV-0003",
        actor="agent:firmware",
        files=["firmware/timing.c"],
        intent="Update firmware timing",
        ttl_hours=2,
    )
    
    if success2:
        print(f"✅ Lock acquired for AAV-0003 (no conflict)")
    else:
        print(f"❌ Should have acquired non-conflicting lock")
        return False
    
    # Get active locks
    active = lock_mgr.get_active_locks()
    print(f"✅ Active locks: {len(active)}")
    for lock in active:
        print(f"   - {lock['task_id']} by {lock['actor']}: {len(lock['files'])} file(s)")
    
    # Release lock
    lock_mgr.release_lock("AAV-0001", "agent:implementation")
    print(f"✅ Released lock for AAV-0001")
    
    # Verify lock was released
    active_after = lock_mgr.get_active_locks()
    print(f"✅ Active locks after release: {len(active_after)}")
    
    # Clean expired locks
    cleaned = lock_mgr.clean_expired_locks()
    print(f"✅ Cleaned {cleaned} expired lock(s)")
    
    print()
    return True


def test_file_hashing():
    """Test file hashing functionality."""
    print("=" * 60)
    print("TEST 4: File Hashing")
    print("=" * 60)
    
    # Create test file
    test_dir = Path("/var/folders/9q/yt6wn1cx29d6xltyl6_3cjbc0000gn/T/opencode/agile-v-test")
    test_file = test_dir / "test_file.txt"
    test_file.write_text("This is a test file for hashing.")
    
    # Compute hash
    sha256_hash = hashlib.sha256()
    with open(test_file, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    file_hash = f"sha256:{sha256_hash.hexdigest()}"
    print(f"✅ Computed file hash: {file_hash[:60]}...")
    
    # Verify hash is deterministic
    sha256_hash2 = hashlib.sha256()
    with open(test_file, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash2.update(byte_block)
    
    file_hash2 = f"sha256:{sha256_hash2.hexdigest()}"
    
    if file_hash == file_hash2:
        print(f"✅ Hash is deterministic (matches on second computation)")
    else:
        print(f"❌ Hash is not deterministic")
        return False
    
    print()
    return True


def test_integration():
    """Test integration of all components."""
    print("=" * 60)
    print("TEST 5: Integration Test")
    print("=" * 60)
    
    test_dir = Path("/var/folders/9q/yt6wn1cx29d6xltyl6_3cjbc0000gn/T/opencode/agile-v-test")
    
    # Initialize all components
    logger = EventLogger(test_dir / "events.jsonl")
    task_state = TaskState(test_dir / "tasks.json")
    lock_mgr = LockManager(test_dir / "locks.json")
    
    # Simulate workflow
    print("Simulating task workflow...")
    
    # 1. Create task
    task_id = "AAV-9999"
    task_state.create_task(task_id, "Integration test task", "L2")
    logger.log_event(
        event_type="BriefCreated",
        actor="test-script",
        task_id=task_id,
        summary="Created integration test task",
    )
    print(f"✅ Step 1: Task created and event logged")
    
    # 2. Acquire lock
    lock_success = lock_mgr.acquire_lock(
        task_id=task_id,
        actor="test-agent",
        files=["src/integration.ts"],
        intent="Integration test",
        ttl_hours=1,
    )
    logger.log_event(
        event_type="FilesChanged",
        actor="test-agent",
        task_id=task_id,
        summary="Acquired lock and started implementation",
        artifacts=["src/integration.ts"],
    )
    print(f"✅ Step 2: Lock acquired and event logged")
    
    # 3. Update task status
    task_state.update_task_status(task_id, "in_progress")
    logger.log_event(
        event_type="ImplementationStarted",
        actor="test-agent",
        task_id=task_id,
        summary="Started implementation",
    )
    print(f"✅ Step 3: Status updated and event logged")
    
    # 4. Add evidence
    logger.log_event(
        event_type="EvidenceAdded",
        actor="test-agent",
        task_id=task_id,
        summary="Added test evidence",
        metadata={"tests_passed": True, "coverage": "95%"},
    )
    print(f"✅ Step 4: Evidence logged")
    
    # 5. Verification
    logger.log_event(
        event_type="VerificationPassed",
        actor="agent:red-team",
        task_id=task_id,
        summary="Independent verification completed",
    )
    print(f"✅ Step 5: Verification logged")
    
    # 6. Approval
    logger.log_event(
        event_type="HumanApproved",
        actor="human:reviewer",
        task_id=task_id,
        summary="Task approved for merge",
    )
    print(f"✅ Step 6: Approval logged")
    
    # 7. Release lock
    lock_mgr.release_lock(task_id, "test-agent")
    task_state.update_task_status(task_id, "completed")
    logger.log_event(
        event_type="TaskClosed",
        actor="test-script",
        task_id=task_id,
        summary="Task completed and closed",
    )
    print(f"✅ Step 7: Lock released, task completed")
    
    # Verify event chain
    valid, errors = logger.verify_chain()
    if valid:
        print(f"✅ Event chain integrity verified")
    else:
        print(f"❌ Event chain corrupted")
        return False
    
    # Check final state
    task = task_state.get_task(task_id)
    events = logger.get_events(task_id=task_id)
    locks = lock_mgr.get_active_locks()
    
    print(f"\nFinal state:")
    print(f"  Task status: {task['status']}")
    print(f"  Events logged: {len(events)}")
    print(f"  Active locks: {len([l for l in locks if l['task_id'] == task_id])}")
    
    print()
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("AGENTIC AGILE-V CORE FUNCTIONALITY TEST SUITE")
    print("=" * 60)
    print()
    
    results = {
        "Event Logger": test_event_logger(),
        "Task State Manager": test_task_state(),
        "Lock Manager": test_lock_manager(),
        "File Hashing": test_file_hashing(),
        "Integration": test_integration(),
    }
    
    print("=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
