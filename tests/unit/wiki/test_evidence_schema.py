"""Validate that evidence_bundle.schema.json accepts a knowledge_snapshot.

Uses the real example evidence bundle plus a knowledge_snapshot merged in,
to prove the schema addition is valid JSON Schema and doesn't reject
otherwise-valid bundles.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = REPO_ROOT / "schemas" / "evidence_bundle.schema.json"
EXAMPLE_BUNDLE_PATH = REPO_ROOT / "evidence" / "examples" / "feature" / "evidence_bundle.json"


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _load_example_bundle() -> dict:
    return json.loads(EXAMPLE_BUNDLE_PATH.read_text(encoding="utf-8"))


def test_example_bundle_still_valid_without_knowledge_snapshot() -> None:
    schema = _load_schema()
    bundle = _load_example_bundle()

    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(bundle))

    assert errors == []


def test_bundle_with_knowledge_snapshot_is_valid() -> None:
    schema = _load_schema()
    bundle = _load_example_bundle()
    bundle["knowledge_snapshot"] = {
        "wiki_dir": "openwiki",
        "manifest_path": ".agile-v/wiki/manifest.json",
        "manifest_generated_at": "2026-01-01T00:00:00+00:00",
        "page_count": 6,
        "pages": ["README.md"],
        "required_pages": ["README.md"],
        "validation_passed": True,
        "validation_errors": [],
        "validation_warnings": [],
        "stale_pages": [],
        "captured_at": "2026-01-01T00:00:00+00:00",
    }

    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(bundle))

    assert errors == []


def test_knowledge_snapshot_missing_required_field_is_invalid() -> None:
    schema = _load_schema()
    bundle = _load_example_bundle()
    bundle["knowledge_snapshot"] = {"wiki_dir": "openwiki"}  # missing page_count, validation_passed

    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(bundle))

    assert len(errors) >= 1
