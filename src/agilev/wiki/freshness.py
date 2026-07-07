"""Freshness tracking for the OpenWiki knowledge layer.

Compares each wiki page's declared source paths against the manifest's
`generated_at` timestamp to determine whether the page may be out of date
relative to the code/config it documents.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from agilev.wiki import constants
from agilev.wiki.manifest import WikiManifest


@dataclass
class PageFreshness:
    """Freshness result for a single wiki page."""

    path: str
    stale: bool
    stale_sources: list[str] = field(default_factory=list)
    missing_sources: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "stale": self.stale,
            "stale_sources": self.stale_sources,
            "missing_sources": self.missing_sources,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PageFreshness:
        return cls(
            path=data["path"],
            stale=data.get("stale", False),
            stale_sources=list(data.get("stale_sources", [])),
            missing_sources=list(data.get("missing_sources", [])),
        )


@dataclass
class FreshnessReport:
    """Freshness report across all wiki pages."""

    schema_version: str = constants.SCHEMA_VERSION
    generated_at: str = ""
    manifest_generated_at: str = ""
    pages: dict[str, PageFreshness] = field(default_factory=dict)

    @property
    def stale_pages(self) -> list[str]:
        return sorted(p for p, f in self.pages.items() if f.stale)

    @property
    def is_fresh(self) -> bool:
        return len(self.stale_pages) == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "manifest_generated_at": self.manifest_generated_at,
            "pages": {path: f.to_dict() for path, f in self.pages.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FreshnessReport:
        pages = {
            path: PageFreshness.from_dict(entry) for path, entry in data.get("pages", {}).items()
        }
        return cls(
            schema_version=data.get("schema_version", constants.SCHEMA_VERSION),
            generated_at=data.get("generated_at", ""),
            manifest_generated_at=data.get("manifest_generated_at", ""),
            pages=pages,
        )


def freshness_path(repo_root: Path) -> Path:
    return repo_root / constants.STATE_DIR / constants.FRESHNESS_FILENAME


def load_freshness(repo_root: Path) -> FreshnessReport | None:
    path = freshness_path(repo_root)
    if not path.exists():
        return None
    return FreshnessReport.from_dict(json.loads(path.read_text(encoding="utf-8")))


def save_freshness(repo_root: Path, report: FreshnessReport) -> Path:
    path = freshness_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return path


def compute_freshness(repo_root: Path, manifest: WikiManifest) -> FreshnessReport:
    """Compute a freshness report by comparing sources against the manifest.

    A page is considered stale if any of its declared source paths (files or
    directories) have a modification time newer than the manifest's
    `generated_at` timestamp, or if a declared source path no longer exists.

    Args:
        repo_root: Repository root directory.
        manifest: The manifest to compare against (baseline snapshot).

    Returns:
        A FreshnessReport describing per-page staleness.
    """
    manifest_time = _parse_iso(manifest.generated_at)
    pages: dict[str, PageFreshness] = {}

    for page_path, entry in sorted(manifest.pages.items()):
        stale_sources: list[str] = []
        missing_sources: list[str] = []

        for source in entry.sources:
            source_path = repo_root / source
            if not source_path.exists():
                missing_sources.append(source)
                continue

            newest_mtime = _newest_mtime(source_path)
            if manifest_time is not None and newest_mtime is not None:
                newest_dt = datetime.fromtimestamp(newest_mtime, tz=UTC)
                if newest_dt > manifest_time:
                    stale_sources.append(source)

        pages[page_path] = PageFreshness(
            path=page_path,
            stale=bool(stale_sources) or bool(missing_sources),
            stale_sources=stale_sources,
            missing_sources=missing_sources,
        )

    return FreshnessReport(
        generated_at=datetime.now(UTC).isoformat(),
        manifest_generated_at=manifest.generated_at,
        pages=pages,
    )


def _parse_iso(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _newest_mtime(path: Path) -> float | None:
    if path.is_file():
        return path.stat().st_mtime
    if path.is_dir():
        mtimes = [f.stat().st_mtime for f in path.rglob("*") if f.is_file()]
        return max(mtimes) if mtimes else None
    return None
