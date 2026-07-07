"""Source map for the OpenWiki knowledge layer.

Builds a reverse index from source file/directory patterns declared in each
wiki page's front-matter (`sources:`) back to the pages that document them,
so that changes to a source path can be traced to the wiki page(s) that
should be refreshed.
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
class SourceMap:
    """Reverse index of source path -> wiki pages that reference it."""

    schema_version: str = constants.SCHEMA_VERSION
    generated_at: str = ""
    # page path -> list of declared source patterns
    page_sources: dict[str, list[str]] = field(default_factory=dict)
    # source pattern -> list of page paths that declare it
    source_pages: dict[str, list[str]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "page_sources": self.page_sources,
            "source_pages": self.source_pages,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SourceMap:
        return cls(
            schema_version=data.get("schema_version", constants.SCHEMA_VERSION),
            generated_at=data.get("generated_at", ""),
            page_sources=dict(data.get("page_sources", {})),
            source_pages=dict(data.get("source_pages", {})),
        )

    def pages_for_source(self, source_path: str) -> list[str]:
        """Return wiki pages that declare a source pattern matching a path.

        Matching is prefix-based: a declared source of `src/agilev/wiki`
        matches a changed file `src/agilev/wiki/cli.py`.
        """
        matches: set[str] = set()
        for pattern, pages in self.source_pages.items():
            if source_path == pattern or source_path.startswith(pattern.rstrip("/") + "/"):
                matches.update(pages)
        return sorted(matches)


def source_map_path(repo_root: Path) -> Path:
    return repo_root / constants.STATE_DIR / constants.SOURCE_MAP_FILENAME


def load_source_map(repo_root: Path) -> SourceMap | None:
    path = source_map_path(repo_root)
    if not path.exists():
        return None
    return SourceMap.from_dict(json.loads(path.read_text(encoding="utf-8")))


def save_source_map(repo_root: Path, source_map: SourceMap) -> Path:
    path = source_map_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(source_map.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return path


def build_source_map(manifest: WikiManifest) -> SourceMap:
    """Build a source map from a manifest's per-page declared sources."""
    page_sources: dict[str, list[str]] = {}
    source_pages: dict[str, list[str]] = {}

    for page_path, entry in sorted(manifest.pages.items()):
        page_sources[page_path] = list(entry.sources)
        for source in entry.sources:
            source_pages.setdefault(source, [])
            if page_path not in source_pages[source]:
                source_pages[source].append(page_path)

    return SourceMap(
        generated_at=datetime.now(UTC).isoformat(),
        page_sources=page_sources,
        source_pages=source_pages,
    )
