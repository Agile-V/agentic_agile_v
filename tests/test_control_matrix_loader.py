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
        # L4 with a task_type not in applies_to
        matrix.resolve(task_type="nonexistent", risk_level="L4", agent_mode="builder")
