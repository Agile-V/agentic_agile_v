"""Unit tests for graph-based impact analysis.

Tests cover:
- Keyword extraction from change request text
- Node search by keyword
- Neighbor traversal
- analyze_impact end-to-end
- Risk inference
"""

from __future__ import annotations

import pytest

from agilev.graph.model import SystemGraph, SystemNode, SystemEdge, ImpactMap
from agilev.graph.queries import (
    extract_keywords_from_change_request,
    find_nodes_by_keyword,
    find_nodes_by_path,
    get_neighbors,
    get_test_nodes_for,
)
from agilev.graph.impact import analyze_impact


# ---------------------------------------------------------------------------
# Sample graph fixture
# ---------------------------------------------------------------------------


def make_auth_graph() -> SystemGraph:
    """A small auth-service graph for testing."""
    nodes = [
        SystemNode(
            id="n-ctrl",
            type="class",
            name="AuthController",
            path="src/auth/auth.controller.ts",
            symbol="AuthController",
            summary="Handles login, logout, refresh.",
        ),
        SystemNode(
            id="n-login",
            type="function",
            name="login",
            path="src/auth/auth.controller.ts",
            symbol="AuthController.login",
            summary="Login handler for POST /auth/login.",
        ),
        SystemNode(
            id="n-svc",
            type="class",
            name="AuthService",
            path="src/auth/auth.service.ts",
            symbol="AuthService",
        ),
        SystemNode(
            id="n-module",
            type="module",
            name="AuthModule",
            path="src/auth/auth.module.ts",
            symbol="AuthModule",
        ),
        SystemNode(
            id="n-guard",
            type="class",
            name="RateLimitGuard",
            path="src/auth/guards/rate-limit.guard.ts",
            symbol="RateLimitGuard",
        ),
        SystemNode(
            id="n-test", type="test", name="auth.e2e-spec.ts", path="test/auth/auth.e2e-spec.ts"
        ),
        SystemNode(
            id="n-util",
            type="class",
            name="HashingService",
            path="src/common/hashing.service.ts",
            symbol="HashingService",
        ),
    ]
    edges = [
        SystemEdge(id="e1", source="n-ctrl", target="n-login", type="contains"),
        SystemEdge(id="e2", source="n-ctrl", target="n-svc", type="depends_on"),
        SystemEdge(id="e3", source="n-module", target="n-ctrl", type="contains"),
        SystemEdge(id="e4", source="n-test", target="n-login", type="tests"),
        SystemEdge(id="e5", source="n-svc", target="n-util", type="depends_on"),
    ]
    return SystemGraph(
        source="understand-anything",
        source_graph_path=".understand-anything/knowledge-graph.json",
        source_graph_hash="sha256:abc123",
        generated_at="2026-05-26T09:00:00Z",
        nodes=nodes,
        edges=edges,
    )


# ---------------------------------------------------------------------------
# Keyword extraction tests
# ---------------------------------------------------------------------------


class TestKeywordExtraction:
    def test_extracts_identifiers(self):
        text = "Add rate limiting to the login endpoint"
        keywords = extract_keywords_from_change_request(text)
        assert "limiting" in keywords or "login" in keywords or "endpoint" in keywords

    def test_filters_stop_words(self):
        text = "Add the new feature to the system"
        keywords = extract_keywords_from_change_request(text)
        assert "the" not in keywords
        assert "new" not in keywords
        assert "add" not in keywords

    def test_empty_string_returns_empty(self):
        assert extract_keywords_from_change_request("") == []

    def test_returns_list(self):
        result = extract_keywords_from_change_request("login authentication")
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# Graph query tests
# ---------------------------------------------------------------------------


class TestFindNodesByKeyword:
    def test_finds_by_name(self):
        graph = make_auth_graph()
        results = find_nodes_by_keyword(graph, ["AuthController"])
        ids = {n.id for n in results}
        assert "n-ctrl" in ids

    def test_finds_by_path_fragment(self):
        graph = make_auth_graph()
        results = find_nodes_by_keyword(graph, ["auth.controller"])
        assert any(n.id in ("n-ctrl", "n-login") for n in results)

    def test_finds_by_summary(self):
        graph = make_auth_graph()
        results = find_nodes_by_keyword(graph, ["login handler"])
        assert any(n.id == "n-login" for n in results)

    def test_no_match_returns_empty(self):
        graph = make_auth_graph()
        results = find_nodes_by_keyword(graph, ["zzznomatch"])
        assert results == []

    def test_case_insensitive(self):
        graph = make_auth_graph()
        results = find_nodes_by_keyword(graph, ["authcontroller"])
        assert any(n.id == "n-ctrl" for n in results)

    def test_multiple_keywords(self):
        graph = make_auth_graph()
        results = find_nodes_by_keyword(graph, ["login", "hashing"])
        ids = {n.id for n in results}
        assert "n-login" in ids or "n-ctrl" in ids
        assert "n-util" in ids


