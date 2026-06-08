"""Normalizer: convert raw Understand Anything nodes and edges into Agile-V SystemNode/SystemEdge.

Rules:
- Node type is mapped from the source concept using _NODE_TYPE_MAP.
- Unknown types are mapped to "unknown".
- Missing IDs receive a synthetic ID (node-<index>).
- Unknown fields are preserved in the ``raw`` dict.
- Edge type is mapped from the source relationship using _EDGE_TYPE_MAP.
- Edges referencing unknown node IDs are included with confidence=low and a warning.
- All warnings are accumulated and returned for the adapter metadata.
"""

from __future__ import annotations

import logging
from typing import Any

from ...graph.model import SystemEdge, SystemNode

logger = logging.getLogger(__name__)

# Maps source node type strings (lower-cased) to Agile-V type literals.
_NODE_TYPE_MAP: dict[str, str] = {
    "file": "file",
    "source_file": "file",
    "source file": "file",
    "function": "function",
    "method": "function",
    "procedure": "function",
    "class": "class",
    "struct": "class",
    "interface": "class",
    "enum": "class",
    "module": "module",
    "package": "module",
    "namespace": "module",
    "domain": "domain",
    "flow": "flow",
    "workflow": "flow",
    "pipeline": "flow",
    "step": "step",
    "test": "test",
    "test_file": "test",
    "spec": "test",
    "doc": "doc",
    "documentation": "doc",
    "readme": "doc",
}

# Maps source edge type strings (lower-cased) to Agile-V type literals.
_EDGE_TYPE_MAP: dict[str, str] = {
    "import": "imports",
    "imports": "imports",
    "require": "imports",
    "requires": "imports",
    "call": "calls",
    "calls": "calls",
    "invokes": "calls",
    "contains": "contains",
    "has": "contains",
    "owns": "contains",
    "extends": "extends",
    "inherits": "extends",
    "subclasses": "extends",
    "implements": "implements",
    "realizes": "implements",
    "uses": "uses",
    "references": "uses",
    "reads": "uses",
    "depends": "depends_on",
    "depends_on": "depends_on",
    "dependency": "depends_on",
    "tests": "tests",
    "verifies": "tests",
    "covers": "tests",
    "documents": "documents",
    "describes": "documents",
}


def normalize_node(raw_node: Any, index: int, warnings: list[str]) -> SystemNode:
    """Convert a raw source node dict into a SystemNode.

    Args:
        raw_node: The raw node object from the graph JSON.
        index: The 0-based index of this node in the source array (used for synthetic IDs).
        warnings: Mutable list; normalization warnings are appended here.

    Returns:
        A ``SystemNode`` with normalized fields and ``raw`` preserving the source.
    """
    if not isinstance(raw_node, dict):
        warnings.append(f"Node at index {index} is not a dict; skipping.")
        return SystemNode(
            id=f"node-{index}",
            type="unknown",
            name=f"<invalid-node-{index}>",
            raw={"_invalid": raw_node},
        )

    # ID resolution.
    node_id = (
        raw_node.get("id") or raw_node.get("node_id") or raw_node.get("key") or f"node-{index}"
    )
    if str(node_id) == f"node-{index}" and ("id" not in raw_node and "node_id" not in raw_node):
        warnings.append(f"Node at index {index} has no 'id' field; using synthetic id '{node_id}'.")

    # Type resolution.
    raw_type = raw_node.get("type") or raw_node.get("kind") or raw_node.get("node_type") or ""
    node_type = _NODE_TYPE_MAP.get(str(raw_type).lower().strip(), "unknown")
    if node_type == "unknown" and raw_type:
        warnings.append(f"Node '{node_id}' has unknown type '{raw_type}'; mapped to 'unknown'.")

    # Name and path.
    name = (
        raw_node.get("name")
        or raw_node.get("label")
        or raw_node.get("title")
        or raw_node.get("path")
        or str(node_id)
    )
    path = raw_node.get("path") or raw_node.get("file") or raw_node.get("filepath")
    symbol = raw_node.get("symbol") or raw_node.get("qualified_name") or raw_node.get("full_name")

    return SystemNode(
        id=str(node_id),
        type=node_type,
        name=str(name),
        path=str(path) if path else None,
        symbol=str(symbol) if symbol else None,
        language=raw_node.get("language") or raw_node.get("lang"),
        layer=raw_node.get("layer") or raw_node.get("tier"),
        summary=raw_node.get("summary") or raw_node.get("description") or raw_node.get("doc"),
        tags=list(raw_node.get("tags") or raw_node.get("labels") or []),
        raw=raw_node,
    )


def normalize_edge(
    raw_edge: Any,
    index: int,
    known_ids: set[str],
    warnings: list[str],
) -> SystemEdge:
    """Convert a raw source edge dict into a SystemEdge.

    Args:
        raw_edge: The raw edge object from the graph JSON.
        index: The 0-based index of this edge in the source array.
        known_ids: Set of all normalized node IDs; used to detect dangling edges.
        warnings: Mutable list; normalization warnings are appended here.

    Returns:
        A ``SystemEdge`` with normalized fields.
    """
    if not isinstance(raw_edge, dict):
        warnings.append(f"Edge at index {index} is not a dict; skipping.")
        return SystemEdge(
            id=f"edge-{index}",
            source="unknown",
            target="unknown",
            type="unknown",
            raw={"_invalid": raw_edge},
        )

    edge_id = raw_edge.get("id") or raw_edge.get("edge_id") or f"edge-{index}"

    source = str(raw_edge.get("source") or raw_edge.get("from") or raw_edge.get("src") or "unknown")
    target = str(raw_edge.get("target") or raw_edge.get("to") or raw_edge.get("dst") or "unknown")

    # Flag dangling edges.
    confidence = "high"
    if source not in known_ids and source != "unknown":
        warnings.append(
            f"Edge '{edge_id}' source '{source}' is not in the node list; confidence set to low."
        )
        confidence = "low"
    if target not in known_ids and target != "unknown":
        warnings.append(
            f"Edge '{edge_id}' target '{target}' is not in the node list; confidence set to low."
        )
        confidence = "low"

    # Type resolution.
    raw_type = (
        raw_edge.get("type")
        or raw_edge.get("kind")
        or raw_edge.get("relationship")
        or raw_edge.get("relation")
        or ""
    )
    edge_type = _EDGE_TYPE_MAP.get(str(raw_type).lower().strip(), "unknown")
    if edge_type == "unknown" and raw_type:
        warnings.append(f"Edge '{edge_id}' has unknown type '{raw_type}'; mapped to 'unknown'.")

    return SystemEdge(
        id=str(edge_id),
        source=source,
        target=target,
        type=edge_type,
        confidence=confidence,
        raw=raw_edge,
    )


def normalize_graph(
    raw_nodes: list[Any],
    raw_edges: list[Any],
) -> tuple[list[SystemNode], list[SystemEdge], list[str]]:
    """Normalize raw node and edge lists into SystemNode and SystemEdge instances.

    Args:
        raw_nodes: List of raw node dicts from the graph JSON.
        raw_edges: List of raw edge dicts from the graph JSON.

    Returns:
        A tuple of (nodes, edges, warnings).
    """
    warnings: list[str] = []

    nodes = [normalize_node(n, i, warnings) for i, n in enumerate(raw_nodes)]
    known_ids = {n.id for n in nodes}
    edges = [normalize_edge(e, i, known_ids, warnings) for i, e in enumerate(raw_edges)]

    return nodes, edges, warnings
