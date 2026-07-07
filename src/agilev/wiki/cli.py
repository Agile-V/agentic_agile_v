"""CLI subcommands for the Agile-V OpenWiki knowledge layer.

Adds `agilev wiki init|update|validate|status|snapshot`, following the same
`build_*_parser(subparsers)` pattern used by `agilev.pcb.cli`.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from agilev.wiki import constants
from agilev.wiki.errors import WikiRunnerError
from agilev.wiki.freshness import compute_freshness, load_freshness, save_freshness
from agilev.wiki.manifest import build_manifest, load_manifest, save_manifest
from agilev.wiki.runner import OpenWikiRunner
from agilev.wiki.scaffolder import scaffold_wiki
from agilev.wiki.snapshot import build_knowledge_snapshot, write_snapshot_to_task
from agilev.wiki.source_map import build_source_map, save_source_map
from agilev.wiki.validator import validate as run_validation


def cmd_wiki_init(args: argparse.Namespace) -> int:
    """Scaffold `openwiki/` required pages and record an initial manifest."""
    repo_root = Path.cwd()

    if args.run_openwiki:
        runner = OpenWikiRunner(repo_root)
        try:
            result = runner.init()
            print(f"openwiki --init exit code: {result.returncode}")
            if result.log_path:
                print(f"  log: {result.log_path.relative_to(repo_root)}")
        except WikiRunnerError as exc:
            print(f"⚠️  {exc}")

    written = scaffold_wiki(repo_root, force=args.force)

    manifest = build_manifest(repo_root)
    manifest_path = save_manifest(repo_root, manifest)

    source_map = build_source_map(manifest)
    save_source_map(repo_root, source_map)

    freshness = compute_freshness(repo_root, manifest)
    save_freshness(repo_root, freshness)

    print(f"✅ OpenWiki knowledge layer initialized ({constants.WIKI_DIR}/)")
    if written:
        print(f"\nScaffolded {len(written)} page(s):")
        for path in written:
            print(f"  - {path.relative_to(repo_root)}")
    else:
        print("\nNo new pages scaffolded (all required pages already exist).")
    print(f"\nManifest: {manifest_path.relative_to(repo_root)}")
    print(f"Pages tracked: {len(manifest.pages)}")

    return 0


def cmd_wiki_update(args: argparse.Namespace) -> int:
    """Recompute manifest/source-map/freshness from the current `openwiki/`."""
    repo_root = Path.cwd()

    if args.run_openwiki:
        runner = OpenWikiRunner(repo_root)
        try:
            result = runner.update()
            print(f"openwiki --update exit code: {result.returncode}")
            if result.log_path:
                print(f"  log: {result.log_path.relative_to(repo_root)}")
        except WikiRunnerError as exc:
            print(f"⚠️  {exc}")

    manifest = build_manifest(repo_root)
    save_manifest(repo_root, manifest)

    source_map = build_source_map(manifest)
    save_source_map(repo_root, source_map)

    freshness = compute_freshness(repo_root, manifest)
    save_freshness(repo_root, freshness)

    print(f"✅ Wiki manifest updated: {len(manifest.pages)} page(s) tracked")
    if not freshness.is_fresh:
        print(f"⚠️  Stale pages relative to previous manifest: {', '.join(freshness.stale_pages)}")

    return 0


def cmd_wiki_validate(args: argparse.Namespace) -> int:
    """Validate `openwiki/` structure and manifest freshness."""
    repo_root = Path.cwd()
    result = run_validation(repo_root)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        if result.passed:
            print("✅ OpenWiki knowledge layer validation PASSED")
        else:
            print("❌ OpenWiki knowledge layer validation FAILED")
        for error in result.errors:
            print(f"  ERROR: {error}")
        for warning in result.warnings:
            print(f"  WARNING: {warning}")

    return 0 if result.passed else 1


def cmd_wiki_status(args: argparse.Namespace) -> int:
    """Show a human-readable (or JSON) freshness/validation summary."""
    repo_root = Path.cwd()

    manifest = load_manifest(repo_root)
    freshness = load_freshness(repo_root)
    validation = run_validation(repo_root)

    stale_pages: list[str] = freshness.stale_pages if freshness else []
    status: dict[str, Any] = {
        "wiki_dir": constants.WIKI_DIR,
        "initialized": manifest is not None,
        "page_count": len(manifest.pages) if manifest else 0,
        "manifest_generated_at": manifest.generated_at if manifest else None,
        "fresh": freshness.is_fresh if freshness else None,
        "stale_pages": stale_pages,
        "validation_passed": validation.passed,
        "validation_errors": validation.errors,
        "validation_warnings": validation.warnings,
    }

    if args.json:
        print(json.dumps(status, indent=2))
        return 0 if validation.passed else 1

    print("📚 OpenWiki Knowledge Layer Status\n")
    print(f"  Directory:  {constants.WIKI_DIR}/")
    print(f"  Initialized: {'yes' if status['initialized'] else 'no'}")
    print(f"  Pages tracked: {status['page_count']}")
    print(f"  Manifest generated at: {status['manifest_generated_at'] or 'n/a'}")
    print(f"  Fresh: {status['fresh']}")
    if stale_pages:
        print(f"  Stale pages: {', '.join(stale_pages)}")
    print(f"  Validation: {'PASS' if validation.passed else 'FAIL'}")
    for error in validation.errors:
        print(f"    ERROR: {error}")
    for warning in validation.warnings:
        print(f"    WARNING: {warning}")

    return 0 if validation.passed else 1


def cmd_wiki_snapshot(args: argparse.Namespace) -> int:
    """Write a `knowledge_snapshot` into a task's evidence file."""
    repo_root = Path.cwd()

    try:
        snapshot = build_knowledge_snapshot(repo_root)
        evidence_path = write_snapshot_to_task(repo_root, args.task, snapshot)
    except FileNotFoundError as exc:
        print(f"❌ {exc}")
        return 1

    print(f"✅ Knowledge snapshot written to {evidence_path.relative_to(repo_root)}")
    print(f"   Pages: {snapshot['page_count']}")
    print(f"   Validation passed: {snapshot['validation_passed']}")
    if snapshot["stale_pages"]:
        print(f"   Stale pages: {', '.join(snapshot['stale_pages'])}")

    return 0 if snapshot["validation_passed"] else 1


