"""Tests for agilev.wiki.freshness."""

from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

from agilev.wiki.freshness import (
    compute_freshness,
    freshness_path,
    load_freshness,
    save_freshness,
)
from agilev.wiki.manifest import WikiManifest, WikiPageEntry


def test_compute_freshness_no_sources_is_fresh(tmp_path: Path) -> None:
    manifest = WikiManifest(
        generated_at=datetime.now(UTC).isoformat(),
        pages={"README.md": WikiPageEntry(path="README.md", title="R", sha256="sha256:a")},
    )
    report = compute_freshness(tmp_path, manifest)
    assert report.is_fresh
    assert report.stale_pages == []


def test_compute_freshness_detects_stale_source(tmp_path: Path) -> None:
    src = tmp_path / "src" / "foo.py"
    src.parent.mkdir(parents=True)
    src.write_text("x = 1\n", encoding="utf-8")

    # Manifest generated in the past, before the source file's mtime.
    past = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    manifest = WikiManifest(
        generated_at=past,
        pages={
            "domains/software.md": WikiPageEntry(
                path="domains/software.md",
                title="Software",
                sha256="sha256:a",
                sources=["src/foo.py"],
            )
        },
    )

    report = compute_freshness(tmp_path, manifest)

    assert not report.is_fresh
    assert "domains/software.md" in report.stale_pages
    assert "src/foo.py" in report.pages["domains/software.md"].stale_sources


def test_compute_freshness_source_newer_than_manifest_is_not_stale(tmp_path: Path) -> None:
    src = tmp_path / "src" / "foo.py"
    src.parent.mkdir(parents=True)
    src.write_text("x = 1\n", encoding="utf-8")

    # Manifest generated after the source file existed -> not stale.
    time.sleep(0.01)
    future = datetime.now(UTC).isoformat()
    manifest = WikiManifest(
        generated_at=future,
        pages={
            "domains/software.md": WikiPageEntry(
                path="domains/software.md",
                title="Software",
                sha256="sha256:a",
                sources=["src/foo.py"],
            )
        },
    )

    report = compute_freshness(tmp_path, manifest)
    assert report.is_fresh


def test_compute_freshness_missing_source_flagged(tmp_path: Path) -> None:
    manifest = WikiManifest(
        generated_at=datetime.now(UTC).isoformat(),
        pages={
            "domains/software.md": WikiPageEntry(
                path="domains/software.md",
                title="Software",
                sha256="sha256:a",
                sources=["src/does_not_exist.py"],
            )
        },
    )
    report = compute_freshness(tmp_path, manifest)
    assert not report.is_fresh
    assert "src/does_not_exist.py" in report.pages["domains/software.md"].missing_sources


def test_freshness_round_trip(tmp_path: Path) -> None:
    manifest = WikiManifest(
        generated_at=datetime.now(UTC).isoformat(),
        pages={"README.md": WikiPageEntry(path="README.md", title="R", sha256="sha256:a")},
    )
    report = compute_freshness(tmp_path, manifest)

    path = save_freshness(tmp_path, report)
    assert path == freshness_path(tmp_path)

    loaded = load_freshness(tmp_path)
    assert loaded is not None
    assert loaded.is_fresh == report.is_fresh


def test_load_freshness_missing_returns_none(tmp_path: Path) -> None:
    assert load_freshness(tmp_path) is None


def test_compute_freshness_directory_source(tmp_path: Path) -> None:
    src_dir = tmp_path / "src" / "agilev" / "pcb"
    src_dir.mkdir(parents=True)
    (src_dir / "a.py").write_text("a = 1\n", encoding="utf-8")

    past = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    manifest = WikiManifest(
        generated_at=past,
        pages={
            "domains/pcb.md": WikiPageEntry(
                path="domains/pcb.md",
                title="PCB",
                sha256="sha256:a",
                sources=["src/agilev/pcb"],
            )
        },
    )

    report = compute_freshness(tmp_path, manifest)
    assert not report.is_fresh
    assert "src/agilev/pcb" in report.pages["domains/pcb.md"].stale_sources
