"""CLI smoke tests for `agilev wiki *` subcommands."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agilev.cli import main


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_wiki_help_lists_subcommand(capsys: pytest.CaptureFixture) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "wiki" in out


def test_wiki_init_scaffolds_and_exits_zero(repo: Path) -> None:
    exit_code = main(["wiki", "init"])
    assert exit_code == 0
    assert (repo / "openwiki" / "README.md").exists()
    assert (repo / ".agile-v" / "wiki" / "manifest.json").exists()


def test_wiki_validate_passes_after_init(repo: Path) -> None:
    assert main(["wiki", "init"]) == 0
    assert main(["wiki", "validate"]) == 0


def test_wiki_validate_fails_before_init(repo: Path) -> None:
    assert main(["wiki", "validate"]) == 1


def test_wiki_status_json_output(repo: Path, capsys: pytest.CaptureFixture) -> None:
    main(["wiki", "init"])
    capsys.readouterr()  # discard init output

    exit_code = main(["wiki", "status", "--json"])
    out = capsys.readouterr().out
    data = json.loads(out)

    assert exit_code == 0
    assert data["initialized"] is True
    assert data["validation_passed"] is True


def test_wiki_update_recomputes_manifest(repo: Path) -> None:
    main(["wiki", "init"])
    exit_code = main(["wiki", "update"])
    assert exit_code == 0
    assert (repo / ".agile-v" / "wiki" / "source_map.json").exists()
    assert (repo / ".agile-v" / "wiki" / "freshness.json").exists()


def test_wiki_snapshot_writes_evidence(repo: Path) -> None:
    main(["wiki", "init"])

    task_dir = repo / ".agentic-agile-v" / "tasks" / "AAV-0001"
    task_dir.mkdir(parents=True)
    (task_dir / "evidence.json").write_text(json.dumps({"task_id": "AAV-0001"}), encoding="utf-8")

    exit_code = main(["wiki", "snapshot", "--task", "AAV-0001"])
    assert exit_code == 0

    bundle = json.loads((task_dir / "evidence.json").read_text(encoding="utf-8"))
    assert "knowledge_snapshot" in bundle


def test_wiki_snapshot_missing_task_fails(repo: Path) -> None:
    main(["wiki", "init"])
    exit_code = main(["wiki", "snapshot", "--task", "AAV-9999"])
    assert exit_code == 1
