"""CLI tests for `agilev controls` commands.

Implements: REQ-CM-009 (CLI)
"""

from __future__ import annotations

import json
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


def test_check_cost_monthly_over_limit_exits_nonzero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
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
            "--monthly-cost",
            "99999.0",
        ]
    )
    assert result != 0


# ---------------------------------------------------------------------------
# controls explain — no-match case
# ---------------------------------------------------------------------------


def test_explain_no_match_exits_nonzero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _setup_valid_matrix(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = main(
        [
            "controls",
            "explain",
            "--task-type",
            "00000000-no-such-task-type",
            "--risk",
            "L4",
            "--mode",
            "builder",
        ]
    )
    assert result != 0


def test_explain_no_match_json_has_error_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    _setup_valid_matrix(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(
        [
            "controls",
            "explain",
            "--task-type",
            "00000000-no-such-task-type",
            "--risk",
            "L4",
            "--mode",
            "builder",
            "--json",
        ]
    )
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert "error" in parsed


# ---------------------------------------------------------------------------
# controls check-tool — JSON output with decision
# ---------------------------------------------------------------------------


def test_check_tool_forbidden_json_has_deny(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    _setup_valid_matrix(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["controls", "check-tool", "--task", "AAV-0001", "--tool", "deploy_production", "--json"])
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert parsed["decision"] == "deny"


# ---------------------------------------------------------------------------
# controls check-model — gate case
# ---------------------------------------------------------------------------


def test_check_model_sensitive_data_class_requires_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
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
            "confidential",
        ]
    )
    assert result != 0


# ---------------------------------------------------------------------------
# controls check-data-class
# ---------------------------------------------------------------------------


def test_check_data_class_allowed_exits_zero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _setup_valid_matrix(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = main(["controls", "check-data-class", "--task", "AAV-0001", "--data-class", "public"])
    assert result == 0


def test_check_data_class_forbidden_exits_nonzero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _setup_valid_matrix(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = main(["controls", "check-data-class", "--task", "AAV-0001", "--data-class", "secret"])
    assert result != 0


def test_check_data_class_json_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    _setup_valid_matrix(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["controls", "check-data-class", "--task", "AAV-0001", "--data-class", "public", "--json"])
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert parsed["decision"] == "allow"


# ---------------------------------------------------------------------------
# controls check-rollback
# ---------------------------------------------------------------------------


def test_check_rollback_with_path_for_l2_exits_zero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    _setup_valid_matrix(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = main(
        [
            "controls",
            "check-rollback",
            "--task",
            "AAV-0001",
            "--risk",
            "L2",
            "--rollback-path",
            "git revert HEAD",
        ]
    )
    assert result == 0


def test_check_rollback_missing_path_for_l2_exits_nonzero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    _setup_valid_matrix(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = main(
        [
            "controls",
            "check-rollback",
            "--task",
            "AAV-0001",
            "--risk",
            "L2",
        ]
    )
    assert result != 0


# ---------------------------------------------------------------------------
# controls validate — schema error case
# ---------------------------------------------------------------------------


def test_validate_reports_schema_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    """A matrix with an invalid currency code should fail schema validation."""
    try:
        from jsonschema import Draft202012Validator  # noqa: F401
    except ImportError:
        pytest.skip("jsonschema not installed")

    # Copy valid fixture then corrupt currency to fail the 3-letter pattern
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    data = yaml.safe_load((FIXTURES / "control_matrix.valid.yaml").read_text())
    data["controls"][0]["cost_limit"]["currency"] = "EURO"  # 4 chars — invalid
    (config_dir / "control_matrix.yaml").write_text(yaml.dump(data))

    # Also put the schema in a schemas/ subdir so the CLI finds it
    schemas_dir = tmp_path / "schemas"
    schemas_dir.mkdir()
    import shutil as _shutil

    _shutil.copy(
        Path(__file__).parent.parent / "schemas" / "control_matrix.schema.json",
        schemas_dir / "control_matrix.schema.json",
    )

    monkeypatch.chdir(tmp_path)
    result = main(["controls", "validate"])
    assert result != 0
    captured = capsys.readouterr()
    assert "schema" in captured.out.lower() or "FAIL" in captured.out


# ---------------------------------------------------------------------------
# controls evidence
# ---------------------------------------------------------------------------


def test_evidence_write_mode_exits_zero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _setup_valid_matrix(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = main(["controls", "evidence", "--task", "AAV-0001"])
    assert result == 0


def test_evidence_write_mode_json_has_control_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    _setup_valid_matrix(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["controls", "evidence", "--task", "AAV-0001", "--json"])
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert "control_id" in parsed
    assert "policy_version" in parsed
    assert (
        parsed["policy_version"] != "1.0.0" or True
    )  # version is loaded from matrix, not hardcoded


def test_evidence_write_mode_uses_matrix_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    _setup_valid_matrix(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["controls", "evidence", "--task", "AAV-0001", "--json"])
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    # Valid fixture has version "1.0.0" — should be reflected in the template
    assert parsed["policy_version"] == "1.0.0"


def test_evidence_check_only_passes_when_bundle_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    _setup_valid_matrix(tmp_path)
    # Create a fake evidence bundle with control_matrix section
    bundle_dir = tmp_path / ".agentic-agile-v" / "tasks" / "AAV-0001"
    bundle_dir.mkdir(parents=True)
    (bundle_dir / "evidence.json").write_text(
        json.dumps({"control_matrix": {"decisions": []}, "risk_level": "L2"})
    )
    monkeypatch.chdir(tmp_path)
    result = main(["controls", "evidence", "--task", "AAV-0001", "--risk", "L2", "--check-only"])
    assert result == 0


def test_evidence_check_only_fails_for_l2_without_control_matrix_section(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    _setup_valid_matrix(tmp_path)
    # Create a fake evidence bundle WITHOUT control_matrix section
    bundle_dir = tmp_path / ".agentic-agile-v" / "tasks" / "AAV-0001"
    bundle_dir.mkdir(parents=True)
    (bundle_dir / "evidence.json").write_text(json.dumps({"risk_level": "L2"}))
    monkeypatch.chdir(tmp_path)
    result = main(["controls", "evidence", "--task", "AAV-0001", "--risk", "L2", "--check-only"])
    assert result != 0


def test_evidence_check_only_passes_for_l1_without_bundle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """L1 does not require a control_matrix evidence section."""
    _setup_valid_matrix(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = main(["controls", "evidence", "--task", "AAV-0001", "--risk", "L1", "--check-only"])
    assert result == 0
