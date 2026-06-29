"""Helpers for OpenHands control matrix hooks.

Provides tool-class classification and control-event logging used by shell hooks
and the CLI enforcement commands.

Tool classification uses a two-pass lookup:
1. Try the full (normalised) tool name string.
2. Try the first word of the tool name.

This ensures that compound tool names like ``"git diff"`` and ``"git status"``
map to distinct tool classes (``git_diff`` and ``git_status``) while still
supporting simple names like ``"git"`` via the first-word fallback.

The Python ``_TOOL_CLASS_MAP`` is the authoritative in-process registry.
``config/policies/control_matrix_policy.yaml`` documents the same mapping for
human operators; both must be kept in sync.  A CI step in
``.github/workflows/control-matrix.yml`` diffs them on each push.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tool classification
# ---------------------------------------------------------------------------

#: Mapping from OpenHands concrete tool names/prefixes to control matrix tool classes.
#: Multi-word names (e.g. "git diff") take priority over single-word prefixes.
_TOOL_CLASS_MAP: dict[str, str] = {
    # shell / terminal
    "terminal": "shell_exec",
    "bash": "shell_exec",
    "sh": "shell_exec",
    "exec": "shell_exec",
    # filesystem read
    "read_file": "read_file",
    "read": "read_file",
    "cat": "read_file",
    "list_files": "list_files",
    "ls": "list_files",
    "find": "list_files",
    "glob": "list_files",
    "grep": "read_file",
    "sed": "read_file",
    "awk": "read_file",
    # filesystem write
    "write_file": "write_file",
    "write": "write_file",
    "edit": "write_file",
    "patch": "write_file",
    "create_file": "write_file",
    # git — compound names first for precise matching
    "git diff": "git_diff",
    "git status": "git_status",
    "git log": "git_status",
    "git show": "git_diff",
    "git add": "git_write",
    "git commit": "git_write",
    "git push": "git_write",
    "git merge": "git_write",
    "git rebase": "git_write",
    "git checkout": "git_write",
    "git branch": "git_status",
    "git": "git_diff",  # single-word fallback
    "git_diff": "git_diff",
    "git_status": "git_status",
    # network
    "curl": "network_egress",
    "wget": "network_egress",
    "fetch": "network_egress",
    "http": "network_egress",
    "web_search": "network_egress",
    # dependency install
    "pip": "dependency_install",
    "npm": "dependency_install",
    "pnpm": "dependency_install",
    "yarn": "dependency_install",
    "cargo": "dependency_install",
    # database
    "alembic": "database_migration",
    "prisma": "database_migration",
    "knex": "database_migration",
    # test runner
    "pytest": "run_tests",
    "unittest": "run_tests",
    "jest": "run_tests",
    "run_tests": "run_tests",
    # static analysis
    "ruff": "static_analysis",
    "mypy": "static_analysis",
    "flake8": "static_analysis",
    "eslint": "static_analysis",
    "static_analysis": "static_analysis",
    # schema validation
    "schema_validation": "schema_validation",
    # production / destructive
    "deploy": "deploy_production",
    "kubectl": "deploy_production",
    "kubectl apply": "deploy_production",
    "kubectl delete": "deploy_production",
    "helm": "deploy_production",
    "helm upgrade": "deploy_production",
    "helm install": "deploy_production",
}


def classify_tool(tool_name: str) -> str:
    """Return the control matrix tool class for *tool_name*.

    Performs a two-pass lookup:
    1. Full normalised name (e.g. ``"git diff"`` → ``"git_diff"``).
    2. First word of the normalised name (e.g. ``"git"`` → ``"git_diff"``).

    Falls back to the original *tool_name* when no mapping is found.
    Unknown tool classes will be denied unless the matrix explicitly allows them.
    """
    normalised = tool_name.lower().strip()
    if normalised in _TOOL_CLASS_MAP:
        return _TOOL_CLASS_MAP[normalised]
    first_word = normalised.split()[0] if normalised else normalised
    return _TOOL_CLASS_MAP.get(first_word, tool_name)


# ---------------------------------------------------------------------------
# Control event logging
# ---------------------------------------------------------------------------


def append_control_event(
    log_path: Path,
    task_id: str,
    control_id: str,
    check: str,
    decision: str,
    reason: str,
    extra: dict[str, Any] | None = None,
) -> None:
    """Append a JSONL control event to *log_path*.

    Creates parent directories and the file if they do not exist.
    Write failures are logged to stderr but never propagated — logging must
    not block enforcement.
    """
    entry: dict[str, Any] = {
        "timestamp": datetime.now(UTC).isoformat(),
        "task_id": task_id,
        "control_id": control_id,
        "check": check,
        "decision": decision,
        "reason": reason,
    }
    if extra:
        entry.update(extra)
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
    except OSError as exc:
        print(
            f"WARNING: control matrix log write failed ({log_path}): {exc}",
            file=sys.stderr,
        )


# ---------------------------------------------------------------------------
# Approval lookup
# ---------------------------------------------------------------------------


def has_approval(approvals_file: Path, task_id: str, gate: str) -> bool:
    """Return ``True`` when a durable approval row exists for *task_id* and *gate*.

    Looks for lines in *approvals_file* that contain both *task_id* and *gate*
    and the **whole word** ``approved`` (so ``not_approved`` does not match).

    This is a lightweight heuristic check; the full audit relies on the pipe-
    delimited APPROVALS.md format.
    """
    import re

    if not approvals_file.exists():
        return False
    content = approvals_file.read_text(encoding="utf-8")
    approved_pattern = re.compile(r"\bapproved\b", re.IGNORECASE)
    for line in content.splitlines():
        if task_id in line and gate in line and approved_pattern.search(line):
            return True
    return False


# ---------------------------------------------------------------------------
# Matrix path resolution
# ---------------------------------------------------------------------------


def find_matrix_path(root: Path) -> Path | None:
    """Return the first existing control matrix path under *root*, or ``None``."""
    candidates = [
        root / ".agile-v" / "CONTROL_MATRIX.yaml",
        root / "config" / "control_matrix.yaml",
    ]
    return next((p for p in candidates if p.exists()), None)


def load_raw_matrix(root: Path) -> dict[str, Any] | None:
    """Load the raw YAML dict for the control matrix, or ``None``."""
    path = find_matrix_path(root)
    if path is None:
        return None
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}
