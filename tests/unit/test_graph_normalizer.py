"""Unit tests for the graph normalizer.

Tests cover:
- Node type mapping (all known types + unknown fallback)
- Edge type mapping (all known types + unknown fallback)
- Synthetic ID generation for nodes without IDs
- Dangling edge detection (edges referencing unknown node IDs)
- normalize_graph end-to-end
"""

from __future__ import annotations

from agilev.integrations.understand_anything.normalizer import (
    _EDGE_TYPE_MAP,
    _NODE_TYPE_MAP,
    normalize_edge,
    normalize_graph,
    normalize_node,
)

# ---------------------------------------------------------------------------
# normalize_node
# ---------------------------------------------------------------------------


class TestNormalizeNode:
    def test_maps_file_type(self):
        node = normalize_node({"id": "n1", "type": "file", "name": "foo.ts"}, 0, [])
        assert node.type == "file"

    def test_maps_source_file_type(self):
        node = normalize_node({"id": "n1", "type": "source_file", "name": "foo.ts"}, 0, [])
        assert node.type == "file"

    def test_maps_function_type(self):
        node = normalize_node({"id": "n1", "type": "function", "name": "handler"}, 0, [])
        assert node.type == "function"

    def test_maps_method_to_function(self):
        node = normalize_node({"id": "n1", "type": "method", "name": "login"}, 0, [])
        assert node.type == "function"

    def test_maps_class_type(self):
        node = normalize_node({"id": "n1", "type": "class", "name": "AuthController"}, 0, [])
        assert node.type == "class"

    def test_maps_struct_to_class(self):
        node = normalize_node({"id": "n1", "type": "struct", "name": "Config"}, 0, [])
        assert node.type == "class"

    def test_maps_test_type(self):
        node = normalize_node({"id": "n1", "type": "test", "name": "auth.spec.ts"}, 0, [])
        assert node.type == "test"

    def test_maps_spec_to_test(self):
        node = normalize_node({"id": "n1", "type": "spec", "name": "auth.spec.ts"}, 0, [])
        assert node.type == "test"

    def test_unknown_type_falls_back(self):
        warnings = []
        node = normalize_node({"id": "n1", "type": "widget", "name": "foo"}, 0, warnings)
        assert node.type == "unknown"
        assert any("unknown type" in w for w in warnings)

    def test_missing_id_uses_synthetic(self):
        warnings = []
        node = normalize_node({"type": "file", "name": "foo.ts"}, 5, warnings)
        assert node.id == "node-5"
        assert any("synthetic id" in w for w in warnings)

    def test_path_extracted(self):
        node = normalize_node(
            {"id": "n1", "type": "file", "name": "foo.ts", "path": "src/auth/foo.ts"},
            0,
            [],
        )
        assert node.path == "src/auth/foo.ts"

    def test_symbol_extracted(self):
        node = normalize_node(
            {"id": "n1", "type": "function", "name": "login", "symbol": "AuthController.login"},
            0,
            [],
        )
        assert node.symbol == "AuthController.login"

    def test_summary_extracted(self):
        node = normalize_node(
            {"id": "n1", "type": "function", "name": "login", "summary": "Handles login."},
            0,
            [],
        )
        assert node.summary == "Handles login."

    def test_raw_preserved(self):
        raw = {"id": "n1", "type": "file", "name": "foo.ts", "custom_field": "yes"}
        node = normalize_node(raw, 0, [])
        assert node.raw == raw

    def test_invalid_non_dict_returns_unknown(self):
        warnings = []
        node = normalize_node("not-a-dict", 3, warnings)
        assert node.type == "unknown"
        assert any("not a dict" in w for w in warnings)

    def test_all_node_type_map_values_are_valid_types(self):
        valid_types = {
            "file",
            "function",
            "class",
            "module",
            "domain",
            "flow",
            "step",
            "test",
            "doc",
            "unknown",
        }
        for v in _NODE_TYPE_MAP.values():
            assert v in valid_types


