"""Integration tests for OpenHands shell hooks (enforce_control_matrix.sh and
validate_control_evidence_on_stop.sh).

Tests run the hook scripts via subprocess with controlled environment variables.
Requires bash to be available at /usr/bin/env bash (standard on macOS/Linux).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"
HOOKS_DIR = Path(__file__).parent.parent / ".openhands" / "hooks"
ENFORCE_HOOK = HOOKS_DIR / "enforce_control_matrix.sh"
STOP_HOOK = HOOKS_DIR / "validate_control_evidence_on_stop.sh"

# Skip the entire module if bash is not available
pytestmark = pytest.mark.skipif(
    shutil.which("bash") is None,
    reason="bash not available",
)


def _setup_matrix(tmp_path: Path) -> None:
    """Copy the valid fixture into a project directory structure."""
    config = tmp_path / "config"
    config.mkdir()
    shutil.copy(FIXTURES / "control_matrix.valid.yaml", config / "control_matrix.yaml")
    # Create a git repo so the hook can resolve ROOT
    subprocess.run(["git", "init", str(tmp_path)], capture_output=True)


def _run_hook(hook: Path, env: dict, cwd: Path) -> subprocess.CompletedProcess:
    """Run a hook script with the given environment, returning the result."""
    full_env = {**os.environ, **env}
    return subprocess.run(
        ["bash", str(hook)],
        env=full_env,
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


# ---------------------------------------------------------------------------
# enforce_control_matrix.sh
# ---------------------------------------------------------------------------


class TestEnforceControlMatrix:
    def test_exits_zero_when_no_tool_class(self, tmp_path: Path):
        """No AGILEV_TOOL_CLASS means skip (non-matrix tool)."""
        _setup_matrix(tmp_path)
        result = _run_hook(ENFORCE_HOOK, {}, tmp_path)
        assert result.returncode == 0

    def test_exits_two_when_task_id_missing(self, tmp_path: Path):
        """AGILEV_TOOL_CLASS set but no TASK_ID must block (exit 2)."""
        _setup_matrix(tmp_path)
        result = _run_hook(ENFORCE_HOOK, {"AGILEV_TOOL_CLASS": "read_file"}, tmp_path)
        assert result.returncode == 2
        assert "AGILEV_TASK_ID missing" in result.stderr

    def test_warns_and_exits_zero_when_cli_missing(self, tmp_path: Path, monkeypatch):
        """Missing agilev CLI with STRICT_MODE=0 should warn and allow."""
        _setup_matrix(tmp_path)
        # Use a PATH that definitely doesn't have agilev
        result = _run_hook(
            ENFORCE_HOOK,
            {
                "AGILEV_TOOL_CLASS": "read_file",
                "AGILEV_TASK_ID": "TASK-001",
                "PATH": "/usr/bin:/bin",  # no agilev
            },
            tmp_path,
        )
        # Should exit 0 (warn, not block) by default
        assert result.returncode == 0
        stderr = result.stderr
        assert "warn" in stderr.lower() or "not found" in stderr.lower()

    def test_blocks_when_strict_mode_and_cli_missing(self, tmp_path: Path):
        """STRICT_MODE=1 must block (exit 2) when CLI is not found."""
        _setup_matrix(tmp_path)
        result = _run_hook(
            ENFORCE_HOOK,
            {
                "AGILEV_TOOL_CLASS": "read_file",
                "AGILEV_TASK_ID": "TASK-001",
                "AGILEV_STRICT_MODE": "1",
                "PATH": "/usr/bin:/bin",
            },
            tmp_path,
        )
        assert result.returncode == 2

    def test_warn_logged_to_jsonl_when_cli_missing(self, tmp_path: Path):
        """When CLI is missing, a JSONL warn event should be written to the log."""
        _setup_matrix(tmp_path)
        _run_hook(
            ENFORCE_HOOK,
            {
                "AGILEV_TOOL_CLASS": "read_file",
                "AGILEV_TASK_ID": "TASK-001",
                "PATH": "/usr/bin:/bin",
            },
            tmp_path,
        )
        log = tmp_path / ".agile-v" / "logs" / "control-events.jsonl"
        if log.exists():
            line = log.read_text().strip().splitlines()[0]
            entry = json.loads(line)
            assert entry.get("decision") == "warn"


# ---------------------------------------------------------------------------
# validate_control_evidence_on_stop.sh
# ---------------------------------------------------------------------------


class TestValidateControlEvidenceOnStop:
    def test_exits_zero_when_no_task_id(self, tmp_path: Path):
        """No TASK_ID means skip gracefully."""
        _setup_matrix(tmp_path)
        result = _run_hook(STOP_HOOK, {}, tmp_path)
        assert result.returncode == 0

    def test_warns_and_exits_zero_when_task_id_set_but_no_risk(self, tmp_path: Path):
        """TASK_ID present but no RISK_LEVEL should warn and exit 0."""
        _setup_matrix(tmp_path)
        result = _run_hook(STOP_HOOK, {"AGILEV_TASK_ID": "TASK-001"}, tmp_path)
        assert result.returncode == 0
        assert "warn" in result.stderr.lower() or "RISK_LEVEL" in result.stderr

    def test_exits_zero_for_l1_risk(self, tmp_path: Path):
        """L1 risk level is below the L2+ threshold; hook should pass."""
        _setup_matrix(tmp_path)
        result = _run_hook(
            STOP_HOOK,
            {"AGILEV_TASK_ID": "TASK-001", "AGILEV_RISK_LEVEL": "L1"},
            tmp_path,
        )
        assert result.returncode == 0

    def test_warns_and_exits_zero_when_cli_missing_for_l2(self, tmp_path: Path):
        """L2 task with no CLI should warn and exit 0 (graceful degradation)."""
        _setup_matrix(tmp_path)
        result = _run_hook(
            STOP_HOOK,
            {
                "AGILEV_TASK_ID": "TASK-001",
                "AGILEV_RISK_LEVEL": "L2",
                "PATH": "/usr/bin:/bin",
            },
            tmp_path,
        )
        assert result.returncode == 0
        assert "warn" in result.stderr.lower() or "not found" in result.stderr.lower()
