"""Traceability: link requirements to graph nodes, changed files, and tests.

This module implements the core logic of the ``graph-traceability-agent`` skill.
It produces a list of GraphTraceabilityLink objects that form the evidence chain:

    requirement → graph node → file → test → result

In v0.1 the linking is structural (from ImpactMap + test inventory).
Future versions can add LLM-assisted requirement-to-node matching and
automatic test-result parsing.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass, field

from .model import (
    AffectedComponent,
    GraphTraceabilityLink,
    ImpactMap,
    SystemGraph,
    SystemNode,
)

logger = logging.getLogger(__name__)


@dataclass
class TraceabilityResult:
    """Output of the traceability analysis.

    Attributes:
        links: All traceability links produced.
        orphan_requirements: Requirement IDs with no linked component or test.
        orphan_changes: File paths changed but not linked to any requirement.
        warnings: Non-fatal issues found during analysis.
        decision: 'pass', 'fail', or 'pass_with_findings'.
    """

    links: list[GraphTraceabilityLink] = field(default_factory=list)
    orphan_requirements: list[dict] = field(default_factory=list)
    orphan_changes: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    decision: str = "pass"  # "pass" | "fail" | "pass_with_findings"

    @property
    def req_to_component_links(self) -> list[dict]:
        """Machine-readable requirement-to-component links."""
        seen: set[tuple[str, str]] = set()
        result = []
        for link in self.links:
            key = (link.requirement_id, link.component_id)
            if key not in seen:
                seen.add(key)
                result.append(
                    {
                        "requirement_id": link.requirement_id,
                        "component_id": link.component_id,
                        "path": link.path,
                        "symbol": link.symbol,
                        "confidence": "high",
                    }
                )
        return result

    @property
    def component_to_test_links(self) -> list[dict]:
        """Machine-readable component-to-test links."""
        return [
            {
                "component_id": link.component_id,
                "path": link.path,
                "test_path": link.test_path,
                "evidence_path": link.evidence_path,
                "test_result": link.status,
            }
            for link in self.links
            if link.test_path
        ]


def build_traceability(
    graph: SystemGraph,
    impact_map: ImpactMap,
    requirements: Sequence[tuple[str, str]],
    changed_files: Sequence[str] | None = None,
    test_results: dict[str, str] | None = None,
) -> TraceabilityResult:
    """Build the graph traceability matrix.

    Args:
        graph: The normalized SystemGraph.
        impact_map: The ImpactMap produced by ``analyze_impact``.
        requirements: A sequence of (requirement_id, requirement_text) pairs.
            E.g. [("REQ-001", "Rate limit repeated login attempts."), ...]
        changed_files: File paths changed in the implementation diff.
            Used to detect orphan changes.
        test_results: A dict mapping test file path to result string
            (e.g. ``{"tests/auth/test_login.py": "pass"}``).

    Returns:
        A ``TraceabilityResult`` with links, orphans, warnings, and a decision.
    """
    result = TraceabilityResult()
    test_results = test_results or {}
    changed_files_set = set(changed_files or [])

    # Build a path → component map from the impact map.
    path_to_components: dict[str, list[AffectedComponent]] = {}
    for comp in impact_map.all_components:
        path_to_components.setdefault(comp.path, []).append(comp)

    # Track which requirements got at least one link.
    req_has_component: set[str] = set()
    req_has_test: set[str] = set()

    # --- Build links: requirement → component → test ---
    for req_id, req_text in requirements:
        # Find components whose path or symbol appears in the requirement text (naive).
        req_text_lower = req_text.lower()
        matched_components: list[AffectedComponent] = []

        for comp in impact_map.all_components:
            comp_name = (comp.symbol or comp.path.split("/")[-1]).lower()
            if comp_name in req_text_lower or comp.path.lower() in req_text_lower:
                matched_components.append(comp)

        # If no text match, fall back to all direct components.
        if not matched_components:
            matched_components = list(impact_map.direct_components)

        for comp in matched_components:
            req_has_component.add(req_id)

            # Find test nodes linked to this component in the graph.
            component_node = graph.node_by_id(comp.component_id)
            test_path: str | None = None
            test_result_status: str = "missing"

            if component_node:
                test_nodes = _find_test_nodes_for_component(graph, comp)
                if test_nodes:
                    tn = test_nodes[0]  # Use the first linked test.
                    test_path = tn.path or tn.name
                    test_result_status = test_results.get(test_path, "not_run")
                    req_has_test.add(req_id)

            # Also check test_results for files that match the component path.
            if not test_path:
                comp_basename = comp.path.split("/")[-1].split(".")[0]
                for tp, tr in test_results.items():
                    if comp_basename.lower() in tp.lower():
                        test_path = tp
                        test_result_status = tr
                        req_has_test.add(req_id)
                        break

            link = GraphTraceabilityLink(
                requirement_id=req_id,
                component_id=comp.component_id,
                path=comp.path,
                symbol=comp.symbol,
                test_path=test_path,
                evidence_path=".agile-v/tests/results.json" if test_path else None,
                status=_resolve_status(test_result_status),
            )
            result.links.append(link)

    # --- Orphan requirements ---
    for req_id, req_text in requirements:
        if req_id not in req_has_component:
            result.orphan_requirements.append(
                {
                    "requirement_id": req_id,
                    "issue": "No linked component found in impact map.",
                }
            )
        elif req_id not in req_has_test:
            result.orphan_requirements.append(
                {
                    "requirement_id": req_id,
                    "issue": "No linked test found.",
                }
            )

    # --- Orphan changes ---
    linked_paths = {link.path for link in result.links}
    for changed_path in changed_files_set:
        if changed_path not in linked_paths:
            result.orphan_changes.append(
                {
                    "path": changed_path,
                    "issue": "Changed but not linked to any requirement.",
                    "justification": None,
                }
            )

    # --- Decision ---
    failing_issues = [link for link in result.links if link.status == "failed"]
    if result.orphan_requirements and any(
        o["issue"].startswith("No linked component") for o in result.orphan_requirements
    ):
        result.decision = "fail"
        result.warnings.append(
            f"{len(result.orphan_requirements)} orphan requirement(s) with no component link."
        )
    elif failing_issues:
        result.decision = "fail"
        result.warnings.append(f"{len(failing_issues)} test(s) failed.")
    elif result.orphan_changes or result.orphan_requirements:
        result.decision = "pass_with_findings"
        if result.orphan_changes:
            result.warnings.append(
                f"{len(result.orphan_changes)} orphan change(s) require justification."
            )
    else:
        result.decision = "pass"

    logger.info(
        "Traceability: %d links, %d orphan reqs, %d orphan changes, decision=%s",
        len(result.links),
        len(result.orphan_requirements),
        len(result.orphan_changes),
        result.decision,
    )

    return result


def _find_test_nodes_for_component(
    graph: SystemGraph,
    component: AffectedComponent,
) -> list[SystemNode]:
    """Find test nodes linked to a component via the graph."""
    test_edge_types = {"tests", "covers"}
    test_node_ids = {
        e.source
        for e in graph.edges
        if e.type in test_edge_types and e.target == component.component_id
    }
    node_map = {n.id: n for n in graph.nodes}
    return [node_map[nid] for nid in test_node_ids if nid in node_map]


def _resolve_status(raw_status: str) -> str:
    """Normalize a test result string to a traceability status."""
    s = (raw_status or "").lower().strip()
    if s in ("pass", "passed", "ok", "success"):
        return "verified"
    if s in ("fail", "failed", "error", "failure"):
        return "failed"
    if s in ("skip", "skipped", "not_run", "not run"):
        return "not_applicable"
    return "missing"