# ---------------------------------------------------------------------------
# normalize_edge
# ---------------------------------------------------------------------------


class TestNormalizeEdge:
    def test_maps_import_type(self):
        edge = normalize_edge(
            {"id": "e1", "source": "n1", "target": "n2", "type": "import"},
            0,
            {"n1", "n2"},
            [],
        )
        assert edge.type == "imports"

    def test_maps_call_to_calls(self):
        edge = normalize_edge(
            {"id": "e1", "source": "n1", "target": "n2", "type": "call"},
            0,
            {"n1", "n2"},
            [],
        )
        assert edge.type == "calls"

    def test_maps_tests_type(self):
        edge = normalize_edge(
            {"id": "e1", "source": "n1", "target": "n2", "type": "tests"},
            0,
            {"n1", "n2"},
            [],
        )
        assert edge.type == "tests"

    def test_unknown_edge_type_falls_back(self):
        warnings = []
        edge = normalize_edge(
            {"id": "e1", "source": "n1", "target": "n2", "type": "weird_rel"},
            0,
            {"n1", "n2"},
            warnings,
        )
        assert edge.type == "unknown"
        assert any("unknown type" in w for w in warnings)

    def test_dangling_source_sets_low_confidence(self):
        warnings = []
        edge = normalize_edge(
            {"id": "e1", "source": "ghost", "target": "n2", "type": "calls"},
            0,
            {"n2"},
            warnings,
        )
        assert edge.confidence == "low"
        assert any("source" in w and "ghost" in w for w in warnings)

    def test_dangling_target_sets_low_confidence(self):
        warnings = []
        edge = normalize_edge(
            {"id": "e1", "source": "n1", "target": "ghost", "type": "calls"},
            0,
            {"n1"},
            warnings,
        )
        assert edge.confidence == "low"

    def test_valid_edge_has_high_confidence(self):
        edge = normalize_edge(
            {"id": "e1", "source": "n1", "target": "n2", "type": "imports"},
            0,
            {"n1", "n2"},
            [],
        )
        assert edge.confidence == "high"

    def test_all_edge_type_map_values_are_valid(self):
        valid_types = {
            "imports",
            "calls",
            "contains",
            "extends",
            "implements",
            "uses",
            "tests",
            "documents",
            "depends_on",
            "unknown",
        }
        for v in _EDGE_TYPE_MAP.values():
            assert v in valid_types


# ---------------------------------------------------------------------------
# normalize_graph
# ---------------------------------------------------------------------------


class TestNormalizeGraph:
    def test_returns_correct_counts(self):
        raw_nodes = [
            {"id": "n1", "type": "file", "name": "auth.ts"},
            {"id": "n2", "type": "function", "name": "login"},
        ]
        raw_edges = [
            {"id": "e1", "source": "n1", "target": "n2", "type": "contains"},
        ]
        nodes, edges, warnings = normalize_graph(raw_nodes, raw_edges)
        assert len(nodes) == 2
        assert len(edges) == 1

    def test_empty_inputs_return_empty_outputs(self):
        nodes, edges, warnings = normalize_graph([], [])
        assert nodes == []
        assert edges == []
        assert warnings == []

    def test_warnings_accumulated(self):
        raw_nodes = [
            {"id": "n1", "type": "widget", "name": "foo"},  # unknown type → warning
        ]
        raw_edges = [
            {"id": "e1", "source": "ghost", "target": "n1", "type": "calls"},  # dangling → warning
        ]
        nodes, edges, warnings = normalize_graph(raw_nodes, raw_edges)
        assert len(warnings) >= 2  # at least unknown type + dangling edge

    def test_node_ids_are_unique(self):
        raw_nodes = [
            {"id": "n1", "type": "file", "name": "a.ts"},
            {"id": "n2", "type": "file", "name": "b.ts"},
        ]
        nodes, _, _ = normalize_graph(raw_nodes, [])
        ids = [n.id for n in nodes]
        assert len(ids) == len(set(ids))
