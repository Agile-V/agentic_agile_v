"""Knowledge snapshot builder for evidence bundles.

Produces a compact `knowledge_snapshot` object summarizing the state of the
`openwiki/` knowledge layer (page count, validation result, staleness) for
inclusion in a task's evidence bundle, and merges it in place.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from agilev.wiki import constants
from agilev.wiki.manifest import load_manifest
from agilev.wiki.validator import validate


def build_knowledge_snapshot(repo_root: Path) -> dict[str, Any]:
    """Build a `knowledge_snapshot` evidence object from current wiki state.

    Runs validation fresh (rather than trusting a possibly-stale cached
    validation.json) so the snapshot always reflects the current repository
    state at the time evidence is collected.

    Args:
        repo_root: Repository root directory.

    Returns:
        A JSON-serializable dict suitable for embedding in an evidence
        bundle under the `knowledge_snapshot` key.
    """
    manifest = load_manifest(repo_root)
    result = validate(repo_root)

    return {
        "wiki_dir": constants.WIKI_DIR,
        "manifest_path": f"{constants.STATE_DIR}/{constants.MANIFEST_FILENAME}",
        "manifest_generated_at": manifest.generated_at if manifest else None,
        "page_count": len(manifest.pages) if manifest else 0,
        "pages": sorted(manifest.pages) if manifest else [],
        "required_pages": result.required_pages,
        "validation_passed": result.passed,
        "validation_errors": result.errors,
        "validation_warnings": result.warnings,
        "stale_pages": result.stale_pages,
        "captured_at": datetime.now(UTC).isoformat(),
    }


def find_evidence_file(task_dir: Path) -> Path:
    """Locate the evidence file to merge a knowledge snapshot into.

    Prefers `evidence_bundle.json` (written by OpenHands's EvidenceAdapter)
    over `evidence.json` (written by `agilev new`), falling back to
    `evidence.json` if neither exists yet.
    """
    bundle_path = task_dir / "evidence_bundle.json"
    if bundle_path.exists():
        return bundle_path
    return task_dir / "evidence.json"


def write_snapshot_to_task(
    repo_root: Path, task_id: str, snapshot: dict[str, Any] | None = None
) -> Path:
    """Merge a knowledge snapshot into a task's evidence file.

    Args:
        repo_root: Repository root directory.
        task_id: Task ID (e.g., AAV-0001).
        snapshot: Precomputed snapshot; computed via `build_knowledge_snapshot`
            if not provided.

    Returns:
        Path to the evidence file that was updated.

    Raises:
        FileNotFoundError: If the task directory does not exist.
    """
    task_dir = repo_root / ".agentic-agile-v" / "tasks" / task_id
    if not task_dir.exists():
        raise FileNotFoundError(f"Task directory not found: {task_dir}")

    if snapshot is None:
        snapshot = build_knowledge_snapshot(repo_root)

    evidence_path = find_evidence_file(task_dir)

    if evidence_path.exists():
        bundle = json.loads(evidence_path.read_text(encoding="utf-8"))
    else:
        bundle = {"task_id": task_id}

    bundle["knowledge_snapshot"] = snapshot

    evidence_path.write_text(json.dumps(bundle, indent=2, sort_keys=True), encoding="utf-8")
    return evidence_path
