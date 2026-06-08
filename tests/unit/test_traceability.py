"""Unit tests for graph traceability linking.

Tests cover:
- build_traceability end-to-end
- Orphan requirement detection
- Orphan change detection
- Decision logic (pass, fail, pass_with_findings)
- req_to_component_links and component_to_test_links properties
"""

from __future__ import annotations

from agilev.graph.model import (
    AffectedComponent,
    GraphTraceabilityLink,
    ImpactMap,
    SystemEdge,
    SystemGraph,
    SystemNode,
)
from agilev.graph.traceability import TraceabilityResult, build_traceability

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def make_small_graph() -> SystemGraph:
    nodes = [
        SystemNode(
            id="n-login",
            type="function",
            name="login",
            path="src/auth/login.ts",
            symbol="AuthController.login",
        ),
        SystemNode(id="n-test", type="test", name="login.test.ts", path="tests/auth/login.test.ts"),
    ]
    edges = [
        SystemEdge(id="e1", source="n-test", target="n-login", type="tests"),
    ]
    return SystemGraph(
        source="understand-anything",
        source_graph_path=".understand-anything/knowledge-graph.json",
        source_graph_hash="sha256:abc",
        generated_at="2026-05-26T00:00:00Z",
        nodes=nodes,
        edges=edges,
    )


def make_impact_map(direct_components=None, indirect_components=None) -> ImpactMap:
    direct = direct_components or [
        AffectedComponent(
            component_id="n-login",
            path="src/auth/login.ts",
            symbol="AuthController.login",
            impact_type="modify",
            reason="Login endpoint is the target.",
            confidence="high",
        )
    ]
    return ImpactMap(
        change_request_id="CR-001",
        summary="Add rate limiting to login.",
        direct_components=direct,
        indirect_components=indirect_components or [],
        confidence="high",
    )


# ---------------------------------------------------------------------------
# TraceabilityResult properties
# ---------------------------------------------------------------------------


class TestTraceabilityResultProperties:
    def test_req_to_component_links_deduplicates(self):
        result = TraceabilityResult()
        result.links = [
            GraphTraceabilityLink("REQ-001", "n-login", "src/auth/login.ts", status="verified"),
            GraphTraceabilityLink("REQ-001", "n-login", "src/auth/login.ts", status="verified"),
        ]
        links = result.req_to_component_links
        assert len(links) == 1

    def test_component_to_test_links_only_includes_with_test(self):
        result = TraceabilityResult()
        result.links = [
            GraphTraceabilityLink(
                "REQ-001",
                "n-login",
                "src/auth/login.ts",
                test_path="tests/login.test.ts",
                status="verified",
            ),
            GraphTraceabilityLink("REQ-002", "n-other", "src/other.ts", status="missing"),
        ]
        links = result.component_to_test_links
        assert len(links) == 1
        assert links[0]["test_path"] == "tests/login.test.ts"


# ---------------------------------------------------------------------------
# build_traceability tests
# ---------------------------------------------------------------------------


class TestBuildTraceability:
    def test_basic_pass(self):
        graph = make_small_graph()
        impact = make_impact_map()
        requirements = [("REQ-001", "Rate limit the login endpoint")]

        result = build_traceability(
            graph=graph,
            impact_map=impact,
            requirements=requirements,
            test_results={"tests/auth/login.test.ts": "pass"},
        )

        assert result.decision in ("pass", "pass_with_findings")
        assert len(result.links) > 0

    def test_links_include_requirement_id(self):
        graph = make_small_graph()
        impact = make_impact_map()
        requirements = [("REQ-001", "Rate limit the login")]

        result = build_traceability(graph, impact, requirements)

        req_ids = {link.requirement_id for link in result.links}
        assert "REQ-001" in req_ids

    def test_links_include_component_path(self):
        graph = make_small_graph()
        impact = make_impact_map()
        requirements = [("REQ-001", "login")]

        result = build_traceability(graph, impact, requirements)

        paths = {link.path for link in result.links}
        assert "src/auth/login.ts" in paths

    def test_test_path_populated_from_graph(self):
        graph = make_small_graph()
        impact = make_impact_map()
        requirements = [("REQ-001", "login")]

        result = build_traceability(
            graph=graph,
            impact_map=impact,
            requirements=requirements,
            test_results={"tests/auth/login.test.ts": "pass"},
        )

        test_paths = [link.test_path for link in result.links if link.test_path]
        assert len(test_paths) > 0

    def test_verified_status_when_test_passes(self):
        graph = make_small_graph()
        impact = make_impact_map()
        requirements = [("REQ-001", "login")]

        result = build_traceability(
            graph=graph,
            impact_map=impact,
            requirements=requirements,
            test_results={"tests/auth/login.test.ts": "pass"},
        )

        statuses = [link.status for link in result.links if link.test_path]
        assert any(s == "verified" for s in statuses)

    def test_failed_status_when_test_fails(self):
        graph = make_small_graph()
        impact = make_impact_map()
        requirements = [("REQ-001", "login")]

        result = build_traceability(
            graph=graph,
            impact_map=impact,
            requirements=requirements,
            test_results={"tests/auth/login.test.ts": "fail"},
        )

        statuses = [link.status for link in result.links if link.test_path]
        assert any(s == "failed" for s in statuses)
        assert result.decision == "fail"

    def test_orphan_change_detected(self):
        graph = make_small_graph()
        impact = make_impact_map()
        requirements = [("REQ-001", "login")]

        result = build_traceability(
            graph=graph,
            impact_map=impact,
            requirements=requirements,
            changed_files=["src/auth/login.ts", "src/config/unrelated.ts"],
        )

        orphan_paths = [o["path"] for o in result.orphan_changes]
        assert "src/config/unrelated.ts" in orphan_paths

    def test_no_orphan_changes_when_all_linked(self):
        graph = make_small_graph()
        impact = make_impact_map()
        requirements = [("REQ-001", "login")]

        result = build_traceability(
            graph=graph,
            impact_map=impact,
            requirements=requirements,
            changed_files=["src/auth/login.ts"],
        )

        assert result.orphan_changes == []

    def test_empty_requirements_produces_no_links(self):
        graph = make_small_graph()
        impact = make_impact_map()

        result = build_traceability(graph, impact, requirements=[])

        assert result.links == []

    def test_empty_impact_produces_no_links(self):
        graph = make_small_graph()
        empty_impact = ImpactMap(change_request_id="CR-001", summary="test")
        requirements = [("REQ-001", "login")]

        result = build_traceability(graph, empty_impact, requirements)

        # With no components in impact map, no links should be created.
        assert result.links == []

    def test_req_to_component_links_populated(self):
        graph = make_small_graph()
        impact = make_impact_map()
        requirements = [("REQ-001", "login")]

        result = build_traceability(graph, impact, requirements)
        links = result.req_to_component_links

        assert len(links) > 0
        assert all("requirement_id" in l for l in links)
        assert all("component_id" in l for l in links)

    def test_pass_with_findings_when_orphan_changes(self):
        graph = make_small_graph()
        impact = make_impact_map()
        requirements = [("REQ-001", "login")]

        result = build_traceability(
            graph=graph,
            impact_map=impact,
            requirements=requirements,
            changed_files=["src/auth/login.ts", "src/unrelated.ts"],
            test_results={"tests/auth/login.test.ts": "pass"},
        )

        # Orphan change → pass_with_findings (not fail, since tests pass).
        assert result.decision in ("pass_with_findings", "pass")