def build_wiki_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """Register the `wiki` command group on the top-level `agilev` parser."""
    wiki_parser = subparsers.add_parser("wiki", help="OpenWiki knowledge-layer commands")
    wiki_subparsers = wiki_parser.add_subparsers(dest="wiki_command", required=True)

    init_parser = wiki_subparsers.add_parser(
        "init", help="Scaffold openwiki/ required pages and manifest"
    )
    init_parser.add_argument(
        "--force", action="store_true", help="Overwrite existing scaffolded pages"
    )
    init_parser.add_argument(
        "--run-openwiki",
        action="store_true",
        help="Also invoke the real 'openwiki --init' CLI if it is installed",
    )
    init_parser.set_defaults(func=cmd_wiki_init)

    update_parser = wiki_subparsers.add_parser(
        "update", help="Recompute manifest/source-map/freshness from openwiki/"
    )
    update_parser.add_argument(
        "--run-openwiki",
        action="store_true",
        help="Also invoke the real 'openwiki --update' CLI if it is installed",
    )
    update_parser.set_defaults(func=cmd_wiki_update)

    validate_parser = wiki_subparsers.add_parser(
        "validate", help="Validate openwiki/ structure and freshness"
    )
    validate_parser.add_argument("--json", action="store_true", help="Output as JSON")
    validate_parser.set_defaults(func=cmd_wiki_validate)

    status_parser = wiki_subparsers.add_parser(
        "status", help="Show wiki freshness/validation summary"
    )
    status_parser.add_argument("--json", action="store_true", help="Output as JSON")
    status_parser.set_defaults(func=cmd_wiki_status)

    snapshot_parser = wiki_subparsers.add_parser(
        "snapshot", help="Write a knowledge_snapshot into a task's evidence file"
    )
    snapshot_parser.add_argument("--task", required=True, help="Task ID (e.g., AAV-0001)")
    snapshot_parser.set_defaults(func=cmd_wiki_snapshot)

    return wiki_parser
