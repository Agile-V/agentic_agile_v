"""Tests for agilev.wiki.source_map."""

from __future__ import annotations

from pathlib import Path

from agilev.wiki.manifest import WikiManifest, WikiPageEntry
from agilev.wiki.source_map import (
    build_source_map,
    load_source_map,
    save_source_map,
    source_map_path,
)


def _manifest_with_sources() -> WikiManifest:
    return WikiManifest(
        generated_at="2026-01-01T00:00:00+00:00",
        pages={
            "domains/software.md": WikiPageEntry(
                path="domains/software.md",
                title="Software",
                sha256="sha256:a",
                sources=["src/agilev/cli.py", "src/agilev/state.py"],
            ),
            "domains/pcb.md": WikiPageEntry(
                path="domains/pcb.md",
                title="PCB",
                sha256="sha256:b",
                sources=["src/agilev/pcb"],
            ),
        },
    )


def test_build_source_map_reverse_index() -> None:
    manifest = _manifest_with_sources()
    source_map = build_source_map(manifest)

    assert source_map.page_sources["domains/software.md"] == [
        "src/agilev/cli.py",
        "src/agilev/state.py",
    ]
    assert source_map.source_pages["src/agilev/pcb"] == ["domains/pcb.md"]


def test_pages_for_source_exact_match() -> None:
    manifest = _manifest_with_sources()
    source_map = build_source_map(manifest)

    assert source_map.pages_for_source("src/agilev/cli.py") == ["domains/software.md"]


def test_pages_for_source_directory_prefix_match() -> None:
    manifest = _manifest_with_sources()
    source_map = build_source_map(manifest)

    assert source_map.pages_for_source("src/agilev/pcb/circuit_ir.py") == ["domains/pcb.md"]


def test_pages_for_source_no_match_returns_empty() -> None:
    manifest = _manifest_with_sources()
    source_map = build_source_map(manifest)

    assert source_map.pages_for_source("unrelated/file.py") == []


def test_source_map_round_trip(tmp_path: Path) -> None:
    manifest = _manifest_with_sources()
    source_map = build_source_map(manifest)

    path = save_source_map(tmp_path, source_map)
    assert path == source_map_path(tmp_path)

    loaded = load_source_map(tmp_path)
    assert loaded is not None
    assert loaded.page_sources == source_map.page_sources
    assert loaded.source_pages == source_map.source_pages


def test_load_source_map_missing_returns_none(tmp_path: Path) -> None:
    assert load_source_map(tmp_path) is None
