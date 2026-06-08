"""Task context resolution for OpenHands integration.

Resolves the active Agile-V task from various sources:
- CLI option (--task AAV-001)
- Environment variable (AGILEV_TASK_ID)
- Git branch name (aav-001-*)
- GitHub metadata (in CI)
- Latest modified task (if unambiguous)
"""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path


class TaskContextResolver:
    """Resolves active task context from multiple sources."""
    
    def __init__(self, repo_root: Path | None = None):
        """Initialize task context resolver.
        
        Args:
            repo_root: Repository root directory (defaults to current directory)
        """
        self.repo_root = repo_root or Path.cwd()
    
    def resolve(
        self,
        explicit_task_id: str | None = None,
        fail_on_ambiguous: bool = True
    ) -> str | None:
        """Resolve task ID from available sources.
        
        Args:
            explicit_task_id: Explicitly provided task ID (highest priority)
            fail_on_ambiguous: Raise error if task context is ambiguous
            
        Returns:
            Task ID (e.g., "AAV-0001") or None if not found
            
        Raises:
            ValueError: If task context is ambiguous and fail_on_ambiguous=True
        """
        # 1. Explicit CLI option
        if explicit_task_id:
            return self._normalize_task_id(explicit_task_id)
        
        # 2. Environment variable
        env_task_id = os.environ.get("AGILEV_TASK_ID")
        if env_task_id:
            return self._normalize_task_id(env_task_id)
        
        # 3. Git branch name
        branch_task_id = self._resolve_from_branch()
        if branch_task_id:
            return branch_task_id
        
        # 4. GitHub metadata (in CI)
        github_task_id = self._resolve_from_github()
        if github_task_id:
            return github_task_id
        
        # 5. Latest modified task (if unambiguous)
        latest_task_id = self._resolve_from_latest_modified(fail_on_ambiguous)
        if latest_task_id:
            return latest_task_id
        
        return None
    
    def _normalize_task_id(self, task_id: str) -> str:
        """Normalize task ID to AAV-XXXX format.
        
        Args:
            task_id: Task ID in various formats (AAV-001, aav-1, 1, etc.)
            
        Returns:
            Normalized task ID (AAV-0001)
        """
        # Extract number
        match = re.search(r'(\d+)', task_id)
        if not match:
            return task_id  # Return as-is if no number found
        
        task_num = int(match.group(1))
        return f"AAV-{task_num:04d}"
    
    def _resolve_from_branch(self) -> str | None:
        """Resolve task ID from Git branch name.
        
        Returns:
            Task ID if branch matches pattern, None otherwise
        """
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode != 0:
                return None
            
            branch = result.stdout.strip()
            
            # Match patterns like: aav-001-*, AAV-001-*, aav-1-*
            match = re.match(r'^aav-(\d+)', branch, re.IGNORECASE)
            if match:
                task_num = int(match.group(1))
                return f"AAV-{task_num:04d}"
            
            return None
        except Exception:
            return None
    
    def _resolve_from_github(self) -> str | None:
        """Resolve task ID from GitHub environment variables.
        
        Returns:
            Task ID if found in GitHub context, None otherwise
        """
        # GitHub PR title or issue title
        pr_title = os.environ.get("GITHUB_PR_TITLE", "")
        issue_title = os.environ.get("GITHUB_ISSUE_TITLE", "")
        
        for title in [pr_title, issue_title]:
            match = re.search(r'AAV-(\d{4})', title, re.IGNORECASE)
            if match:
                return match.group(0).upper()
        
        return None
    
    def _resolve_from_latest_modified(self, fail_on_ambiguous: bool) -> str | None:
        """Resolve task ID from latest modified task directory.
        
        Args:
            fail_on_ambiguous: Raise error if multiple tasks modified recently
            
        Returns:
            Task ID if unambiguous, None otherwise
            
        Raises:
            ValueError: If multiple tasks modified and fail_on_ambiguous=True
        """
        tasks_dir = self.repo_root / ".agentic-agile-v/tasks"
        if not tasks_dir.exists():
            return None
        
        # Find all task directories
        task_dirs = [d for d in tasks_dir.iterdir() if d.is_dir() and re.match(r'^AAV-\d{4}$', d.name)]
        
        if not task_dirs:
            return None
        
        if len(task_dirs) == 1:
            return task_dirs[0].name
        
        # Multiple tasks exist - check modification times
        # Consider "recently modified" as within last 24 hours
        import time
        now = time.time()
        recent_threshold = 24 * 3600  # 24 hours
        
        recent_tasks = []
        for task_dir in task_dirs:
            # Check modification time of evidence bundle or task brief
            evidence_bundle = task_dir / "evidence_bundle.json"
            task_brief = task_dir / "task_brief.md"
            
            max_mtime = 0
            for file_path in [evidence_bundle, task_brief]:
                if file_path.exists():
                    max_mtime = max(max_mtime, file_path.stat().st_mtime)
            
            if max_mtime > 0 and (now - max_mtime) < recent_threshold:
                recent_tasks.append((task_dir.name, max_mtime))
        
        if len(recent_tasks) == 0:
            return None
        
        if len(recent_tasks) == 1:
            return recent_tasks[0][0]
        
        # Multiple recent tasks - ambiguous
        if fail_on_ambiguous:
            task_names = [t[0] for t in recent_tasks]
            raise ValueError(
                f"Ambiguous task context: multiple tasks modified recently: {', '.join(task_names)}. "
                f"Specify task explicitly: --task AAV-XXXX or AGILEV_TASK_ID=AAV-XXXX"
            )
        
        # Return most recently modified
        recent_tasks.sort(key=lambda x: x[1], reverse=True)
        return recent_tasks[0][0]
    
    def get_task_dir(self, task_id: str) -> Path:
        """Get task directory path.
        
        Args:
            task_id: Task ID
            
        Returns:
            Path to task directory
        """
        normalized_id = self._normalize_task_id(task_id)
        return self.repo_root / ".agentic-agile-v/tasks" / normalized_id
    
    def validate_task_exists(self, task_id: str) -> bool:
        """Check if task exists.
        
        Args:
            task_id: Task ID
            
        Returns:
            True if task directory exists, False otherwise
        """
        task_dir = self.get_task_dir(task_id)
        return task_dir.exists() and (task_dir / "task_brief.md").exists()
