"""
Event Ledger with Cryptographic Hash Chain

Provides a tamper-proof audit trail for OpenHands sessions and Agile-V events.

Features:
- Append-only event log
- Cryptographic hash chain linking events
- Verification of event integrity
- Merkle tree summaries for efficient verification
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class EventType(Enum):
    """Types of events that can be logged."""
    SESSION_STARTED = "session_started"
    SESSION_COMPLETED = "session_completed"
    TOOL_INVOKED = "tool_invoked"
    SCOPE_VIOLATION = "scope_violation"
    EVIDENCE_COLLECTED = "evidence_collected"
    VERIFICATION_RESULT = "verification_result"
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    HANDOFF_GENERATED = "handoff_generated"


@dataclass
class Event:
    """A single event in the ledger."""
    # Event metadata
    event_id: str
    event_type: EventType
    timestamp: datetime
    
    # Actor information
    actor: str  # e.g., "openhands", "human:john", "ci:github-actions"
    actor_session_id: str | None = None
    
    # Event data
    task_id: str | None = None
    summary: str = ""
    details: dict[str, Any] = None
    
    # Hash chain
    previous_hash: str | None = None
    event_hash: str | None = None
    
    def __post_init__(self):
        """Initialize fields after dataclass construction."""
        if self.details is None:
            self.details = {}
        
        # Compute event hash if not provided
        if self.event_hash is None:
            self.event_hash = self.compute_hash()
    
    def compute_hash(self) -> str:
        """
        Compute cryptographic hash of this event.
        
        Hash includes:
        - Event ID
        - Event type
        - Timestamp
        - Actor
        - Task ID
        - Summary
        - Details (JSON)
        - Previous hash (creating chain)
        """
        hasher = hashlib.sha256()
        
        # Add fields in deterministic order
        hasher.update(self.event_id.encode('utf-8'))
        hasher.update(self.event_type.value.encode('utf-8'))
        hasher.update(self.timestamp.isoformat().encode('utf-8'))
        hasher.update(self.actor.encode('utf-8'))
        
        if self.task_id:
            hasher.update(self.task_id.encode('utf-8'))
        
        hasher.update(self.summary.encode('utf-8'))
        
        # Canonicalize details JSON
        details_json = json.dumps(self.details, sort_keys=True)
        hasher.update(details_json.encode('utf-8'))
        
        # Include previous hash to create chain
        if self.previous_hash:
            hasher.update(self.previous_hash.encode('utf-8'))
        
        return f"sha256:{hasher.hexdigest()}"
    
    def verify_hash(self) -> bool:
        """Verify that the stored hash matches computed hash."""
        computed = self.compute_hash()
        return computed == self.event_hash
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'timestamp': self.timestamp.isoformat(),
            'actor': self.actor,
            'actor_session_id': self.actor_session_id,
            'task_id': self.task_id,
            'summary': self.summary,
            'details': self.details,
            'previous_hash': self.previous_hash,
            'event_hash': self.event_hash
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'Event':
        """Create event from dictionary."""
        return cls(
            event_id=data['event_id'],
            event_type=EventType(data['event_type']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            actor=data['actor'],
            actor_session_id=data.get('actor_session_id'),
            task_id=data.get('task_id'),
            summary=data.get('summary', ''),
            details=data.get('details', {}),
            previous_hash=data.get('previous_hash'),
            event_hash=data.get('event_hash')
        )


class EventLedger:
    """
    Append-only event ledger with cryptographic hash chain.
    
    Events are stored in a JSONL file with each event linking to the
    previous event via cryptographic hash, creating a tamper-evident chain.
    """
    
    def __init__(self, ledger_file: Path):
        """
        Initialize ledger.
        
        Args:
            ledger_file: Path to JSONL ledger file
        """
        self.ledger_file = ledger_file
        self.ledger_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Touch file if it doesn't exist
        if not self.ledger_file.exists():
            self.ledger_file.touch()
    
    def append_event(
        self,
        event_type: EventType,
        actor: str,
        summary: str,
        task_id: str | None = None,
        details: dict[str, Any] | None = None,
        actor_session_id: str | None = None
    ) -> Event:
        """
        Append a new event to the ledger.
        
        Args:
            event_type: Type of event
            actor: Who performed the action
            summary: Brief description
            task_id: Associated task ID (optional)
            details: Additional details (optional)
            actor_session_id: Session ID if actor is OpenHands (optional)
            
        Returns:
            The created event
        """
        # Get previous hash
        previous_hash = self._get_last_hash()
        
        # Generate event ID
        event_count = self._count_events()
        event_id = f"EVT-{event_count + 1:08d}"
        
        # Create event
        event = Event(
            event_id=event_id,
            event_type=event_type,
            timestamp=datetime.now(),
            actor=actor,
            actor_session_id=actor_session_id,
            task_id=task_id,
            summary=summary,
            details=details or {},
            previous_hash=previous_hash
        )
        
        # Append to file
        with open(self.ledger_file, 'a') as f:
            f.write(json.dumps(event.to_dict()) + '\n')
        
        return event
    
    def get_events(
        self,
        task_id: str | None = None,
        event_type: EventType | None = None,
        actor: str | None = None,
        since: datetime | None = None
    ) -> list[Event]:
        """
        Get events from the ledger.
        
        Args:
            task_id: Filter by task ID (optional)
            event_type: Filter by event type (optional)
            actor: Filter by actor (optional)
            since: Only events after this time (optional)
            
        Returns:
            List of matching events
        """
        if not self.ledger_file.exists():
            return []
        
        events = []
        with open(self.ledger_file) as f:
            for line in f:
                if not line.strip():
                    continue
                
                data = json.loads(line)
                event = Event.from_dict(data)
                
                # Apply filters
                if task_id and event.task_id != task_id:
                    continue
                
                if event_type and event.event_type != event_type:
                    continue
                
                if actor and event.actor != actor:
                    continue
                
                if since and event.timestamp < since:
                    continue
                
                events.append(event)
        
        return events
    
    def verify_chain(self) -> tuple[bool, list[str]]:
        """
        Verify the integrity of the entire hash chain.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        if not self.ledger_file.exists():
            return True, []
        
        errors = []
        previous_hash = None
        
        with open(self.ledger_file) as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                
                try:
                    data = json.loads(line)
                    event = Event.from_dict(data)
                    
                    # Verify hash computation
                    if not event.verify_hash():
                        errors.append(f"Event {event.event_id} (line {line_num}): Hash mismatch")
                    
                    # Verify chain link
                    if event.previous_hash != previous_hash:
                        errors.append(
                            f"Event {event.event_id} (line {line_num}): "
                            f"Chain broken. Expected previous_hash={previous_hash}, "
                            f"got {event.previous_hash}"
                        )
                    
                    previous_hash = event.event_hash
                    
                except Exception as e:
                    errors.append(f"Line {line_num}: Failed to parse/verify: {e}")
        
        return len(errors) == 0, errors
    
    def get_chain_summary(self) -> dict[str, Any]:
        """
        Get summary of the event chain.
        
        Returns:
            Summary with event count, date range, head hash, etc.
        """
        events = self.get_events()
        
        if not events:
            return {
                'event_count': 0,
                'head_hash': None,
                'tail_hash': None,
                'first_event': None,
                'last_event': None
            }
        
        return {
            'event_count': len(events),
            'head_hash': events[0].event_hash if events else None,
            'tail_hash': events[-1].event_hash if events else None,
            'first_event': {
                'id': events[0].event_id,
                'timestamp': events[0].timestamp.isoformat(),
                'type': events[0].event_type.value
            },
            'last_event': {
                'id': events[-1].event_id,
                'timestamp': events[-1].timestamp.isoformat(),
                'type': events[-1].event_type.value
            }
        }
    
    def export_task_timeline(self, task_id: str) -> list[dict[str, Any]]:
        """
        Export timeline of events for a specific task.
        
        Args:
            task_id: Task ID
            
        Returns:
            List of events in chronological order
        """
        events = self.get_events(task_id=task_id)
        return [e.to_dict() for e in events]
    
    def _get_last_hash(self) -> str | None:
        """Get hash of the last event in the chain."""
        if not self.ledger_file.exists():
            return None
        
        last_hash = None
        with open(self.ledger_file) as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    last_hash = data.get('event_hash')
        
        return last_hash
    
    def _count_events(self) -> int:
        """Count events in the ledger."""
        if not self.ledger_file.exists():
            return 0
        
        count = 0
        with open(self.ledger_file) as f:
            for line in f:
                if line.strip():
                    count += 1
        
        return count


