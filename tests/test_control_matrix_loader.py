"""Unit tests for ControlMatrix loader and semantic validator.

Implements: REQ-CM-001, REQ-CM-002
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from agilev.control_matrix import ControlMatrix, ControlMatrixError

FIXTURES = Path(__file__).parent / "fixtures"


def _make_matrix_dir(tmp_path: Path, fixture_name: str, location: str = "config") -> Path:
    """Copy a fixture YAML into a temporary project directory."""
    src = FIXTURES / fixture_name
    if location == "config":
        dest_dir = tmp_path / "config"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / "control_matrix.yaml"
    else:
        dest_dir = tmp_path / ".agile-v"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / "CONTROL_MATRIX.yaml"
    shutil.copy(src, dest)
    return tmp_path


# ---------------------------------------------------------------------------
# Load path tests
# ---------------------------------------------------------------------------


def test_loads_from_config_dir(tmp_path: Path):
    _make_matrix_dir(tmp_path, "control_matrix.valid.yaml", location="config")
    matrix = ControlMatrix.load(tmp_path)
    assert "config/control_matrix.yaml" in str(matrix.source_path)


def test_agile_v_dir_takes_precedence(tmp_path: Path):
    _make_matrix_dir(tmp_path, "control_matrix.valid.yaml", location="config")
    _make_matrix_dir(tmp_path, "control_matrix.valid.yaml", location=".agile-v")
    matrix = ControlMatrix.load(tmp_path)
    assert ".agile-v" in str(matrix.source_path)


def test_raises_when_no_matrix(tmp_path: Path):
    with pytest.raises(ControlMatrixError, match="No control matrix found"):
        ControlMatrix.load(tmp_path)


# ---------------------------------------------------------------------------
# Semantic validation tests
# ---------------------------------------------------------------------------


def test_valid_fixture_loads_ok(tmp_path: Path):
    _make_matrix_dir(tmp_path, "control_matrix.valid.yaml")
    matrix = ControlMatrix.load(tmp_path)
    assert matrix.version == "1.0.0"


def test_fails_on_duplicate_ids(tmp_path: Path):
    data = yaml.safe_load((FIXTURES / "control_matrix.valid.yaml").read_text())
    # Duplicate the first control
    data["controls"].append(data["controls"][0].copy())
    matrix_path = tmp_path / "config" / "control_matrix.yaml"
    matrix_path.parent.mkdir(parents=True)
    matrix_path.write_text(yaml.dump(data))
    with pytest.raises(ControlMatrixError, match="Duplicate control id"):
        ControlMatrix.load(tmp_path)


def test_fails_on_tbd_owner_for_active_control(tmp_path: Path):
    _make_matrix_dir(tmp_path, "control_matrix.invalid_missing_owner.yaml")
    with pytest.raises(ControlMatrixError, match="unresolved owner"):
        ControlMatrix.load(tmp_path)


def test_fails_on_allowed_forbidden_overlap(tmp_path: Path):
    _make_matrix_dir(tmp_path, "control_matrix.invalid_forbidden_tool.yaml")
    with pytest.raises(ControlMatrixError, match="overlapping tools"):
        ControlMatrix.load(tmp_path)


def test_draft_control_passes_with_tbd_owners(tmp_path: Path):
    """Draft controls may contain TBD placeholders without raising."""
    data = yaml.safe_load((FIXTURES / "control_matrix.invalid_missing_owner.yaml").read_text())
    data["controls"][0]["status"] = "draft"
    matrix_path = tmp_path / "config" / "control_matrix.yaml"
    matrix_path.parent.mkdir(parents=True)
    matrix_path.write_text(yaml.dump(data))
    matrix = ControlMatrix.load(tmp_path)  # should not raise
    assert matrix.data["controls"][0]["status"] == "draft"


# ---------------------------------------------------------------------------
# Resolve tests
# ---------------------------------------------------------------------------


def test_resolve_default_task(tmp_path: Path):
    _make_matrix_dir(tmp_path, "control_matrix.valid.yaml")
    matrix = ControlMatrix.load(tmp_path)
    control = matrix.resolve(task_type="feature", risk_level="L1", agent_mode="builder")
    assert control["id"] == "cm-test-valid"


def test_resolve_wildcard_skill(tmp_path: Path):
    _make_matrix_dir(tmp_path, "control_matrix.valid.yaml")
    matrix = ControlMatrix.load(tmp_path)
    control = matrix.resolve(
        task_type="feature", risk_level="L1", agent_mode="builder", skill="any-skill"
    )
    assert control["id"] == "cm-test-valid"


def test_resolve_raises_when_no_match(tmp_path: Path):
    _make_matrix_dir(tmp_path, "control_matrix.valid.yaml")
    matrix = ControlMatrix.load(tmp_path)
    with pytest.raises(ControlMatrixError, match="No matching active control"):
        # Use a UUID task type guaranteed not to be in any applies_to list
        matrix.resolve(
            task_type="00000000-0000-0000-0000-task-nonexistent",
            risk_level="L4",
            agent_mode="builder",
        )


def test_resolve_l0_below_l1_minimum_raises(tmp_path: Path):
    """L0 risk level is below minimum_risk_level=L1 and must not match."""
    _make_matrix_dir(tmp_path, "control_matrix.valid.yaml")
    matrix = ControlMatrix.load(tmp_path)
    with pytest.raises(ControlMatrixError, match="No matching active control"):
        matrix.resolve(task_type="feature", risk_level="L0", agent_mode="builder")


def test_resolve_warns_on_invalid_risk_level(tmp_path: Path):
    _make_matrix_dir(tmp_path, "control_matrix.valid.yaml")
    matrix = ControlMatrix.load(tmp_path)
    with pytest.warns(UserWarning, match="Unrecognised risk level"):
        with pytest.raises(ControlMatrixError):
            matrix.resolve(task_type="feature", risk_level="INVALID", agent_mode="builder")


def test_summary_contains_version(tmp_path: Path):
    _make_matrix_dir(tmp_path, "control_matrix.valid.yaml")
    matrix = ControlMatrix.load(tmp_path)
    summary = matrix.summary()
    assert "1.0.0" in summary
    assert "1 active" in summary or "control" in summary


def test_default_fail_mode_closed(tmp_path: Path):
    _make_matrix_dir(tmp_path, "control_matrix.valid.yaml")
    matrix = ControlMatrix.load(tmp_path)
    assert matrix.default_fail_mode == "closed"


def test_default_fail_mode_fallback(tmp_path: Path):
    """A matrix without default_fail_mode falls back to 'closed'."""
    data = yaml.safe_load((FIXTURES / "control_matrix.valid.yaml").read_text())
    data.pop("default_fail_mode", None)
    matrix_path = tmp_path / "config" / "control_matrix.yaml"
    matrix_path.parent.mkdir(parents=True)
    matrix_path.write_text(yaml.dump(data))
    matrix = ControlMatrix.load(tmp_path)
    assert matrix.default_fail_mode == "closed"


def test_repr_contains_key_info(tmp_path: Path):
    _make_matrix_dir(tmp_path, "control_matrix.valid.yaml")
    matrix = ControlMatrix.load(tmp_path)
    r = repr(matrix)
    assert "ControlMatrix" in r
    assert "1.0.0" in r


def test_requires_gate_forbidden_overlap_raises(tmp_path: Path):
    data = yaml.safe_load((FIXTURES / "control_matrix.valid.yaml").read_text())
    # Use a tool name that is ONLY in requires_gate and forbidden (not in allowed) to avoid
    # the allowed∩forbidden check firing first
    data["controls"][0]["tools"]["requires_gate"].append("some_unique_tool_xyz")
    data["controls"][0]["tools"]["forbidden"].append("some_unique_tool_xyz")
    matrix_path = tmp_path / "config" / "control_matrix.yaml"
    matrix_path.parent.mkdir(parents=True)
    matrix_path.write_text(yaml.dump(data))
    with pytest.raises(ControlMatrixError, match="requires_gate and forbidden"):
        ControlMatrix.load(tmp_path)


def test_invalid_minimum_risk_level_raises(tmp_path: Path):
    data = yaml.safe_load((FIXTURES / "control_matrix.valid.yaml").read_text())
    data["controls"][0]["minimum_risk_level"] = "L99"
    matrix_path = tmp_path / "config" / "control_matrix.yaml"
    matrix_path.parent.mkdir(parents=True)
    matrix_path.write_text(yaml.dump(data))
    with pytest.raises(ControlMatrixError, match="invalid minimum_risk_level"):
        ControlMatrix.load(tmp_path)


def test_active_control_with_tbd_model_vendor_raises(tmp_path: Path):
    data = yaml.safe_load((FIXTURES / "control_matrix.valid.yaml").read_text())
    data["controls"][0]["model"]["vendor"] = "TBD"
    matrix_path = tmp_path / "config" / "control_matrix.yaml"
    matrix_path.parent.mkdir(parents=True)
    matrix_path.write_text(yaml.dump(data))
    with pytest.raises(ControlMatrixError, match="unresolved model field"):
        ControlMatrix.load(tmp_path)


def test_active_control_with_approved_vendor_placeholder_raises(tmp_path: Path):
    data = yaml.safe_load((FIXTURES / "control_matrix.valid.yaml").read_text())
    data["controls"][0]["model"]["vendor"] = "approved_vendor"
    matrix_path = tmp_path / "config" / "control_matrix.yaml"
    matrix_path.parent.mkdir(parents=True)
    matrix_path.write_text(yaml.dump(data))
    with pytest.raises(ControlMatrixError, match="unresolved model field"):
        ControlMatrix.load(tmp_path)
