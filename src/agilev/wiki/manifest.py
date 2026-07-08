"""Manifest tracking for the OpenWiki knowledge layer.

The manifest is Agile-V's own record of what `openwiki/` looked like the
last time it was scanned: one entry per page, with its content hash,
declared sources, and title. It is the baseline that `freshness.py` compares
the live repository against.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from agilev.wiki import constants
from agilev.wiki.frontmatter import parse_frontmatter


@dataclass
class WikiPageEntry:
    """Manifest entry for a single wiki page."""

    path: str
    title: str
    sha256: str
    sources: list[str] = field(default_factory=list)
    owners: list[str] = field(default_factory=list)
    last_reviewed: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "title": self.title,
            "sha256": self.sha256,
            "sources": self.sources,
            "owners": self.owners,
            "last_reviewed": self.last_reviewed,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WikiPageEntry:
        return cls(
            path=data["path"],
            title=data.get("title", ""),
            sha256=data.get("sha256", ""),
            sources=list(data.get("sources", [])),
            owners=list(data.get("owners", [])),
            last_reviewed=data.get("last_reviewed"),
        )


@dataclass
class WikiManifest:
    """Snapshot of the `openwiki/` tree as last scanned by Agile-V."""

    schema_version: str = constants.SCHEMA_VERSION
    generated_at: str = ""
    repo_commit: str | None = None
    pages: dict[str, WikiPageEntry] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "repo_commit": self.repo_commit,
            "pages": {path: entry.to_dict() for path, entry in self.pages.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WikiManifest:
        pages = {
            path: WikiPageEntry.from_dict(entry) for path, entry in data.get("pages", {}).items()
        }
        return cls(
            schema_version=data.get("schema_version", constants.SCHEMA_VERSION),
            generated_at=data.get("generated_at", ""),
            repo_commit=data.get("repo_commit"),
            pages=pages,
        )


def manifest_path(repo_root: Path) -> Path:
    return repo_root / constants.STATE_DIR / constants.MANIFEST_FILENAME


def load_manifest(repo_root: Path) -> WikiManifest | None:
    """Load the manifest from `.agile-v/wiki/manifest.json`, if present."""
    path = manifest_path(repo_root)
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return WikiManifest.from_dict(data)


def save_manifest(repo_root: Path, manifest: WikiManifest) -> Path:
    """Save the manifest to `.agile-v/wiki/manifest.json`."""
    path = manifest_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return path


def compute_file_hash(path: Path) -> str:
    """Compute a `sha256:<hex>` hash of a file's contents."""
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return f"sha256:{digest.hexdigest()}"


def build_manifest(repo_root: Path, repo_commit: str | None = None) -> WikiManifest:
    """Scan `openwiki/` and build a fresh manifest from what's on disk.

    Args:
        repo_root: Repository root directory.
        repo_commit: Optional git commit hash to record for provenance.

    Returns:
        A new WikiManifest reflecting the current state of `openwiki/`.
    """
    wiki_dir = repo_root / constants.WIKI_DIR
    pages: dict[str, WikiPageEntry] = {}

    if wiki_dir.exists():
        for md_file in sorted(wiki_dir.rglob("*.md")):
            rel_path = md_file.relative_to(wiki_dir).as_posix()
            text = md_file.read_text(encoding="utf-8")
            front_matter, _ = parse_frontmatter(text)

            pages[rel_path] = WikiPageEntry(
                path=rel_path,
                title=front_matter.get("title", rel_path),
                sha256=compute_file_hash(md_file),
                sources=list(front_matter.get("sources", []) or []),
                owners=list(front_matter.get("owners", []) or []),
                last_reviewed=front_matter.get("last_reviewed"),
            )

    return WikiManifest(
        generated_at=datetime.now(UTC).isoformat(),
        repo_commit=repo_commit,
        pages=pages,
    )
