"""
OpenHands Session Manager

Manages OpenHands agent sessions, including:
- Starting and stopping sessions
- Monitoring session progress
- Collecting session outputs
- Managing builder/verifier workflow

This module provides the core infrastructure for automatic OpenHands execution.
"""

import json
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..task_context import TaskContextResolver
from .event_ledger import EventLedger, EventType, create_session_events


class SessionState(Enum):
    """Possible states of an OpenHands session."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentRole(Enum):
    """Agent roles in the builder/verifier pattern."""
    BUILDER = "builder"
    VERIFIER = "verifier"
    STANDALONE = "standalone"


@dataclass
class SessionConfig:
    """Configuration for an OpenHands session."""
    task_id: str
    role: AgentRole
    workspace_dir: Path
    max_iterations: int = 50
    timeout_seconds: int = 3600
    model: str = "gpt-4"
    temperature: float = 0.0
    
    # Builder/verifier specific
    verify_previous_session: Optional[str] = None  # Session ID to verify
    

@dataclass
class SessionMetadata:
    """Metadata about an OpenHands session."""
    session_id: str
    task_id: str
    role: AgentRole
    state: SessionState
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    exit_code: Optional[int] = None
    error_message: Optional[str] = None
    
    # Metrics
    iterations: int = 0
    tool_calls: int = 0
    files_modified: int = 0
    
    # Results
    output_file: Optional[Path] = None
    log_file: Optional[Path] = None
    

class OpenHandsSessionManager:
    """
    Manages OpenHands agent sessions.
    
    Responsibilities:
    - Launch OpenHands processes
    - Monitor execution
    - Collect outputs and logs
    - Manage session lifecycle
    - Coordinate builder/verifier workflow
    """
    
    def __init__(self, workspace_dir: Path, agilev_dir: Path):
        """
        Initialize the session manager.
        
        Args:
            workspace_dir: Root directory of the workspace
            agilev_dir: .agentic-agile-v directory
        """
        self.workspace_dir = workspace_dir
        self.agilev_dir = agilev_dir
        self.sessions_dir = agilev_dir / "openhands" / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        
        # Session registry
        self.registry_file = self.sessions_dir / "registry.jsonl"
        
        # Event ledger
        ledger_file = agilev_dir / "openhands" / "events.jsonl"
        self.ledger = EventLedger(ledger_file)
        
    def create_session(self, config: SessionConfig) -> str:
        """
        Create a new session.
        
        Args:
            config: Session configuration
            
        Returns:
            Session ID
        """
        # Generate session ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"{config.task_id}_{config.role.value}_{timestamp}"
        
        # Create session directory
        session_dir = self.sessions_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize metadata
        metadata = SessionMetadata(
            session_id=session_id,
            task_id=config.task_id,
            role=config.role,
            state=SessionState.PENDING,
            created_at=datetime.now(),
            log_file=session_dir / "session.log",
            output_file=session_dir / "output.json"
        )
        
        # Save metadata
        self._save_metadata(metadata)
        
        # Save config
        config_file = session_dir / "config.json"
        with open(config_file, 'w') as f:
            json.dump({
                'task_id': config.task_id,
                'role': config.role.value,
                'workspace_dir': str(config.workspace_dir),
                'max_iterations': config.max_iterations,
                'timeout_seconds': config.timeout_seconds,
                'model': config.model,
                'temperature': config.temperature,
                'verify_previous_session': config.verify_previous_session
            }, f, indent=2)
        
        return session_id
    
    def start_session(self, session_id: str, prompt: str) -> None:
        """
        Start an OpenHands session.
        
        Args:
            session_id: Session to start
            prompt: Initial prompt for the agent
        """
        metadata = self._load_metadata(session_id)
        if metadata.state != SessionState.PENDING:
            raise ValueError(f"Session {session_id} is not in PENDING state")
        
        # Update state
        metadata.state = SessionState.RUNNING
        metadata.started_at = datetime.now()
        self._save_metadata(metadata)
        
        # Log session start event
        self.ledger.append_event(
            event_type=EventType.SESSION_STARTED,
            actor="openhands",
            actor_session_id=session_id,
            task_id=metadata.task_id,
            summary=f"Started {metadata.role.value} session for task {metadata.task_id}",
            details={'prompt': prompt[:200]}  # Truncate long prompts
        )
        
        # Load config
        session_dir = self.sessions_dir / session_id
        config_file = session_dir / "config.json"
        with open(config_file) as f:
            config = json.load(f)
        
        # Prepare environment
        env = {
            'AGILEV_TASK_ID': config['task_id'],
            'AGILEV_SESSION_ID': session_id,
            'AGILEV_AGENT_ROLE': config['role']
        }
        
        # Write prompt to file
        prompt_file = session_dir / "prompt.txt"
        prompt_file.write_text(prompt)
        
        # Build OpenHands command
        # This is a placeholder - actual command depends on OpenHands installation
        cmd = self._build_openhands_command(config, prompt_file, session_dir)
        
        # Start process
        log_file = session_dir / "session.log"
        with open(log_file, 'w') as log:
            try:
                # Run OpenHands (this is blocking for now)
                result = subprocess.run(
                    cmd,
                    cwd=self.workspace_dir,
                    env=env,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    timeout=config['timeout_seconds']
                )
                
                # Update metadata
                metadata.state = SessionState.COMPLETED if result.returncode == 0 else SessionState.FAILED
                metadata.exit_code = result.returncode
                metadata.completed_at = datetime.now()
                
            except subprocess.TimeoutExpired:
                metadata.state = SessionState.FAILED
                metadata.error_message = "Session timed out"
                metadata.completed_at = datetime.now()
                
            except Exception as e:
                metadata.state = SessionState.FAILED
                metadata.error_message = str(e)
                metadata.completed_at = datetime.now()
        
        # Collect metrics
        metadata.iterations = self._count_iterations(log_file)
        metadata.tool_calls = self._count_tool_calls(log_file)
        metadata.files_modified = self._count_modified_files(session_dir)
        
        # Save final metadata
        self._save_metadata(metadata)
        
        # Log session completion event
        self.ledger.append_event(
            event_type=EventType.SESSION_COMPLETED,
            actor="openhands",
            actor_session_id=session_id,
            task_id=metadata.task_id,
            summary=f"Completed {metadata.role.value} session with status: {metadata.state.value}",
            details={
                'exit_code': metadata.exit_code,
                'iterations': metadata.iterations,
                'tool_calls': metadata.tool_calls,
                'files_modified': metadata.files_modified,
                'duration_seconds': (metadata.completed_at - metadata.started_at).total_seconds() if metadata.started_at and metadata.completed_at else 0
            }
        )
    
    def get_session(self, session_id: str) -> SessionMetadata:
        """Get session metadata."""
        return self._load_metadata(session_id)
    
    def list_sessions(self, task_id: Optional[str] = None) -> List[SessionMetadata]:
        """
        List sessions.
        
        Args:
            task_id: Filter by task ID (optional)
            
        Returns:
            List of session metadata
        """
        if not self.registry_file.exists():
            return []
        
        sessions = []
        with open(self.registry_file) as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    metadata = self._parse_metadata(data)
                    if task_id is None or metadata.task_id == task_id:
                        sessions.append(metadata)
        
        return sorted(sessions, key=lambda s: s.created_at, reverse=True)
    
    def cancel_session(self, session_id: str) -> None:
        """Cancel a running session."""
        metadata = self._load_metadata(session_id)
        if metadata.state == SessionState.RUNNING:
            # TODO: Kill process
            metadata.state = SessionState.CANCELLED
            metadata.completed_at = datetime.now()
            self._save_metadata(metadata)
    
    def _build_openhands_command(
        self, 
        config: Dict[str, Any], 
        prompt_file: Path,
        session_dir: Path
    ) -> List[str]:
        """
        Build the OpenHands command.
        
        This is a placeholder that builds a command based on common
        OpenHands deployment methods. In practice, this may need to be
        configured based on how OpenHands is installed.
        """
        # Check for Docker installation
        docker_check = subprocess.run(
            ['docker', 'images', '-q', 'ghcr.io/all-hands-ai/openhands'],
            capture_output=True,
            text=True
        )
        
        if docker_check.stdout.strip():
            # Docker installation found
            return [
                'docker', 'run', '--rm',
                '-v', f'{self.workspace_dir}:/workspace',
                '-v', f'{session_dir}:/session',
                '-e', f'AGILEV_TASK_ID={config["task_id"]}',
                '-e', f'AGILEV_AGENT_ROLE={config["role"]}',
                'ghcr.io/all-hands-ai/openhands:latest',
                '--directory', '/workspace',
                '--prompt-file', '/session/prompt.txt',
                '--max-iterations', str(config['max_iterations']),
                '--model', config['model']
            ]
        else:
            # Assume local installation
            return [
                'openhands',
                '--directory', str(self.workspace_dir),
                '--prompt-file', str(prompt_file),
                '--max-iterations', str(config['max_iterations']),
                '--model', config['model']
            ]
    
    def _save_metadata(self, metadata: SessionMetadata) -> None:
        """Save session metadata to registry."""
        data = {
            'session_id': metadata.session_id,
            'task_id': metadata.task_id,
            'role': metadata.role.value,
            'state': metadata.state.value,
            'created_at': metadata.created_at.isoformat(),
            'started_at': metadata.started_at.isoformat() if metadata.started_at else None,
            'completed_at': metadata.completed_at.isoformat() if metadata.completed_at else None,
            'exit_code': metadata.exit_code,
            'error_message': metadata.error_message,
            'iterations': metadata.iterations,
            'tool_calls': metadata.tool_calls,
            'files_modified': metadata.files_modified,
            'output_file': str(metadata.output_file) if metadata.output_file else None,
            'log_file': str(metadata.log_file) if metadata.log_file else None
        }
        
        # Append to registry
        with open(self.registry_file, 'a') as f:
            f.write(json.dumps(data) + '\n')
    
    def _load_metadata(self, session_id: str) -> SessionMetadata:
        """Load session metadata from registry."""
        if not self.registry_file.exists():
            raise ValueError(f"Session {session_id} not found")
        
        with open(self.registry_file) as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    if data['session_id'] == session_id:
                        return self._parse_metadata(data)
        
        raise ValueError(f"Session {session_id} not found")
    
    def _parse_metadata(self, data: Dict[str, Any]) -> SessionMetadata:
        """Parse metadata from JSON."""
        return SessionMetadata(
            session_id=data['session_id'],
            task_id=data['task_id'],
            role=AgentRole(data['role']),
            state=SessionState(data['state']),
            created_at=datetime.fromisoformat(data['created_at']),
            started_at=datetime.fromisoformat(data['started_at']) if data.get('started_at') else None,
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None,
            exit_code=data.get('exit_code'),
            error_message=data.get('error_message'),
            iterations=data.get('iterations', 0),
            tool_calls=data.get('tool_calls', 0),
            files_modified=data.get('files_modified', 0),
            output_file=Path(data['output_file']) if data.get('output_file') else None,
            log_file=Path(data['log_file']) if data.get('log_file') else None
        )
    
    def _count_iterations(self, log_file: Path) -> int:
        """Count iterations from log file."""
        if not log_file.exists():
            return 0
        
        content = log_file.read_text()
        # Look for iteration markers (this depends on OpenHands output format)
        import re
        matches = re.findall(r'Iteration (\d+)', content)
        return len(matches)
    
    def _count_tool_calls(self, log_file: Path) -> int:
        """Count tool calls from log file."""
        if not log_file.exists():
            return 0
        
        content = log_file.read_text()
        # Look for tool call markers
        import re
        matches = re.findall(r'Tool: \w+', content)
        return len(matches)
    
    def _count_modified_files(self, session_dir: Path) -> int:
        """Count modified files."""
        # This would ideally parse the session output
        # For now, return 0 as placeholder
        return 0


class BuilderVerifierWorkflow:
    """
    Implements the builder/verifier pattern.
    
    Workflow:
    1. Builder agent implements changes
    2. Verifier agent reviews changes
    3. If verifier approves, done
    4. If verifier rejects, builder iterates
    5. Maximum 3 builder-verifier cycles
    """
    
    def __init__(self, session_manager: OpenHandsSessionManager):
        """Initialize workflow."""
        self.session_manager = session_manager
        self.max_cycles = 3
    
    def run(self, task_id: str, implementation_prompt: str) -> Dict[str, Any]:
        """
        Run the builder/verifier workflow.
        
        Args:
            task_id: Task ID
            implementation_prompt: What to implement
            
        Returns:
            Workflow results including all sessions
        """
        results = {
            'task_id': task_id,
            'cycles': [],
            'final_state': None,
            'approved': False
        }
        
        for cycle in range(self.max_cycles):
            print(f"\n=== Cycle {cycle + 1}/{self.max_cycles} ===\n")
            
            cycle_results = {'cycle': cycle + 1, 'builder': None, 'verifier': None}
            
            # Step 1: Builder implements
            print("Starting builder agent...")
            builder_config = SessionConfig(
                task_id=task_id,
                role=AgentRole.BUILDER,
                workspace_dir=self.session_manager.workspace_dir
            )
            builder_session_id = self.session_manager.create_session(builder_config)
            
            builder_prompt = self._build_builder_prompt(
                task_id, 
                implementation_prompt,
                cycle,
                results['cycles'][-1]['verifier'] if cycle > 0 else None
            )
            
            self.session_manager.start_session(builder_session_id, builder_prompt)
            builder_metadata = self.session_manager.get_session(builder_session_id)
            cycle_results['builder'] = builder_session_id
            
            if builder_metadata.state == SessionState.FAILED:
                print(f"Builder failed: {builder_metadata.error_message}")
                results['final_state'] = 'builder_failed'
                results['cycles'].append(cycle_results)
                break
            
            print(f"Builder completed ({builder_metadata.iterations} iterations)")
            
            # Step 2: Verifier reviews
            print("Starting verifier agent...")
            verifier_config = SessionConfig(
                task_id=task_id,
                role=AgentRole.VERIFIER,
                workspace_dir=self.session_manager.workspace_dir,
                verify_previous_session=builder_session_id
            )
            verifier_session_id = self.session_manager.create_session(verifier_config)
            
            verifier_prompt = self._build_verifier_prompt(task_id, builder_session_id)
            
            self.session_manager.start_session(verifier_session_id, verifier_prompt)
            verifier_metadata = self.session_manager.get_session(verifier_session_id)
            cycle_results['verifier'] = verifier_session_id
            
            if verifier_metadata.state == SessionState.FAILED:
                print(f"Verifier failed: {verifier_metadata.error_message}")
                results['final_state'] = 'verifier_failed'
                results['cycles'].append(cycle_results)
                break
            
            print(f"Verifier completed ({verifier_metadata.iterations} iterations)")
            
            # Step 3: Check if approved
            approved = self._check_verification_result(verifier_session_id)
            cycle_results['approved'] = approved
            results['cycles'].append(cycle_results)
            
            if approved:
                print("✅ Changes approved by verifier!")
                results['final_state'] = 'approved'
                results['approved'] = True
                break
            else:
                print("❌ Changes rejected by verifier, starting next cycle...")
        
        if not results['approved'] and results['final_state'] is None:
            results['final_state'] = 'max_cycles_reached'
            print(f"\n⚠️  Maximum cycles ({self.max_cycles}) reached without approval")
        
        return results
    
    def _build_builder_prompt(
        self,
        task_id: str,
        implementation_prompt: str,
        cycle: int,
        previous_verifier_session: Optional[str]
    ) -> str:
        """Build the prompt for the builder agent."""
        prompt = f"""You are the BUILDER agent for Agile-V task {task_id}.

