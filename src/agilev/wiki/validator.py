"""Validation for the OpenWiki knowledge layer.

`agilev wiki validate` fails (non-zero exit) only on structural problems:
missing required pages, or a manifest that no longer matches what's on disk
(meaning `agilev wiki update` was not run after `openwiki/` changed).
Staleness relative to source code (see `freshness.py`) is reported as a
warning only, since editing code between OpenWiki refresh cycles is normal.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from agilev.wiki import constants, domains
from agilev.wiki.freshness import compute_freshness
from agilev.wiki.manifest import WikiManifest, build_manifest, compute_file_hash, load_manifest


@dataclass
class WikiValidationResult:
    """Result of validating the `openwiki/` tree against Agile-V rules."""

    schema_version: str = constants.SCHEMA_VERSION
    generated_at: str = ""
    passed: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    required_pages: list[str] = field(default_factory=list)
    stale_pages: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "passed": self.passed,
            "errors": self.errors,
            "warnings": self.warnings,
            "required_pages": self.required_pages,
            "stale_pages": self.stale_pages,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WikiValidationResult:
        return cls(
            schema_version=data.get("schema_version", constants.SCHEMA_VERSION),
            generated_at=data.get("generated_at", ""),
            passed=data.get("passed", True),
            errors=list(data.get("errors", [])),
            warnings=list(data.get("warnings", [])),
            required_pages=list(data.get("required_pages", [])),
            stale_pages=list(data.get("stale_pages", [])),
        )


def validation_path(repo_root: Path) -> Path:
    return repo_root / constants.STATE_DIR / constants.VALIDATION_FILENAME


def load_validation(repo_root: Path) -> WikiValidationResult | None:
    path = validation_path(repo_root)
    if not path.exists():
        return None
    return WikiValidationResult.from_dict(json.loads(path.read_text(encoding="utf-8")))


def save_validation(repo_root: Path, result: WikiValidationResult) -> Path:
    path = validation_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return path


def validate(repo_root: Path) -> WikiValidationResult:
    """Validate the `openwiki/` tree and its Agile-V manifest.

    Args:
        repo_root: Repository root directory.

    Returns:
        WikiValidationResult. `passed` is False only for structural
        failures (missing required page, manifest/disk mismatch); staleness
        relative to source code is reported in `warnings` only.
    """
    errors: list[str] = []
    warnings: list[str] = []

    wiki_dir = repo_root / constants.WIKI_DIR
    required = domains.required_pages(repo_root)

    if not wiki_dir.exists():
        errors.append(
            f"{constants.WIKI_DIR}/ does not exist. Run 'agilev wiki init' to scaffold it."
        )
        result = WikiValidationResult(
            generated_at=datetime.now(UTC).isoformat(),
            passed=False,
            errors=errors,
            warnings=warnings,
            required_pages=required,
        )
        save_validation(repo_root, result)
        return result

    for page in required:
        if not (wiki_dir / page).exists():
            errors.append(f"Required page missing: {constants.WIKI_DIR}/{page}")

    stored_manifest = load_manifest(repo_root)
    current_manifest = build_manifest(repo_root)

    if stored_manifest is None:
        warnings.append(
            "No manifest found at "
            f"{constants.STATE_DIR}/{constants.MANIFEST_FILENAME}. "
            "Run 'agilev wiki update' to record one."
        )
    else:
        errors.extend(_diff_manifest(stored_manifest, current_manifest))

    stale_pages: list[str] = []
    if stored_manifest is not None:
        freshness = compute_freshness(repo_root, stored_manifest)
        if not freshness.is_fresh:
            stale_pages = freshness.stale_pages
            warnings.append(
                "Pages may be stale relative to their declared sources "
                f"(run 'agilev wiki update' to refresh): {', '.join(stale_pages)}"
            )

    result = WikiValidationResult(
        generated_at=datetime.now(UTC).isoformat(),
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        required_pages=required,
        stale_pages=stale_pages,
    )
    save_validation(repo_root, result)
    return result


def _diff_manifest(stored: WikiManifest, current: WikiManifest) -> list[str]:
    """Compare a stored manifest against a freshly-scanned one.

    Returns a list of error strings for pages whose on-disk hash no longer
    matches the manifest (indicating `agilev wiki update` was not run after
    an edit), or that were added/removed without updating the manifest.
    """
    errors: list[str] = []

    stored_paths = set(stored.pages)
    current_paths = set(current.pages)

    for missing in sorted(stored_paths - current_paths):
        errors.append(
            f"Page in manifest but missing on disk: {constants.WIKI_DIR}/{missing} "
            "(run 'agilev wiki update')"
        )

    for extra in sorted(current_paths - stored_paths):
        errors.append(
            f"Page on disk but missing from manifest: {constants.WIKI_DIR}/{extra} "
            "(run 'agilev wiki update')"
        )

    for path in sorted(stored_paths & current_paths):
        if stored.pages[path].sha256 != current.pages[path].sha256:
            errors.append(
                f"Manifest out of date for {constants.WIKI_DIR}/{path} "
                "(content changed since last 'agilev wiki update')"
            )

    return errors


__all__ = [
    "WikiValidationResult",
    "validate",
    "validation_path",
    "load_validation",
    "save_validation",
    "compute_file_hash",
]