class TestFindNodesByPath:
    def test_exact_path_match(self):
        graph = make_auth_graph()
        results = find_nodes_by_path(graph, "src/auth/auth.controller.ts")
        assert len(results) == 2  # n-ctrl and n-login share this path

    def test_fragment_match(self):
        graph = make_auth_graph()
        results = find_nodes_by_path(graph, "auth.controller")
        assert len(results) >= 1


class TestGetNeighbors:
    def test_out_direction(self):
        graph = make_auth_graph()
        neighbors = get_neighbors(graph, "n-ctrl", direction="out", hops=1)
        ids = {n.id for n in neighbors}
        # n-ctrl --contains--> n-login, --depends_on--> n-svc
        assert "n-login" in ids
        assert "n-svc" in ids

    def test_in_direction(self):
        graph = make_auth_graph()
        neighbors = get_neighbors(graph, "n-ctrl", direction="in", hops=1)
        ids = {n.id for n in neighbors}
        # n-module --contains--> n-ctrl
        assert "n-module" in ids

    def test_both_direction(self):
        graph = make_auth_graph()
        neighbors = get_neighbors(graph, "n-ctrl", direction="both", hops=1)
        ids = {n.id for n in neighbors}
        assert "n-login" in ids
        assert "n-module" in ids

    def test_two_hops(self):
        graph = make_auth_graph()
        # n-ctrl --depends_on--> n-svc --depends_on--> n-util
        neighbors = get_neighbors(graph, "n-ctrl", direction="out", hops=2)
        ids = {n.id for n in neighbors}
        assert "n-util" in ids

    def test_edge_type_filter(self):
        graph = make_auth_graph()
        neighbors = get_neighbors(graph, "n-ctrl", edge_types=["contains"], direction="out")
        ids = {n.id for n in neighbors}
        assert "n-login" in ids
        assert "n-svc" not in ids  # only depends_on, not contains


class TestGetTestNodes:
    def test_finds_test_for_login(self):
        graph = make_auth_graph()
        test_nodes = get_test_nodes_for(graph, "n-login")
        ids = {n.id for n in test_nodes}
        assert "n-test" in ids

    def test_no_test_nodes_returns_empty(self):
        graph = make_auth_graph()
        test_nodes = get_test_nodes_for(graph, "n-module")
        assert test_nodes == []


# ---------------------------------------------------------------------------
# analyze_impact tests
# ---------------------------------------------------------------------------


class TestAnalyzeImpact:
    def test_returns_impact_map(self):
        graph = make_auth_graph()
        impact = analyze_impact(graph, "CR-001", "Add rate limiting to login endpoint")
        assert isinstance(impact, ImpactMap)
        assert impact.change_request_id == "CR-001"

    def test_direct_components_found(self):
        graph = make_auth_graph()
        impact = analyze_impact(graph, "CR-001", "Add rate limiting to login endpoint")
        direct_paths = {c.path for c in impact.direct_components}
        # "login" should match n-login (and likely n-ctrl)
        assert any("auth.controller" in p for p in direct_paths)

    def test_required_tests_found(self):
        graph = make_auth_graph()
        impact = analyze_impact(graph, "CR-001", "Add rate limiting to login endpoint")
        # n-test is connected to n-login via "tests" edge
        assert any("auth.e2e-spec" in t for t in impact.required_tests)

    def test_confidence_is_high_when_matches_found(self):
        graph = make_auth_graph()
        impact = analyze_impact(graph, "CR-001", "login rate limiting AuthController")
        assert impact.confidence == "high"

    def test_confidence_is_low_when_no_matches(self):
        graph = make_auth_graph()
        impact = analyze_impact(graph, "CR-999", "zzznomatch xyzxyz")
        assert impact.confidence == "low"

    def test_risks_identified_for_auth_change(self):
        graph = make_auth_graph()
        impact = analyze_impact(graph, "CR-001", "login authentication token security")
        risk_descs = [r.description.lower() for r in impact.risks]
        assert any("security" in d for d in risk_descs)

    def test_summary_truncated_to_200_chars(self):
        graph = make_auth_graph()
        long_text = "A" * 300
        impact = analyze_impact(graph, "CR-001", long_text)
        assert len(impact.summary) <= 200

    def test_assumptions_not_empty(self):
        graph = make_auth_graph()
        impact = analyze_impact(graph, "CR-001", "login")
        assert len(impact.assumptions) > 0

    def test_empty_graph_returns_low_confidence(self):
        empty_graph = SystemGraph(
            source="understand-anything",
            source_graph_path="path",
            source_graph_hash="sha256:abc",
            generated_at="2026-01-01T00:00:00Z",
        )
        impact = analyze_impact(empty_graph, "CR-001", "login endpoint")
        assert impact.confidence == "low"