Your role: Implement the requested changes according to the task brief.

Task: {implementation_prompt}

Instructions:
1. Read the task brief at .agentic-agile-v/tasks/{task_id}/task_brief.md
2. Respect the scope constraints (allowed_paths, blocked_paths)
3. Implement the changes according to requirements
4. Run tests to verify your changes work
5. Ensure code quality (linting, type checking)

"""
        
        if cycle > 0 and previous_verifier_session:
            prompt += f"""
This is iteration {cycle + 1}. The verifier rejected your previous implementation.

Review the verifier's feedback in the previous session and address all issues.
"""
        
        prompt += """
When done, summarize:
- What you implemented
- What tests you ran
- What files you changed
- Any concerns or limitations

Remember: You cannot approve your own work. The verifier will review your changes.
"""
        
        return prompt
    
    def _build_verifier_prompt(self, task_id: str, builder_session_id: str) -> str:
        """Build the prompt for the verifier agent."""
        return f"""You are the VERIFIER agent for Agile-V task {task_id}.

Your role: Review the builder's implementation and verify it meets requirements.

The builder session ID is: {builder_session_id}

Instructions:
1. Read the task brief at .agentic-agile-v/tasks/{task_id}/task_brief.md
2. Review the changes made by the builder (use git diff)
3. Verify scope compliance (no changes to blocked paths)
4. Run all tests to ensure they pass
5. Check code quality (linting, type checking)
6. Verify the implementation matches requirements

Verification checklist:
- [ ] Task brief requirements met
- [ ] Scope constraints respected
- [ ] All tests pass
- [ ] No new linting/type errors
- [ ] Code is maintainable and clear
- [ ] No security issues introduced
- [ ] Documentation updated if needed

Decision:
At the end, you must make a decision:

APPROVE: If all checks pass and implementation is satisfactory
REJECT: If there are issues that need to be fixed

Format your final decision as:
DECISION: APPROVE
or
DECISION: REJECT
Reason: <detailed explanation>

Remember: You are protecting code quality. Be thorough but fair.
"""
    
    def _check_verification_result(self, verifier_session_id: str) -> bool:
        """
        Check if verifier approved the changes.
        
        Looks for "DECISION: APPROVE" in the verifier's output.
        """
        session_dir = self.session_manager.sessions_dir / verifier_session_id
        log_file = session_dir / "session.log"
        
        if not log_file.exists():
            return False
        
        content = log_file.read_text()
        return 'DECISION: APPROVE' in content