def create_session_events(
    ledger: EventLedger,
    session_id: str,
    task_id: str,
    start_time: datetime,
    end_time: datetime,
    status: str,
    iterations: int,
    tool_calls: int,
    files_modified: list[str]
) -> None:
    """
    Create events for an OpenHands session.
    
    Args:
        ledger: Event ledger
        session_id: OpenHands session ID
        task_id: Task ID
        start_time: Session start time
        end_time: Session end time
        status: Final status
        iterations: Number of iterations
        tool_calls: Number of tool calls
        files_modified: List of modified files
    """
    # Session started event
    ledger.append_event(
        event_type=EventType.SESSION_STARTED,
        actor="openhands",
        actor_session_id=session_id,
        task_id=task_id,
        summary=f"OpenHands session {session_id} started for task {task_id}",
        details={'start_time': start_time.isoformat()}
    )
    
    # Session completed event
    ledger.append_event(
        event_type=EventType.SESSION_COMPLETED,
        actor="openhands",
        actor_session_id=session_id,
        task_id=task_id,
        summary=f"OpenHands session {session_id} completed with status: {status}",
        details={
            'end_time': end_time.isoformat(),
            'duration_seconds': (end_time - start_time).total_seconds(),
            'status': status,
            'iterations': iterations,
            'tool_calls': tool_calls,
            'files_modified': files_modified,
            'files_modified_count': len(files_modified)
        }
    )
