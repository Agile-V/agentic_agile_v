"""Tests for agilev.wiki.manifest."""

from __future__ import annotations

from pathlib import Path

from agilev.wiki.manifest import (
    WikiManifest,
    WikiPageEntry,
    build_manifest,
    compute_file_hash,
    load_manifest,
    manifest_path,
    save_manifest,
)


def _write_page(repo_root: Path, rel_path: str, title: str = "Test Page") -> Path:
    page_path = repo_root / "openwiki" / rel_path
    page_path.parent.mkdir(parents=True, exist_ok=True)
    page_path.write_text(
        f"---\ntitle: {title}\nsources:\n  - src/foo.py\nowners:\n  - agile-v-core\n"
        "last_reviewed: null\n---\n\n# Body\n",
        encoding="utf-8",
    )
    return page_path


def test_build_manifest_empty_repo(tmp_path: Path) -> None:
    manifest = build_manifest(tmp_path)
    assert manifest.pages == {}
    assert manifest.generated_at


def test_build_manifest_scans_pages(tmp_path: Path) -> None:
    _write_page(tmp_path, "README.md", title="Repo Knowledge Base")

    manifest = build_manifest(tmp_path)

    assert "README.md" in manifest.pages
    entry = manifest.pages["README.md"]
    assert entry.title == "Repo Knowledge Base"
    assert entry.sources == ["src/foo.py"]
    assert entry.owners == ["agile-v-core"]
    assert entry.sha256.startswith("sha256:")


def test_manifest_round_trip_save_and_load(tmp_path: Path) -> None:
    _write_page(tmp_path, "README.md")
    manifest = build_manifest(tmp_path)

    path = save_manifest(tmp_path, manifest)
    assert path == manifest_path(tmp_path)
    assert path.exists()

    loaded = load_manifest(tmp_path)
    assert loaded is not None
    assert loaded.pages.keys() == manifest.pages.keys()
    assert loaded.pages["README.md"].sha256 == manifest.pages["README.md"].sha256


def test_load_manifest_missing_returns_none(tmp_path: Path) -> None:
    assert load_manifest(tmp_path) is None


def test_compute_file_hash_deterministic(tmp_path: Path) -> None:
    f = tmp_path / "a.txt"
    f.write_text("hello", encoding="utf-8")
    h1 = compute_file_hash(f)
    h2 = compute_file_hash(f)
    assert h1 == h2
    assert h1.startswith("sha256:")


def test_wiki_page_entry_dict_round_trip() -> None:
    entry = WikiPageEntry(
        path="README.md", title="Title", sha256="sha256:abc", sources=["a"], owners=["b"]
    )
    restored = WikiPageEntry.from_dict(entry.to_dict())
    assert restored == entry


def test_wiki_manifest_dict_round_trip() -> None:
    manifest = WikiManifest(
        generated_at="2026-01-01T00:00:00+00:00",
        pages={"a.md": WikiPageEntry(path="a.md", title="A", sha256="sha256:x")},
    )
    restored = WikiManifest.from_dict(manifest.to_dict())
    assert restored.pages.keys() == manifest.pages.keys()
    assert restored.generated_at == manifest.generated_at
