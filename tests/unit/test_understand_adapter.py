"""Unit tests for the Understand Anything adapter.

Tests cover:
- Graph detection (find_understand_graph, find_understand_diff)
- Graph loading (load_graph_json)
- Hash computation (sha256_file)
- Adapter end-to-end (UnderstandAnythingAdapter.load)
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from agilev.integrations.understand_anything.detector import (
    find_understand_graph,
    find_understand_diff,
    graph_is_available,
)
from agilev.integrations.understand_anything.errors import (
    GraphLoadError,
    GraphHashError,
    GraphNotFoundError,
)
from agilev.integrations.understand_anything.hashing import sha256_file, write_hash_file
from agilev.integrations.understand_anything.loader import (
    load_graph_json,
    detect_nodes,
    detect_edges,
)
from agilev.integrations.understand_anything.adapter import UnderstandAnythingAdapter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_repo(
    tmp_path: Path, graph_data: dict | None = None, diff_data: dict | None = None
) -> Path:
    """Create a temporary repo directory with optional graph and diff files."""
    ua_dir = tmp_path / ".understand-anything"
    ua_dir.mkdir()
    if graph_data is not None:
        (ua_dir / "knowledge-graph.json").write_text(json.dumps(graph_data), encoding="utf-8")
    if diff_data is not None:
        (ua_dir / "diff-overlay.json").write_text(json.dumps(diff_data), encoding="utf-8")
    return tmp_path


MINIMAL_GRAPH = {
    "nodes": [
        {"id": "node-1", "type": "file", "name": "auth.ts", "path": "src/auth/auth.ts"},
        {"id": "node-2", "type": "function", "name": "loginHandler", "path": "src/auth/auth.ts"},
        {"id": "node-3", "type": "test", "name": "auth.spec.ts", "path": "tests/auth.spec.ts"},
    ],
    "edges": [
        {"id": "edge-1", "source": "node-1", "target": "node-2", "type": "contains"},
        {"id": "edge-2", "source": "node-3", "target": "node-2", "type": "tests"},
    ],
}


# ---------------------------------------------------------------------------
# detector tests
# ---------------------------------------------------------------------------


class TestDetector:
    def test_find_graph_default_path(self, tmp_path):
        repo = _make_repo(tmp_path, graph_data=MINIMAL_GRAPH)
        result = find_understand_graph(repo)
        assert result is not None
        assert result.name == "knowledge-graph.json"

    def test_find_graph_not_found(self, tmp_path):
        result = find_understand_graph(tmp_path)
        assert result is None

    def test_find_diff_found(self, tmp_path):
        repo = _make_repo(tmp_path, graph_data=MINIMAL_GRAPH, diff_data={"changes": []})
        result = find_understand_diff(repo)
        assert result is not None

    def test_find_diff_not_found(self, tmp_path):
        repo = _make_repo(tmp_path, graph_data=MINIMAL_GRAPH)
        result = find_understand_diff(repo)
        assert result is None

    def test_graph_is_available_true(self, tmp_path):
        repo = _make_repo(tmp_path, graph_data=MINIMAL_GRAPH)
        assert graph_is_available(repo) is True

    def test_graph_is_available_false(self, tmp_path):
        assert graph_is_available(tmp_path) is False


# ---------------------------------------------------------------------------
# hashing tests
# ---------------------------------------------------------------------------


class TestHashing:
    def test_sha256_produces_correct_format(self, tmp_path):
        f = tmp_path / "test.json"
        f.write_text('{"hello": "world"}', encoding="utf-8")
        h = sha256_file(f)
        assert h.startswith("sha256:")
        assert len(h) == 7 + 64  # "sha256:" + 64 hex chars

    def test_sha256_consistent(self, tmp_path):
        f = tmp_path / "test.json"
        f.write_text('{"hello": "world"}', encoding="utf-8")
        assert sha256_file(f) == sha256_file(f)

    def test_sha256_different_for_different_files(self, tmp_path):
        f1 = tmp_path / "a.json"
        f2 = tmp_path / "b.json"
        f1.write_text('{"a": 1}', encoding="utf-8")
        f2.write_text('{"b": 2}', encoding="utf-8")
        assert sha256_file(f1) != sha256_file(f2)

    def test_sha256_missing_file_raises(self, tmp_path):
        with pytest.raises(GraphHashError):
            sha256_file(tmp_path / "nonexistent.json")

    def test_write_hash_file(self, tmp_path):
        out = tmp_path / "hash.txt"
        write_hash_file("sha256:abc123", out)
        assert out.read_text().strip() == "sha256:abc123"


# ---------------------------------------------------------------------------
# loader tests
# ---------------------------------------------------------------------------


class TestLoader:
    def test_load_valid_json(self, tmp_path):
        f = tmp_path / "graph.json"
        f.write_text(json.dumps(MINIMAL_GRAPH), encoding="utf-8")
        data = load_graph_json(f)
        assert "nodes" in data
        assert len(data["nodes"]) == 3

    def test_load_invalid_json_raises(self, tmp_path):
        f = tmp_path / "graph.json"
        f.write_text("not json at all {{{", encoding="utf-8")
        with pytest.raises(GraphLoadError):
            load_graph_json(f)

    def test_load_missing_file_raises(self, tmp_path):
        with pytest.raises(GraphLoadError):
            load_graph_json(tmp_path / "missing.json")

    def test_load_non_object_json_raises(self, tmp_path):
        f = tmp_path / "graph.json"
        f.write_text("[1, 2, 3]", encoding="utf-8")
        with pytest.raises(GraphLoadError, match="Expected a JSON object"):
            load_graph_json(f)

    def test_detect_nodes_standard(self):
        nodes, key = detect_nodes(MINIMAL_GRAPH)
        assert key == "nodes"
        assert len(nodes) == 3

    def test_detect_nodes_nested_graph_key(self):
        data = {"graph": {"nodes": [{"id": "n1", "type": "file", "name": "foo.py"}]}}
        nodes, key = detect_nodes(data)
        assert key == "graph.nodes"
        assert len(nodes) == 1

    def test_detect_nodes_files_key(self):
        data = {"files": [{"id": "f1", "name": "foo.py"}]}
        nodes, key = detect_nodes(data)
        assert key == "files"

    def test_detect_nodes_no_nodes_returns_empty(self):
        nodes, key = detect_nodes({"metadata": {}})
        assert nodes == []
        assert key is None

    def test_detect_edges_standard(self):
        edges, key = detect_edges(MINIMAL_GRAPH)
        assert key == "edges"
        assert len(edges) == 2

    def test_detect_edges_relationships_key(self):
        data = {"nodes": [], "relationships": [{"id": "e1", "source": "a", "target": "b"}]}
        edges, key = detect_edges(data)
        assert key == "relationships"

    def test_detect_edges_no_edges_returns_empty(self):
        edges, key = detect_edges({"nodes": []})
        assert edges == []
        assert key is None


# ---------------------------------------------------------------------------
# adapter end-to-end tests
# ---------------------------------------------------------------------------


class TestAdapter:
    def test_load_success(self, tmp_path):
        repo = _make_repo(tmp_path, graph_data=MINIMAL_GRAPH)
        adapter = UnderstandAnythingAdapter(repo_root=repo)
        result = adapter.load()

        assert result.mode == "consume-graph"
        assert result.error is None
        assert result.graph is not None
        assert len(result.graph.nodes) == 3
        assert len(result.graph.edges) == 2
        assert result.graph.source_graph_hash.startswith("sha256:")

    def test_load_no_graph_returns_standalone(self, tmp_path):
        adapter = UnderstandAnythingAdapter(repo_root=tmp_path)
        result = adapter.load()

        assert result.mode == "standalone"
        assert result.graph is None
        assert result.error is not None

    def test_load_invalid_json_returns_error(self, tmp_path):
        ua_dir = tmp_path / ".understand-anything"
        ua_dir.mkdir()
        (ua_dir / "knowledge-graph.json").write_text("INVALID JSON", encoding="utf-8")

        adapter = UnderstandAnythingAdapter(repo_root=tmp_path)
        result = adapter.load()

        assert result.graph is None
        assert result.error is not None
        assert "Invalid JSON" in result.error or "Cannot load" in result.error

    def test_load_detects_diff(self, tmp_path):
        repo = _make_repo(tmp_path, graph_data=MINIMAL_GRAPH, diff_data={"changes": []})
        adapter = UnderstandAnythingAdapter(repo_root=repo)
        result = adapter.load()

        assert result.diff_path is not None

    def test_graph_metadata_contains_adapter_info(self, tmp_path):
        repo = _make_repo(tmp_path, graph_data=MINIMAL_GRAPH)
        adapter = UnderstandAnythingAdapter(repo_root=repo)
        result = adapter.load()

        meta = result.graph.metadata
        assert meta["adapter_name"] == "understand-anything-adapter"
        assert meta["adapter_version"] == "0.1.0"

    def test_graph_to_dict_is_serializable(self, tmp_path):
        repo = _make_repo(tmp_path, graph_data=MINIMAL_GRAPH)
        adapter = UnderstandAnythingAdapter(repo_root=repo)
        result = adapter.load()

        d = result.graph.to_dict()
        # Must be JSON-serializable.
        serialized = json.dumps(d)
        assert len(serialized) > 0
        assert d["schema_version"] == "1.0.0"
