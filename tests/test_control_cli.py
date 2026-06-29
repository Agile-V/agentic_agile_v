"""CLI tests for `agilev controls` commands.

Implements: REQ-CM-009 (CLI)
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import pytest
import yaml

from agilev.cli import main

FIXTURES = Path(__file__).parent / "fixtures"


def _setup_valid_matrix(tmp_path: Path) -> Path:
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True)
    shutil.copy(FIXTURES / "control_matrix.valid.yaml", config_dir / "control_matrix.yaml")
    return tmp_path


# ---------------------------------------------------------------------------
# controls validate
# ---------------------------------------------------------------------------


def test_validate_passes_with_valid_matrix(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _setup_valid_matrix(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = main(["controls", "validate"])
    assert result == 0


def test_validate_fails_without_matrix(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    result = main(["controls", "validate"])
    assert result != 0


def test_validate_fails_with_invalid_owner(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True)
    shutil.copy(
        FIXTURES / "control_matrix.invalid_missing_owner.yaml",
        config_dir / "control_matrix.yaml",
    )
    monkeypatch.chdir(tmp_path)
    result = main(["controls", "validate"])
    assert result != 0


def test_validate_fails_with_tool_overlap(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True)
    shutil.copy(
        FIXTURES / "control_matrix.invalid_forbidden_tool.yaml",
        config_dir / "control_matrix.yaml",
    )
    monkeypatch.chdir(tmp_path)
    result = main(["controls", "validate"])
    assert result != 0


# ---------------------------------------------------------------------------
# controls explain
# ---------------------------------------------------------------------------


def test_explain_returns_zero_on_match(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    _setup_valid_matrix(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = main(
        ["controls", "explain", "--task-type", "feature", "--risk", "L1", "--mode", "builder"]
    )
    assert result == 0


def test_explain_json_output_parseable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    _setup_valid_matrix(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = main(
        [
            "controls",
            "explain",
            "--task-type",
            "feature",
            "--risk",
            "L1",
            "--mode",
            "builder",
            "--json",
        ]
    )
    assert result == 0
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert "id" in parsed


# ---------------------------------------------------------------------------
# controls check-tool
# ---------------------------------------------------------------------------


def test_check_tool_allowed_exits_zero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _setup_valid_matrix(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = main(["controls", "check-tool", "--task", "AAV-0001", "--tool", "read_file"])
    assert result == 0


def test_check_tool_forbidden_exits_nonzero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _setup_valid_matrix(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = main(["controls", "check-tool", "--task", "AAV-0001", "--tool", "deploy_production"])
    assert result != 0


def test_check_tool_gated_exits_nonzero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _setup_valid_matrix(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = main(["controls", "check-tool", "--task", "AAV-0001", "--tool", "shell_exec"])
    assert result != 0


def test_check_tool_json_output_has_decision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    _setup_valid_matrix(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["controls", "check-tool", "--task", "AAV-0001", "--tool", "read_file", "--json"])
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert "decision" in parsed
    assert "control_id" in parsed


# ---------------------------------------------------------------------------
# controls check-model
# ---------------------------------------------------------------------------


def test_check_model_allowed_exits_zero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _setup_valid_matrix(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = main(
        [
            "controls",
            "check-model",
            "--task",
            "AAV-0001",
            "--vendor",
            "acme-ai",
            "--model",
            "acme-model-v1",
            "--data-class",
            "internal",
        ]
    )
    assert result == 0


def test_check_model_wrong_vendor_exits_nonzero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _setup_valid_matrix(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = main(
        [
            "controls",
            "check-model",
            "--task",
            "AAV-0001",
            "--vendor",
            "rival-ai",
            "--model",
            "rival-model",
            "--data-class",
            "internal",
        ]
    )
    assert result != 0


# ---------------------------------------------------------------------------
# controls check-cost
# ---------------------------------------------------------------------------


def test_check_cost_within_limits_exits_zero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _setup_valid_matrix(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = main(
        [
            "controls",
            "check-cost",
            "--task",
            "AAV-0001",
            "--run-cost",
            "1.0",
            "--daily-cost",
            "10.0",
        ]
    )
    assert result == 0


def test_check_cost_over_limit_exits_nonzero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _setup_valid_matrix(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = main(
        [
            "controls",
            "check-cost",
            "--task",
            "AAV-0001",
            "--run-cost",
            "5.0",
            "--daily-cost",
            "10.0",
        ]
    )
    assert result != 0
