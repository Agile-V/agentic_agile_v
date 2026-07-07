"""Tests for agilev.wiki.validator."""

from __future__ import annotations

from pathlib import Path

from agilev.wiki.manifest import build_manifest, save_manifest
from agilev.wiki.scaffolder import scaffold_wiki
from agilev.wiki.validator import validate


def test_validate_missing_wiki_dir_fails(tmp_path: Path) -> None:
    result = validate(tmp_path)
    assert result.passed is False
    assert any("does not exist" in e for e in result.errors)


def test_validate_missing_required_page_fails(tmp_path: Path) -> None:
    scaffold_wiki(tmp_path)
    manifest = build_manifest(tmp_path)
    save_manifest(tmp_path, manifest)

    # Delete a required page after scaffolding + recording the manifest.
    (tmp_path / "openwiki" / "README.md").unlink()

    result = validate(tmp_path)
    assert result.passed is False
    assert any("README.md" in e for e in result.errors)


def test_validate_passes_after_scaffold_and_update(tmp_path: Path) -> None:
    scaffold_wiki(tmp_path)
    manifest = build_manifest(tmp_path)
    save_manifest(tmp_path, manifest)

    result = validate(tmp_path)
    assert result.passed is True
    assert result.errors == []


def test_validate_fails_when_manifest_out_of_sync(tmp_path: Path) -> None:
    scaffold_wiki(tmp_path)
    manifest = build_manifest(tmp_path)
    save_manifest(tmp_path, manifest)

    # Edit a page after the manifest was saved without re-running update.
    readme = tmp_path / "openwiki" / "README.md"
    readme.write_text(readme.read_text(encoding="utf-8") + "\nExtra edit.\n", encoding="utf-8")

    result = validate(tmp_path)
    assert result.passed is False
    assert any("Manifest out of date" in e for e in result.errors)


def test_validate_warns_but_passes_on_missing_manifest(tmp_path: Path) -> None:
    scaffold_wiki(tmp_path)

    result = validate(tmp_path)
    assert result.passed is True
    assert any("No manifest found" in w for w in result.warnings)


def test_validate_required_pages_scale_with_detected_domains(tmp_path: Path) -> None:
    (tmp_path / "src/agilev/pcb").mkdir(parents=True)
    scaffold_wiki(tmp_path)
    manifest = build_manifest(tmp_path)
    save_manifest(tmp_path, manifest)

    result = validate(tmp_path)
    assert "domains/pcb.md" in result.required_pages
    assert result.passed is True
