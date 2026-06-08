"""Scope policy enforcement for OpenHands integration.

Validates that file changes are within allowed scope as defined in task briefs.
"""
from __future__ import annotations

import fnmatch
import re
from pathlib import Path
from typing import Any


class ScopePolicy:
    """Represents scope control policy from a task brief."""
    
    def __init__(
        self,
        allowed_paths: list[str] | None = None,
        blocked_paths: list[str] | None = None,
        public_api_changes_allowed: bool = False,
        dependency_changes_allowed: bool = False
    ):
        """Initialize scope policy.
        
        Args:
            allowed_paths: List of glob patterns for allowed file changes
            blocked_paths: List of glob patterns for blocked file changes
            public_api_changes_allowed: Whether public API changes are allowed
            dependency_changes_allowed: Whether dependency changes are allowed
        """
        self.allowed_paths = allowed_paths or []
        self.blocked_paths = blocked_paths or []
        self.public_api_changes_allowed = public_api_changes_allowed
        self.dependency_changes_allowed = dependency_changes_allowed
    
    def is_path_allowed(self, file_path: str) -> tuple[bool, str]:
        """Check if a file path is allowed.
        
        Args:
            file_path: File path to check
            
        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        # Check blocked paths first
        for pattern in self.blocked_paths:
            if self._matches_pattern(file_path, pattern):
                return False, f"File is in blocked path: {pattern}"
        
        # If no allowed paths specified, allow all (except blocked)
        if not self.allowed_paths:
            return True, "No scope restrictions"
        
        # Check allowed paths
        for pattern in self.allowed_paths:
            if self._matches_pattern(file_path, pattern):
                return True, f"Matches allowed pattern: {pattern}"
        
        # Not in any allowed path
        return False, f"File not in any allowed path. Allowed: {', '.join(self.allowed_paths)}"
    
    def _matches_pattern(self, file_path: str, pattern: str) -> bool:
        """Check if file path matches glob pattern.
        
        Args:
            file_path: File path to check
            pattern: Glob pattern (supports *, **, ?)
            
        Returns:
            True if path matches pattern
        """
        # Normalize paths
        file_path = file_path.replace('\\', '/')
        pattern = pattern.replace('\\', '/')
        
        # Handle ** (match any number of directories)
        if '**' in pattern:
            # Convert to regex, handling ** before single *
            # Replace ** with a placeholder first
            regex_pattern = pattern.replace('**', '__DOUBLESTAR__')
            # Replace single * and ?
            regex_pattern = regex_pattern.replace('*', '[^/]*').replace('?', '[^/]')
            # Replace placeholder with .*
            regex_pattern = regex_pattern.replace('__DOUBLESTAR__', '.*')
            regex_pattern = f"^{regex_pattern}$"
            return bool(re.match(regex_pattern, file_path))
        
        # Use fnmatch for simple glob patterns
        return fnmatch.fnmatch(file_path, pattern)


class ScopeValidator:
    """Validates file changes against scope policy."""
    
    def __init__(self, repo_root: Path | None = None):
        """Initialize scope validator.
        
        Args:
            repo_root: Repository root directory
        """
        self.repo_root = repo_root or Path.cwd()
    
    def parse_task_brief_scope(self, task_id: str) -> ScopePolicy:
        """Parse scope policy from task brief.
        
        Args:
            task_id: Task ID
            
        Returns:
            ScopePolicy object
        """
        task_dir = self.repo_root / ".agentic-agile-v/tasks" / task_id
        brief_path = task_dir / "task_brief.md"
        
        if not brief_path.exists():
            return ScopePolicy()  # Empty policy
        
        try:
            content = brief_path.read_text()
            
            # Look for YAML frontmatter
            if content.startswith('---'):
                # Extract frontmatter
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = parts[1]
                    
                    # Parse YAML (simple parsing for MVP)
                    allowed_paths = self._extract_yaml_list(frontmatter, 'allowed_paths')
                    blocked_paths = self._extract_yaml_list(frontmatter, 'blocked_paths')
                    public_api = self._extract_yaml_bool(frontmatter, 'public_api_changes_allowed')
                    dependency = self._extract_yaml_bool(frontmatter, 'dependency_changes_allowed')
                    
                    return ScopePolicy(
                        allowed_paths=allowed_paths,
                        blocked_paths=blocked_paths,
                        public_api_changes_allowed=public_api,
                        dependency_changes_allowed=dependency
                    )
            
            return ScopePolicy()
        
        except Exception as e:
            print(f"Warning: Failed to parse task brief scope: {e}")
            return ScopePolicy()
    
    def _extract_yaml_list(self, yaml_text: str, key: str) -> list[str]:
        """Extract list from YAML text (simple parser).
        
        Args:
            yaml_text: YAML text
            key: Key to extract
            
        Returns:
            List of strings
        """
        lines = yaml_text.split('\n')
        result = []
        in_list = False
        
        for line in lines:
            stripped = line.strip()
            
            # Check if this is the key we're looking for
            if stripped.startswith(f"{key}:"):
                in_list = True
                # Check if value is on same line (e.g., "key: [val1, val2]")
                if '[' in line and ']' in line:
                    # Parse inline list
                    list_str = line.split('[')[1].split(']')[0]
                    items = [item.strip().strip('"').strip("'") for item in list_str.split(',')]
                    return [item for item in items if item]
                continue
            
            if in_list:
                # Check if still in list (starts with -)
                if stripped.startswith('-'):
                    # Extract value
                    value = stripped[1:].strip().strip('"').strip("'")
                    if value:
                        result.append(value)
                elif stripped and not stripped.startswith('#'):
                    # End of list (new key or non-list item)
                    break
        
        return result
    
    def _extract_yaml_bool(self, yaml_text: str, key: str) -> bool:
        """Extract boolean from YAML text (simple parser).
        
        Args:
            yaml_text: YAML text
            key: Key to extract
            
        Returns:
            Boolean value
        """
        for line in yaml_text.split('\n'):
            stripped = line.strip()
            if stripped.startswith(f"{key}:"):
                value = stripped.split(':', 1)[1].strip().lower()
                return value in ['true', 'yes', '1']
        
        return False
    
    def validate_changes(
        self,
        task_id: str,
        changed_files: list[str]
    ) -> dict[str, Any]:
        """Validate changed files against scope policy.
        
        Args:
            task_id: Task ID
            changed_files: List of changed file paths
            
        Returns:
            Validation result dict with violations
        """
        policy = self.parse_task_brief_scope(task_id)
        
        violations = []
        warnings = []
        allowed_count = 0
        
        for file_path in changed_files:
            allowed, reason = policy.is_path_allowed(file_path)
            
            if allowed:
                allowed_count += 1
            else:
                violations.append({
                    "file": file_path,
                    "reason": reason
                })
        
        # Check for dependency changes
        dependency_files = self._detect_dependency_files(changed_files)
        if dependency_files and not policy.dependency_changes_allowed:
            warnings.append({
                "type": "dependency_changes",
                "files": dependency_files,
                "message": "Dependency files changed but dependency_changes_allowed=false in task brief"
            })
        
        return {
            "policy": {
                "allowed_paths": policy.allowed_paths,
                "blocked_paths": policy.blocked_paths,
                "public_api_changes_allowed": policy.public_api_changes_allowed,
                "dependency_changes_allowed": policy.dependency_changes_allowed
            },
            "total_files": len(changed_files),
            "allowed_files": allowed_count,
            "violations": violations,
            "warnings": warnings,
            "passed": len(violations) == 0
        }
    
    def _detect_dependency_files(self, files: list[str]) -> list[str]:
        """Detect dependency management files.
        
        Args:
            files: List of file paths
            
        Returns:
            List of dependency files
        """
        dependency_patterns = [
            "requirements.txt",
            "requirements-*.txt",
            "pyproject.toml",
            "setup.py",
            "setup.cfg",
            "Pipfile",
            "Pipfile.lock",
            "package.json",
            "package-lock.json",
            "yarn.lock",
            "pnpm-lock.yaml",
            "Cargo.toml",
            "Cargo.lock",
            "go.mod",
            "go.sum",
            "pom.xml",
            "build.gradle",
            "build.gradle.kts",
            "Gemfile",
            "Gemfile.lock",
        ]
        
        dependency_files = []
        for file_path in files:
            filename = Path(file_path).name
            for pattern in dependency_patterns:
                if fnmatch.fnmatch(filename, pattern):
                    dependency_files.append(file_path)
                    break
        
        return dependency_files
