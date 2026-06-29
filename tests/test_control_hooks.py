"""Unit tests for openhands/control_hooks.py.

Implements: REQ-CM-011 (tool classification), REQ-CM-012 (approval check),
            REQ-CM-013 (event logging)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agilev.openhands.control_hooks import (
    append_control_event,
    classify_tool,
    find_matrix_path,
    has_approval,
    load_raw_matrix,
)


# ---------------------------------------------------------------------------
# classify_tool
# ---------------------------------------------------------------------------


class TestClassifyTool:
    def test_known_single_word(self):
        assert classify_tool("read_file") == "read_file"

    def test_known_single_word_case_insensitive(self):
        assert classify_tool("READ_FILE") == "read_file"

    def test_compound_git_diff(self):
        assert classify_tool("git diff") == "git_diff"

    def test_compound_git_status(self):
        assert classify_tool("git status") == "git_status"

    def test_compound_git_status_not_mapped_as_diff(self):
        # git status must not resolve to git_diff
        assert classify_tool("git status") != "git_diff"

    def test_compound_git_log_is_status(self):
        assert classify_tool("git log") == "git_status"

    def test_compound_git_commit_is_write(self):
        assert classify_tool("git commit") == "git_write"

    def test_single_word_git_fallback(self):
        # Single "git" falls back to git_diff (first-word fallback)
        assert classify_tool("git") == "git_diff"

    def test_compound_kubectl_apply(self):
        assert classify_tool("kubectl apply") == "deploy_production"

    def test_compound_helm_upgrade(self):
        assert classify_tool("helm upgrade") == "deploy_production"

    def test_shell_exec(self):
        assert classify_tool("bash") == "shell_exec"

    def test_dependency_install(self):
        assert classify_tool("pip") == "dependency_install"

    def test_network_egress(self):
        assert classify_tool("curl") == "network_egress"

    def test_run_tests(self):
        assert classify_tool("pytest") == "run_tests"

    def test_static_analysis(self):
        assert classify_tool("ruff") == "static_analysis"

    def test_sed_mapped_as_read_file(self):
        assert classify_tool("sed") == "read_file"

    def test_awk_mapped_as_read_file(self):
        assert classify_tool("awk") == "read_file"

    def test_unknown_tool_returns_original_name(self):
        result = classify_tool("some_custom_tool_xyz")
        assert result == "some_custom_tool_xyz"

    def test_unknown_compound_returns_original_name(self):
        result = classify_tool("unknown_tool with args")
        assert result == "unknown_tool with args"

    def test_leading_trailing_whitespace_stripped(self):
        assert classify_tool("  pytest  ") == "run_tests"


# ---------------------------------------------------------------------------
# has_approval
# ---------------------------------------------------------------------------


class TestHasApproval:
    def test_returns_false_when_file_missing(self, tmp_path: Path):
        result = has_approval(tmp_path / "APPROVALS.md", "TASK-001", "G2")
        assert result is False

    def test_returns_true_when_approval_present(self, tmp_path: Path):
        f = tmp_path / "APPROVALS.md"
        f.write_text("2026-06-28 | TASK-001 | G2 | alice | approved\n")
        assert has_approval(f, "TASK-001", "G2") is True

    def test_returns_false_when_task_id_missing(self, tmp_path: Path):
        f = tmp_path / "APPROVALS.md"
        f.write_text("2026-06-28 | TASK-002 | G2 | alice | approved\n")
        assert has_approval(f, "TASK-001", "G2") is False

    def test_returns_false_when_gate_missing(self, tmp_path: Path):
        f = tmp_path / "APPROVALS.md"
        f.write_text("2026-06-28 | TASK-001 | G1 | alice | approved\n")
        assert has_approval(f, "TASK-001", "G2") is False

    def test_not_approved_does_not_match(self, tmp_path: Path):
        """'not_approved' must not match the word-boundary 'approved' check."""
        f = tmp_path / "APPROVALS.md"
        f.write_text("2026-06-28 | TASK-001 | G2 | alice | not_approved\n")
        assert has_approval(f, "TASK-001", "G2") is False

    def test_not_approved_substring_no_false_positive(self, tmp_path: Path):
        """Substring 'approved' inside 'not_approved' must not trigger a match."""
        f = tmp_path / "APPROVALS.md"
        f.write_text("TASK-001 G2 not_approved by alice\n")
        assert has_approval(f, "TASK-001", "G2") is False

    def test_case_insensitive_approved(self, tmp_path: Path):
        f = tmp_path / "APPROVALS.md"
        f.write_text("TASK-001 | G2 | APPROVED\n")
        assert has_approval(f, "TASK-001", "G2") is True

    def test_multiline_file_matches_correct_line(self, tmp_path: Path):
        f = tmp_path / "APPROVALS.md"
        f.write_text(
            "2026-06-28 | TASK-000 | G1 | alice | approved\n"
            "2026-06-28 | TASK-001 | G2 | bob   | approved\n"
            "2026-06-28 | TASK-002 | G2 | carol | not_approved\n"
        )
        assert has_approval(f, "TASK-001", "G2") is True
        assert has_approval(f, "TASK-002", "G2") is False

    def test_empty_file_returns_false(self, tmp_path: Path):
        f = tmp_path / "APPROVALS.md"
        f.write_text("")
        assert has_approval(f, "TASK-001", "G2") is False


# ---------------------------------------------------------------------------
# append_control_event
# ---------------------------------------------------------------------------


class TestAppendControlEvent:
    def test_creates_file_and_appends_jsonl(self, tmp_path: Path):
        log = tmp_path / "logs" / "control-events.jsonl"
        append_control_event(log, "TASK-001", "cm-test", "tool", "allow", "Tool allowed")
        assert log.exists()
        entry = json.loads(log.read_text().strip())
        assert entry["task_id"] == "TASK-001"
        assert entry["control_id"] == "cm-test"
        assert entry["check"] == "tool"
        assert entry["decision"] == "allow"
        assert entry["reason"] == "Tool allowed"
        assert "timestamp" in entry

    def test_appends_multiple_entries(self, tmp_path: Path):
        log = tmp_path / "events.jsonl"
        for i in range(3):
            append_control_event(log, f"TASK-{i:03d}", "cm-test", "tool", "allow", f"event {i}")
        lines = [l for l in log.read_text().splitlines() if l.strip()]
        assert len(lines) == 3

    def test_extra_fields_included(self, tmp_path: Path):
        log = tmp_path / "events.jsonl"
        append_control_event(
            log,
            "TASK-001",
            "cm-test",
            "tool",
            "deny",
            "Forbidden",
            extra={"tool_class": "deploy_production"},
        )
        entry = json.loads(log.read_text().strip())
        assert entry["tool_class"] == "deploy_production"

    def test_write_failure_does_not_raise(self, tmp_path: Path):
        """A read-only directory must not propagate OSError."""
        read_only_dir = tmp_path / "readonly"
        read_only_dir.mkdir()
        read_only_dir.chmod(0o555)
        log = read_only_dir / "subdir" / "events.jsonl"
        try:
            # Should not raise; failure is logged to stderr
            append_control_event(log, "TASK-001", "cm-test", "tool", "allow", "ok")
        except OSError:
            pytest.fail("append_control_event raised OSError instead of swallowing it")
        finally:
            read_only_dir.chmod(0o755)


# ---------------------------------------------------------------------------
# find_matrix_path / load_raw_matrix
# ---------------------------------------------------------------------------


class TestFindMatrixPath:
    def test_returns_none_when_missing(self, tmp_path: Path):
        assert find_matrix_path(tmp_path) is None

    def test_finds_config_path(self, tmp_path: Path):
        p = tmp_path / "config" / "control_matrix.yaml"
        p.parent.mkdir()
        p.write_text("version: '1.0.0'\n")
        assert find_matrix_path(tmp_path) == p

    def test_agile_v_dir_takes_precedence(self, tmp_path: Path):
        config_path = tmp_path / "config" / "control_matrix.yaml"
        config_path.parent.mkdir()
        config_path.write_text("version: '1.0.0'\n")
        agile_v_path = tmp_path / ".agile-v" / "CONTROL_MATRIX.yaml"
        agile_v_path.parent.mkdir()
        agile_v_path.write_text("version: '2.0.0'\n")
        assert find_matrix_path(tmp_path) == agile_v_path


class TestLoadRawMatrix:
    def test_returns_none_when_missing(self, tmp_path: Path):
        assert load_raw_matrix(tmp_path) is None

    def test_loads_yaml(self, tmp_path: Path):
        p = tmp_path / "config" / "control_matrix.yaml"
        p.parent.mkdir()
        p.write_text("version: '1.0.0'\ncontrols: []\n")
        result = load_raw_matrix(tmp_path)
        assert result is not None
        assert result["version"] == "1.0.0"
