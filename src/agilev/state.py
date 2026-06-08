"""Agentic Agile-V State Kernel - Event logging and state management."""
from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class EventLogger:
    """Manages the append-only event log for Agile-V process history."""

    def __init__(self, log_path: Path | None = None):
        """Initialize the event logger.
        
        Args:
            log_path: Path to events.jsonl file. Defaults to .agentic-agile-v/state/events.jsonl
        """
        if log_path is None:
            log_path = Path.cwd() / ".agentic-agile-v" / "state" / "events.jsonl"
        
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._last_event_hash: str | None = None
        
        # Load the last event hash if the log exists
        if self.log_path.exists():
            self._load_last_hash()
    
    def _load_last_hash(self) -> None:
        """Load the hash of the last event in the log."""
        try:
            with open(self.log_path) as f:
                lines = f.readlines()
                if lines:
                    last_event = json.loads(lines[-1])
                    self._last_event_hash = last_event.get('hash')
        except (json.JSONDecodeError, KeyError):
            self._last_event_hash = None
    
    def _generate_event_id(self) -> str:
        """Generate a unique event ID."""
        # Count existing events
        event_count = 0
        if self.log_path.exists():
            with open(self.log_path) as f:
                event_count = sum(1 for _ in f)
        
        return f"evt_{event_count + 1:06d}"
    
    def _compute_hash(self, event: dict[str, Any]) -> str:
        """Compute SHA-256 hash of event content (excluding the hash field itself)."""
        # Create a copy without the hash field
        event_copy = {k: v for k, v in event.items() if k != 'hash'}
        
        # Sort keys for deterministic hashing
        event_json = json.dumps(event_copy, sort_keys=True)
        hash_digest = hashlib.sha256(event_json.encode()).hexdigest()
        
        return f"sha256:{hash_digest}"
    
    def log_event(
        self,
        event_type: str,
        actor: str,
        task_id: str | None = None,
        summary: str | None = None,
        artifacts: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Log a new event to the event log.
        
        Args:
            event_type: Type of event (e.g., IntentDeclared, BriefCreated, etc.)
            actor: Agent, tool, or human who triggered the event
            task_id: Associated task ID (optional)
            summary: Human-readable summary (optional)
            artifacts: List of artifact paths (optional)
            metadata: Additional event-specific metadata (optional)
        
        Returns:
            The logged event as a dictionary
        """
        event: dict[str, Any] = {
            "event_id": self._generate_event_id(),
            "timestamp": datetime.now(UTC).isoformat(),
            "event_type": event_type,
            "actor": actor,
        }
        
        if task_id:
            event["task_id"] = task_id
        if summary:
            event["summary"] = summary
        if artifacts:
            event["artifacts"] = artifacts
        if metadata:
            event["metadata"] = metadata
        
        # Add previous event hash for chain integrity
        if self._last_event_hash:
            event["previous_event_hash"] = self._last_event_hash
        
        # Compute and add hash
        event["hash"] = self._compute_hash(event)
        
        # Write to log
        with open(self.log_path, 'a') as f:
            f.write(json.dumps(event) + '\n')
        
        # Update last hash
        self._last_event_hash = event["hash"]
        
        return event
    
    def get_events(
        self,
        task_id: str | None = None,
        event_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve events from the log.
        
        Args:
            task_id: Filter by task ID (optional)
            event_type: Filter by event type (optional)
        
        Returns:
            List of events matching the criteria
        """
        if not self.log_path.exists():
            return []
        
        events = []
        with open(self.log_path) as f:
            for line in f:
                try:
                    event = json.loads(line)
                    
                    # Apply filters
                    if task_id and event.get('task_id') != task_id:
                        continue
                    if event_type and event.get('event_type') != event_type:
                        continue
                    
                    events.append(event)
                except json.JSONDecodeError:
                    continue
        
        return events
    
    def verify_chain(self) -> tuple[bool, list[str]]:
        """Verify the integrity of the event chain.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        if not self.log_path.exists():
            return True, []
        
        errors = []
        previous_hash = None
        
        with open(self.log_path) as f:
            for i, line in enumerate(f, 1):
                try:
                    event = json.loads(line)
                    
                    # Verify hash
                    claimed_hash = event.get('hash')
                    if claimed_hash:
                        computed_hash = self._compute_hash(event)
                        if claimed_hash != computed_hash:
                            errors.append(
                                f"Event {i} ({event.get('event_id')}): "
                                f"Hash mismatch (claimed: {claimed_hash}, computed: {computed_hash})"
                            )
                    
                    # Verify chain linkage
                    if previous_hash:
                        claimed_previous = event.get('previous_event_hash')
                        if claimed_previous != previous_hash:
                            errors.append(
                                f"Event {i} ({event.get('event_id')}): "
                                f"Chain break (expected previous: {previous_hash}, "
                                f"claimed: {claimed_previous})"
                            )
                    
                    previous_hash = claimed_hash
                    
                except json.JSONDecodeError:
                    errors.append(f"Event {i}: Invalid JSON")
        
        return len(errors) == 0, errors


class TaskState:
    """Manages task state information."""
    
    def __init__(self, state_path: Path | None = None):
        """Initialize task state manager.
        
        Args:
            state_path: Path to tasks.json file. Defaults to .agentic-agile-v/state/tasks.json
        """
        if state_path is None:
            state_path = Path.cwd() / ".agentic-agile-v" / "state" / "tasks.json"
        
        self.state_path = state_path
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize empty state if file doesn't exist
        if not self.state_path.exists():
            self._save_state({"tasks": {}})
    
    def _load_state(self) -> dict[str, Any]:
        """Load the current state."""
        with open(self.state_path) as f:
            return json.load(f)
    
    def _save_state(self, state: dict[str, Any]) -> None:
        """Save the state."""
        with open(self.state_path, 'w') as f:
            json.dump(state, f, indent=2)
    
    def create_task(self, task_id: str, title: str, risk_level: str) -> None:
        """Create a new task in the state."""
        state = self._load_state()
        
        state["tasks"][task_id] = {
            "task_id": task_id,
            "title": title,
            "risk_level": risk_level,
            "status": "created",
            "created_at": datetime.now(UTC).isoformat(),
        }
        
        self._save_state(state)
    
    def update_task_status(self, task_id: str, status: str) -> None:
        """Update task status."""
        state = self._load_state()
        
        if task_id in state["tasks"]:
            state["tasks"][task_id]["status"] = status
            state["tasks"][task_id]["updated_at"] = datetime.now(UTC).isoformat()
            self._save_state(state)
    
    def get_task(self, task_id: str) -> dict[str, Any] | None:
        """Get task information."""
        state = self._load_state()
        return state["tasks"].get(task_id)
    
    def list_tasks(self, status: str | None = None) -> list[dict[str, Any]]:
        """List all tasks, optionally filtered by status."""
        state = self._load_state()
        tasks = list(state["tasks"].values())
        
        if status:
            tasks = [t for t in tasks if t.get("status") == status]
        
        return tasks


class LockManager:
    """Manages file and resource locks for multi-agent coordination."""
    
    def __init__(self, locks_path: Path | None = None):
        """Initialize lock manager.
        
        Args:
            locks_path: Path to locks.json file. Defaults to .agentic-agile-v/state/locks.json
        """
        if locks_path is None:
            locks_path = Path.cwd() / ".agentic-agile-v" / "state" / "locks.json"
        
        self.locks_path = locks_path
        self.locks_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize empty locks if file doesn't exist
        if not self.locks_path.exists():
            self._save_locks({"locks": []})
    
    def _load_locks(self) -> dict[str, Any]:
        """Load current locks."""
        with open(self.locks_path) as f:
            return json.load(f)
    
    def _save_locks(self, locks: dict[str, Any]) -> None:
        """Save locks."""
        with open(self.locks_path, 'w') as f:
            json.dump(locks, f, indent=2)
    
    def acquire_lock(
        self,
        task_id: str,
        actor: str,
        files: list[str],
        intent: str,
        ttl_hours: int = 2,
    ) -> bool:
        """Attempt to acquire a lock on files.
        
        Args:
            task_id: Task ID
            actor: Actor requesting the lock
            files: List of file paths to lock
            intent: Description of intended changes
            ttl_hours: Time to live in hours (default: 2)
        
        Returns:
            True if lock was acquired, False if conflicting lock exists
        """
        locks_data = self._load_locks()
        
        # Check for conflicts
        for lock in locks_data["locks"]:
            # Check if lock is expired
            expires_at = datetime.fromisoformat(lock["expires_at"].replace('Z', '+00:00'))
            if expires_at < datetime.now(UTC):
                continue
            
            # Check for file conflicts
            lock_files = set(lock["files"])
            requested_files = set(files)
            
            if lock_files & requested_files:  # Intersection
                return False
        
        # No conflicts, create lock
        created_at = datetime.now(UTC)
        expires_at = created_at.replace(hour=created_at.hour + ttl_hours)
        
        new_lock = {
            "task_id": task_id,
            "actor": actor,
            "intent": intent,
            "files": files,
            "created_at": created_at.isoformat(),
            "expires_at": expires_at.isoformat(),
        }
        
        locks_data["locks"].append(new_lock)
        self._save_locks(locks_data)
        
        return True
    
    def release_lock(self, task_id: str, actor: str) -> None:
        """Release locks held by an actor for a task."""
        locks_data = self._load_locks()
        
        locks_data["locks"] = [
            lock for lock in locks_data["locks"]
            if not (lock["task_id"] == task_id and lock["actor"] == actor)
        ]
        
        self._save_locks(locks_data)
    
    def get_active_locks(self) -> list[dict[str, Any]]:
        """Get all active (non-expired) locks."""
        locks_data = self._load_locks()
        now = datetime.now(UTC)
        
        active_locks = []
        for lock in locks_data["locks"]:
            expires_at = datetime.fromisoformat(lock["expires_at"].replace('Z', '+00:00'))
            if expires_at >= now:
                active_locks.append(lock)
        
        return active_locks
    
    def clean_expired_locks(self) -> int:
        """Remove expired locks and return count of removed locks."""
        locks_data = self._load_locks()
        now = datetime.now(UTC)
        
        initial_count = len(locks_data["locks"])
        
        locks_data["locks"] = [
            lock for lock in locks_data["locks"]
            if datetime.fromisoformat(lock["expires_at"].replace('Z', '+00:00')) >= now
        ]
        
        final_count = len(locks_data["locks"])
        self._save_locks(locks_data)
        
        return initial_count - final_count
