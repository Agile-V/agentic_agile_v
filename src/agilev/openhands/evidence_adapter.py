"""Evidence adapter for OpenHands sessions.

Collects evidence from OpenHands tool logs, session metadata, Git history,
and CI results, and updates the evidence bundle.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


class EvidenceAdapter:
    """Adapts OpenHands session data into Agile-V evidence bundles."""
    
    def __init__(self, repo_root: Path | None = None):
        """Initialize evidence adapter.
        
        Args:
            repo_root: Repository root directory (defaults to current directory)
        """
        self.repo_root = repo_root or Path.cwd()
    
    def collect_evidence(self, task_id: str) -> dict[str, Any]:
        """Collect evidence from OpenHands session and other sources.
        
        Args:
            task_id: Task ID (e.g., AAV-0001)
            
        Returns:
            Evidence data to merge into evidence bundle
            
        Raises:
            FileNotFoundError: If task directory doesn't exist
        """
        task_dir = self.repo_root / ".agentic-agile-v/tasks" / task_id
        
        if not task_dir.exists():
            raise FileNotFoundError(f"Task directory not found: {task_dir}")
        
        evidence = {}
        
        # Collect OpenHands session metadata
        session_data = self._collect_session_metadata(task_dir)
        if session_data:
            evidence["agent_execution"] = session_data
        
        # Collect changed files from Git (source of truth)
        changed_files = self._collect_changed_files()
        if changed_files:
            evidence["changed_files"] = changed_files
        
        # Collect scope control data
        scope_data = self._collect_scope_data(task_dir, changed_files)
        if scope_data:
            evidence["scope_control"] = scope_data
        
        # Collect test results from tool log
        test_results = self._collect_test_results(task_dir)
        if test_results:
            evidence["tests"] = test_results
        
        # Collect check results from tool log
        check_results = self._collect_check_results(task_dir)
        if check_results:
            evidence["checks"] = check_results
        
        return evidence
    
    def _collect_session_metadata(self, task_dir: Path) -> dict[str, Any] | None:
        """Collect OpenHands session metadata.
        
        Args:
            task_dir: Task directory path
            
        Returns:
            Session metadata dict or None if not found
        """
        session_file = task_dir / "logs/openhands_session.json"
        
        if not session_file.exists():
            return None
        
        try:
            with open(session_file) as f:
                session_data = json.load(f)
            
            # Extract relevant fields
            metadata = {
                "engine": session_data.get("engine", "openhands"),
                "mode": session_data.get("mode", "builder"),
                "session_id": session_data.get("session_id", "unknown"),
            }
            
            if "agent_model" in session_data:
                metadata["agent_model"] = session_data["agent_model"]
            
            if "started_at" in session_data:
                metadata["started_at"] = session_data["started_at"]
            
            if "ended_at" in session_data:
                metadata["ended_at"] = session_data["ended_at"]
            
            # Add relative paths
            tool_log = task_dir / "logs/openhands_tool_log.jsonl"
            if tool_log.exists():
                metadata["tool_log_path"] = str(tool_log.relative_to(self.repo_root))
            
            handoff = task_dir / "openhands_handoff.md"
            if handoff.exists():
                metadata["handoff_path"] = str(handoff.relative_to(self.repo_root))
            
            return metadata
        
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Failed to parse session metadata: {e}")
            return None
    
    def _collect_changed_files(self) -> list[str]:
        """Collect changed files from Git.
        
        Returns:
            List of changed file paths
        """
        try:
            # Get staged and unstaged changes
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
                return files
            
            # Fallback: get all uncommitted changes
            result = subprocess.run(
                ["git", "status", "--short"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                files = []
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        # Parse git status format: "XY filename"
                        parts = line.strip().split(maxsplit=1)
                        if len(parts) == 2:
                            files.append(parts[1])
                return files
            
            return []
        
        except Exception as e:
            print(f"Warning: Failed to collect changed files from Git: {e}")
            return []
    
    def _collect_scope_data(
        self,
        task_dir: Path,
        changed_files: list[str]
    ) -> dict[str, Any] | None:
        """Collect scope control data.
        
        Args:
            task_dir: Task directory path
            changed_files: List of changed files from Git
            
        Returns:
            Scope control data dict or None
        """
        task_brief = task_dir / "task_brief.md"
        
        if not task_brief.exists():
            return None
        
        # TODO: Parse task brief YAML frontmatter for allowed/blocked paths
        # For now, return basic structure
        scope_data = {
            "allowed_paths": [],
            "blocked_paths": [],
            "changed_files_within_scope": True,
            "out_of_scope_changes": [],
            "dependency_changes": [],
            "public_api_changes": []
        }
        
        # Detect dependency changes
        dependency_files = [
            "requirements.txt",
            "pyproject.toml",
            "setup.py",
            "package.json",
            "package-lock.json",
            "yarn.lock",
            "Cargo.toml",
            "Cargo.lock",
            "go.mod",
            "go.sum",
            "pom.xml",
            "build.gradle"
        ]
        
        for file in changed_files:
            filename = Path(file).name
            if filename in dependency_files:
                scope_data["dependency_changes"].append(file)
        
        return scope_data if scope_data["dependency_changes"] else None
    
    def _collect_test_results(self, task_dir: Path) -> list[dict[str, Any]]:
        """Collect test results from tool log.
        
        Args:
            task_dir: Task directory path
            
        Returns:
            List of test result dicts
        """
        tool_log = task_dir / "logs/openhands_tool_log.jsonl"
        
        if not tool_log.exists():
            return []
        
        test_results = []
        
        try:
            with open(tool_log) as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    try:
                        event = json.loads(line)
                        
                        # Look for test commands
                        if event.get("tool_name") == "terminal":
                            args = event.get("tool_args", {})
                            command = args.get("command", "")
                            
                            # Detect test commands
                            test_keywords = ["pytest", "test", "npm test", "cargo test", "go test"]
                            if any(keyword in command for keyword in test_keywords):
                                result = event.get("result", {})
                                
                                test_result = {
                                    "command": command,
                                    "timestamp": event.get("timestamp"),
                                    "exit_code": result.get("exit_code"),
                                    "stdout": result.get("stdout", "")[:500],  # Truncate
                                }
                                
                                # Try to parse test output
                                stdout = result.get("stdout", "")
                                if "passed" in stdout.lower():
                                    test_result["status"] = "passed"
                                elif "failed" in stdout.lower():
                                    test_result["status"] = "failed"
                                elif result.get("exit_code") == 0:
                                    test_result["status"] = "passed"
                                else:
                                    test_result["status"] = "failed"
                                
                                test_results.append(test_result)
                    
                    except json.JSONDecodeError:
                        continue
        
        except Exception as e:
            print(f"Warning: Failed to parse tool log: {e}")
        
        return test_results
    
    def _collect_check_results(self, task_dir: Path) -> list[dict[str, Any]]:
        """Collect lint/typecheck/build results from tool log.
        
        Args:
            task_dir: Task directory path
            
        Returns:
            List of check result dicts
        """
        tool_log = task_dir / "logs/openhands_tool_log.jsonl"
        
        if not tool_log.exists():
            return []
        
        check_results = []
        
        try:
            with open(tool_log) as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    try:
                        event = json.loads(line)
                        
                        # Look for check commands
                        if event.get("tool_name") == "terminal":
                            args = event.get("tool_args", {})
                            command = args.get("command", "")
                            
                            # Detect check commands
                            check_keywords = {
                                "lint": ["ruff", "pylint", "eslint", "clippy"],
                                "typecheck": ["mypy", "tsc", "pyright"],
                                "build": ["make", "cargo build", "npm run build", "go build"]
                            }
                            
                            for check_type, keywords in check_keywords.items():
                                if any(keyword in command for keyword in keywords):
                                    result = event.get("result", {})
                                    
                                    check_result = {
                                        "type": check_type,
                                        "command": command,
                                        "timestamp": event.get("timestamp"),
                                        "exit_code": result.get("exit_code"),
                                        "status": "passed" if result.get("exit_code") == 0 else "failed",
                                        "output": result.get("stdout", "")[:500],  # Truncate
                                    }
                                    
                                    check_results.append(check_result)
                                    break
                    
                    except json.JSONDecodeError:
                        continue
        
        except Exception as e:
            print(f"Warning: Failed to parse tool log for checks: {e}")
        
        return check_results
    
    def update_evidence_bundle(
        self,
        task_id: str,
        collected_evidence: dict[str, Any]
    ) -> None:
        """Update evidence bundle with collected evidence.
        
        Args:
            task_id: Task ID
            collected_evidence: Evidence data to merge
        """
        task_dir = self.repo_root / ".agentic-agile-v/tasks" / task_id
        bundle_path = task_dir / "evidence_bundle.json"
        
        # Load existing evidence bundle
        if bundle_path.exists():
            with open(bundle_path) as f:
                bundle = json.load(f)
        else:
            # Create minimal bundle if doesn't exist
            bundle = {
                "task_id": task_id,
                "title": "Unknown",
                "task_type": "other",
                "risk_level": "L1",
                "requirement_ids": [],
                "brief_path": "",
                "plan_path": "",
                "changed_files": [],
                "tests": [],
                "checks": [],
                "evidence_artifacts": [],
                "reviewer_gate": {},
                "rollback_path": "",
                "residual_risks": []
            }
        
        # Merge collected evidence
        for key, value in collected_evidence.items():
            if key == "changed_files":
                # Replace changed_files with Git truth
                bundle[key] = value
            elif key in ["tests", "checks"]:
                # Append to arrays
                if key not in bundle:
                    bundle[key] = []
                bundle[key] = value  # Replace with parsed results
            else:
                # Add new top-level fields
                bundle[key] = value
        
        # Write updated bundle
        with open(bundle_path, 'w') as f:
            json.dump(bundle, f, indent=2)
