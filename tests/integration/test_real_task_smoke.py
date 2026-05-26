"""Integration smoke tests against a realistic synthetic knowledge graph.

These tests exercise the full adapter pipeline end-to-end:
  fixture JSON → UnderstandAnythingAdapter.load() → SystemGraph
  → analyze_impact() → build_traceability()

They are NOT mocked — they read the real fixture file and run real code paths.
Run with: pytest tests/integration/ -v
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
GRAPH_PATH = FIXTURES_DIR / "knowledge_graph.json"


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _load_result():
    """Run the full adapter load against the fixture file."""
    from agilev.integrations.understand_anything import UnderstandAnythingAdapter

    adapter = UnderstandAnythingAdapter(repo_root=str(FIXTURES_DIR))
    return adapter.load(graph_path=str(GRAPH_PATH))


def _graph():
    """Return a loaded SystemGraph from the fixture."""
    result = _load_result()
    assert result.graph is not None, f"Graph failed to load: {result.error}"
    return result.graph


def _impact(cr_id: str, cr_text: str):
    """Run analyze_impact on the fixture graph."""
    from agilev.graph.impact import analyze_impact

    return analyze_impact(_graph(), cr_id, cr_text)


# ---------------------------------------------------------------------------
# Adapter / loader
# ---------------------------------------------------------------------------


class TestAdapterLoadFixture:
    def test_mode_is_consume_graph(self):
        assert _load_result().mode == "consume-graph"

    def test_graph_hash_is_sha256(self):
        result = _load_result()
        assert result.graph_hash is not None
        assert result.graph_hash.startswith("sha256:")
        assert len(result.graph_hash) == len("sha256:") + 64

    def test_node_count(self):
        assert len(_graph().nodes) == 24

    def test_edge_count(self):
        assert len(_graph().edges) == 20

    def test_all_node_types_recognized(self):
        valid = {
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
        for node in _graph().nodes:
            assert node.type in valid, f"Unknown node type: {node.type!r}"

    def test_test_nodes_present(self):
        test_nodes = [n for n in _graph().nodes if n.type == "test"]
        assert len(test_nodes) == 4, f"Expected 4 test nodes, got {len(test_nodes)}"

    def test_paths_preserved(self):
        paths = {n.path for n in _graph().nodes if n.path}
        assert "src/api/auth.py" in paths
        assert "src/services/device.py" in paths

    def test_graph_to_dict_is_json_serializable(self):
        json.dumps(_graph().to_dict())  # must not raise

    def test_metadata_contains_repo(self):
        # The fixture's top-level "meta.repo" should be threaded into graph metadata.
        assert _graph().metadata.get("repo") == "device-service"

    def test_source_graph_hash_on_graph(self):
        result = _load_result()
        assert result.graph.source_graph_hash == result.graph_hash


# ---------------------------------------------------------------------------
# Impact analysis — change request: modify authentication / JWT
# ---------------------------------------------------------------------------


class TestImpactAnalysisAuth:
    def test_login_is_direct_component(self):
        result = _impact(
            "CR-AUTH-001", "Modify login to support MFA alongside password authentication"
        )
        direct_paths = {c.path for c in result.direct_components}
        direct_symbols = {c.symbol for c in result.direct_components}
        assert "src/api/auth.py" in direct_paths or "login" in direct_symbols, (
            f"Expected auth nodes in direct components.\n"
            f"paths: {direct_paths}\nsymbols: {direct_symbols}"
        )

    def test_token_store_is_reachable(self):
        result = _impact(
            "CR-AUTH-001", "Modify login to support MFA alongside password authentication"
        )
        all_paths = {c.path for c in result.all_components}
        all_symbols = {c.symbol for c in result.all_components}
        # login → TokenStore edge means token.py should be reachable
        assert "src/services/token.py" in all_paths or "TokenStore" in all_symbols, (
            f"TokenStore/token.py should be reachable.\npaths: {all_paths}\nsymbols: {all_symbols}"
        )

    def test_required_tests_found(self):
        result = _impact("CR-AUTH-001", "Modify login to support MFA")
        assert any("test_auth" in t for t in result.required_tests), (
            f"test_auth.py should be in required tests. Got: {result.required_tests}"
        )

    def test_auth_change_flags_security_risk(self):
        result = _impact("CR-AUTH-002", "Change JWT secret rotation and token expiry logic")
        risk_descs = [r.description.lower() for r in result.risks]
        assert any(
            "auth" in d or "security" in d or "token" in d or "jwt" in d for d in risk_descs
        ), f"Expected auth/security risk. Descriptions: {risk_descs}"

    def test_confidence_high_or_medium_when_matches_found(self):
        result = _impact("CR-AUTH-001", "Modify login function in auth module")
        assert result.confidence in ("high", "medium"), (
            f"Expected high or medium confidence, got: {result.confidence}"
        )


# ---------------------------------------------------------------------------
# Impact analysis — change request: modify device polling timeout
# ---------------------------------------------------------------------------


class TestImpactAnalysisDevice:
    def test_device_poller_is_direct(self):
        result = _impact("CR-DEV-001", "Fix timeout handling in DevicePoller poll method")
        direct_paths = {c.path for c in result.direct_components}
        direct_symbols = {c.symbol for c in result.direct_components}
        assert "src/services/device.py" in direct_paths or "DevicePoller" in direct_symbols, (
            f"Expected DevicePoller/device.py in direct components.\n"
            f"paths: {direct_paths}\nsymbols: {direct_symbols}"
        )

    def test_settings_is_reachable(self):
        result = _impact("CR-DEV-001", "Fix timeout handling in DevicePoller poll method")
        all_paths = {c.path for c in result.all_components}
        # DevicePoller → Settings edge means config.py should be reachable
        assert "src/config.py" in all_paths, (
            f"src/config.py (Settings) should be reachable. Got: {all_paths}"
        )

    def test_test_device_is_required(self):
        result = _impact("CR-DEV-001", "Fix timeout handling in DevicePoller poll method")
        assert any("test_device" in t for t in result.required_tests), (
            f"test_device.py should be required. Got: {result.required_tests}"
        )


# ---------------------------------------------------------------------------
# Traceability — link requirements to components and tests
# ---------------------------------------------------------------------------


class TestTraceabilityRealGraph:
    def test_req_to_component_links_populated(self):
        from agilev.graph.traceability import build_traceability

        g = _graph()
        impact = _impact("CR-AUTH-001", "Modify login to add MFA")
        requirements = [
            ("REQ-001", "Rate limit and MFA for login auth.py"),
            ("REQ-002", "Token revocation via token.py TokenStore"),
        ]
        result = build_traceability(g, impact, requirements)
        assert len(result.req_to_component_links) > 0, "Expected at least one req-to-component link"

    def test_component_to_test_links_populated(self):
        from agilev.graph.traceability import build_traceability

        g = _graph()
        impact = _impact("CR-AUTH-001", "Modify login to add MFA auth.py")
        requirements = [("REQ-001", "MFA support via login in auth.py")]
        result = build_traceability(g, impact, requirements)
        assert len(result.component_to_test_links) > 0, (
            "Expected at least one component-to-test link"
        )

    def test_gate_pass_when_all_components_linked(self):
        from agilev.graph.traceability import build_traceability

        g = _graph()
        impact = _impact("CR-AUTH-001", "Modify login token refresh auth.py")
        requirements = [
            ("REQ-001", "MFA auth login refresh token auth.py token.py"),
        ]
        result = build_traceability(g, impact, requirements)
        assert result.decision in ("pass", "pass_with_findings"), (
            f"Unexpected gate decision: {result.decision}"
        )

    def test_orphan_detected_for_unlinked_component(self):
        from agilev.graph.traceability import build_traceability

        g = _graph()
        impact = _impact("CR-DB-001", "Change database session pool size in db.py get_session")
        requirements = [("REQ-999", "UI tooltip color button widget")]
        # Provide changed_files so orphan detection has something to compare
        result = build_traceability(g, impact, requirements, changed_files=["src/db.py"])
        assert result.decision in ("pass_with_findings", "fail"), (
            f"Expected pass_with_findings or fail for unlinked db change. Got: {result.decision}"
        )

    def test_orphan_detected_for_unlinked_component(self):
        from agilev.graph.traceability import build_traceability

        g = _graph()
        impact = _impact("CR-DB-001", "Change database session pool size in db.py get_session")
        requirements = [("REQ-999", "UI tooltip color button widget")]
        # Provide changed_files so orphan detection has something to compare
        result = build_traceability(g, impact, requirements, changed_files=["src/db.py"])
        assert result.decision in ("pass_with_findings", "fail"), (
            f"Expected pass_with_findings or fail for unlinked db change. Got: {result.decision}"
        )
