"""Impact analysis: map a change request to affected graph components.

This module implements the core logic of the ``impact-analysis-agent`` skill.
It takes a SystemGraph and a change request description and produces an ImpactMap.

The analysis is heuristic:
- Direct components are found by keyword matching the change request against
  node names, paths, symbols, and summaries.
- Indirect components are found by graph traversal (1–2 hops from direct nodes).
- Test nodes linked to affected components are flagged as required regression tests.
- Confidence degrades with traversal distance.

This is intentionally simple in v0.1. Future versions can add LLM-assisted
relevance scoring, architectural layer filtering, and risk inference.
"""

from __future__ import annotations

import logging

from .model import (
    AffectedComponent,
    ImpactMap,
    ImpactRisk,
    SystemGraph,
    SystemNode,
)
from .queries import (
    extract_keywords_from_change_request,
    find_nodes_by_keyword,
    get_neighbors,
    get_test_nodes_for,
)

logger = logging.getLogger(__name__)

# Edge types that indicate a meaningful dependency relationship.
_DEPENDENCY_EDGE_TYPES = ["imports", "calls", "contains", "extends", "implements", "depends_on"]


def analyze_impact(
    graph: SystemGraph,
    change_request_id: str,
    change_request_text: str,
    indirect_hops: int = 2,
) -> ImpactMap:
    """Produce an ImpactMap from a change request and a SystemGraph.

    Args:
        graph: The normalized SystemGraph.
        change_request_id: ID of the change request (e.g. ``CR-001``).
        change_request_text: Plain-English description of the change.
        indirect_hops: Number of hops to traverse for indirect impact (default 2).

    Returns:
        An ``ImpactMap`` with direct and indirect components, required tests, and risks.
    """
    keywords = extract_keywords_from_change_request(change_request_text)
    logger.info("Impact analysis keywords: %s", keywords)

    # --- Direct components: keyword match ---
    direct_nodes = find_nodes_by_keyword(graph, keywords)
    logger.info("Direct matches: %d nodes", len(direct_nodes))

    direct_components = [
        AffectedComponent(
            component_id=node.id,
            path=node.path or node.name,
            symbol=node.symbol,
            impact_type="modify",
            reason=f"Keyword match in name/path/summary for change: '{change_request_text[:80]}'.",
            confidence="high",
        )
        for node in direct_nodes
    ]

    direct_ids = {n.id for n in direct_nodes}

    # --- Indirect components: graph traversal ---
    indirect_seen: set[str] = set(direct_ids)
    indirect_nodes: list[SystemNode] = []

    for direct_node in direct_nodes:
        neighbors = get_neighbors(
            graph,
            direct_node.id,
            edge_types=_DEPENDENCY_EDGE_TYPES,
            direction="both",
            hops=indirect_hops,
        )
        for neighbor in neighbors:
            if neighbor.id not in indirect_seen:
                indirect_seen.add(neighbor.id)
                indirect_nodes.append(neighbor)

    logger.info("Indirect matches: %d nodes", len(indirect_nodes))

    indirect_components = [
        AffectedComponent(
            component_id=node.id,
            path=node.path or node.name,
            symbol=node.symbol,
            impact_type="review",
            reason=f"Indirect dependency on a directly affected component (≤{indirect_hops} hops).",
            confidence="medium",
        )
        for node in indirect_nodes
    ]

    # --- Required regression tests ---
    all_affected_ids = direct_ids | {n.id for n in indirect_nodes}
    test_paths: list[str] = []
    seen_test_paths: set[str] = set()

    # 1. If a test node was itself a direct/indirect match, include it immediately.
    for node_id in all_affected_ids:
        node = graph.node_by_id(node_id)
        if node and node.type == "test":
            path = node.path or node.name
            if path not in seen_test_paths:
                seen_test_paths.add(path)
                test_paths.append(path)

    # 2. Follow explicit "tests" / "covers" edges from affected nodes.
    for node_id in all_affected_ids:
        test_nodes = get_test_nodes_for(graph, node_id)
        for tn in test_nodes:
            path = tn.path or tn.name
            if path not in seen_test_paths:
                seen_test_paths.add(path)
                test_paths.append(path)

    # 3. Heuristic: include test nodes whose name or summary references an affected file.
    for node in graph.nodes:
        if node.type == "test" and node.id not in all_affected_ids:
            for affected_id in all_affected_ids:
                affected_node = graph.node_by_id(affected_id)
                if affected_node and affected_node.path:
                    if (
                        node.summary and affected_node.path.split("/")[-1] in (node.summary or "")
                    ) or (
                        node.name and affected_node.path.split("/")[-1].split(".")[0] in node.name
                    ):
                        path = node.path or node.name
                        if path not in seen_test_paths:
                            seen_test_paths.add(path)
                            test_paths.append(path)

    logger.info("Required regression tests: %d", len(test_paths))

    # --- Basic risks ---
    risks = _infer_risks(direct_nodes, indirect_nodes, change_request_text)

    # --- Assumptions ---
    assumptions = [
        "Keywords extracted from the change request may not capture all affected components.",
        "Indirect impact traversal is limited to dependency edges; other relationship types are excluded.",
        "Test node detection relies on graph 'tests'/'covers' edges; tests not in the graph may be missed.",
    ]
    if not direct_nodes:
        assumptions.insert(
            0,
            "No nodes matched the change request keywords. The impact map may be incomplete.",
        )

    confidence = "high" if direct_nodes else ("medium" if indirect_nodes else "low")

    return ImpactMap(
        change_request_id=change_request_id,
        summary=change_request_text[:200],
        direct_components=direct_components,
        indirect_components=indirect_components,
        required_tests=test_paths,
        risks=risks,
        assumptions=assumptions,
        confidence=confidence,
    )


