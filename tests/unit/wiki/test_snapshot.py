"""Tests for agilev.wiki.snapshot."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agilev.wiki.manifest import build_manifest, save_manifest
from agilev.wiki.scaffolder import scaffold_wiki
from agilev.wiki.snapshot import (
    build_knowledge_snapshot,
    find_evidence_file,
    write_snapshot_to_task,
)


def _init_wiki(repo_root: Path) -> None:
    scaffold_wiki(repo_root)
    manifest = build_manifest(repo_root)
    save_manifest(repo_root, manifest)


def test_build_knowledge_snapshot_reports_pass(tmp_path: Path) -> None:
    _init_wiki(tmp_path)

    snapshot = build_knowledge_snapshot(tmp_path)

    assert snapshot["validation_passed"] is True
    assert snapshot["page_count"] > 0
    assert snapshot["wiki_dir"] == "openwiki"


def test_build_knowledge_snapshot_reports_fail_when_page_missing(tmp_path: Path) -> None:
    _init_wiki(tmp_path)
    (tmp_path / "openwiki" / "README.md").unlink()

    snapshot = build_knowledge_snapshot(tmp_path)

    assert snapshot["validation_passed"] is False
    assert any("README.md" in e for e in snapshot["validation_errors"])


def test_find_evidence_file_prefers_bundle(tmp_path: Path) -> None:
    task_dir = tmp_path / "task"
    task_dir.mkdir()
    (task_dir / "evidence.json").write_text("{}", encoding="utf-8")
    (task_dir / "evidence_bundle.json").write_text("{}", encoding="utf-8")

    assert find_evidence_file(task_dir).name == "evidence_bundle.json"


def test_find_evidence_file_falls_back_to_evidence_json(tmp_path: Path) -> None:
    task_dir = tmp_path / "task"
    task_dir.mkdir()
    (task_dir / "evidence.json").write_text("{}", encoding="utf-8")

    assert find_evidence_file(task_dir).name == "evidence.json"


def test_write_snapshot_to_task_merges_into_existing_evidence(tmp_path: Path) -> None:
    _init_wiki(tmp_path)

    task_dir = tmp_path / ".agentic-agile-v" / "tasks" / "AAV-0001"
    task_dir.mkdir(parents=True)
    evidence_path = task_dir / "evidence.json"
    evidence_path.write_text(json.dumps({"task_id": "AAV-0001", "changed_files": []}), "utf-8")

    result_path = write_snapshot_to_task(tmp_path, "AAV-0001")

    assert result_path == evidence_path
    bundle = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert bundle["task_id"] == "AAV-0001"
    assert "knowledge_snapshot" in bundle
    assert bundle["knowledge_snapshot"]["validation_passed"] is True


def test_write_snapshot_to_task_missing_task_raises(tmp_path: Path) -> None:
    _init_wiki(tmp_path)
    with pytest.raises(FileNotFoundError):
        write_snapshot_to_task(tmp_path, "AAV-9999")