def _infer_risks(
    direct_nodes: list[SystemNode],
    indirect_nodes: list[SystemNode],
    change_request_text: str,
) -> list[ImpactRisk]:
    """Infer basic risks from the affected components and change description.

    This is a heuristic v0.1 implementation. It flags:
    - Shared/utility nodes affected indirectly (regression risk).
    - Test nodes affected (test suite may need updating).
    - Auth/security-related nodes (security regression risk).
    """
    risks: list[ImpactRisk] = []
    risk_counter = 1

    def make_id() -> str:
        nonlocal risk_counter
        rid = f"RISK-{risk_counter:03d}"
        risk_counter += 1
        return rid

    # Security-sensitive terms in node names or change request.
    security_terms = {"auth", "login", "token", "password", "secret", "key", "permission", "role"}
    all_nodes = direct_nodes + indirect_nodes
    security_nodes = [
        n
        for n in all_nodes
        if any(t in (n.name or "").lower() for t in security_terms)
        or any(t in change_request_text.lower() for t in security_terms)
    ]
    if security_nodes:
        risks.append(
            ImpactRisk(
                risk_id=make_id(),
                description="Security-sensitive components are in the impact scope.",
                severity="high",
                mitigation="Ensure security regression tests are included and reviewed.",
                verification="Run security test suite. Red Team to review auth behavior.",
            )
        )

    # Utility/shared modules — anything named "util", "helper", "common", "shared".
    shared_terms = {"util", "helper", "common", "shared", "base", "core"}
    shared_nodes = [
        n for n in indirect_nodes if any(t in (n.name or "").lower() for t in shared_terms)
    ]
    if shared_nodes:
        risks.append(
            ImpactRisk(
                risk_id=make_id(),
                description=f"Shared/utility components are indirectly affected: "
                f"{', '.join(n.name for n in shared_nodes[:3])}.",
                severity="medium",
                mitigation="Run regression tests for all consumers of affected shared modules.",
                verification="CI regression test suite pass.",
            )
        )

    # No direct matches at all — low-confidence analysis.
    if not direct_nodes:
        risks.append(
            ImpactRisk(
                risk_id=make_id(),
                description="No nodes matched the change request keywords. "
                "The impact analysis is based on indirect graph traversal only.",
                severity="medium",
                mitigation="Manually review the change scope against the system overview.",
                verification="Human reviewer confirms impact map before Gate 1.",
            )
        )

    return risks
