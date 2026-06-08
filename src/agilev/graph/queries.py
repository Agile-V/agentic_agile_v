"""Graph query helpers: keyword search, neighbor traversal, path-based lookup.

These functions operate on a normalized SystemGraph and return subsets of nodes
and edges relevant to a change request or query.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from .model import SystemGraph, SystemNode


def find_nodes_by_keyword(graph: SystemGraph, keywords: Iterable[str]) -> list[SystemNode]:
    """Return nodes whose name, path, symbol, or summary matches any keyword.

    Matching is case-insensitive substring matching.

    Args:
        graph: The SystemGraph to search.
        keywords: Iterable of search terms.

    Returns:
        Deduplicated list of matching SystemNode objects.
    """
    keywords_lower = [k.lower() for k in keywords if k]
    matched: dict[str, SystemNode] = {}

    for node in graph.nodes:
        searchable = " ".join(
            filter(None, [node.name, node.path, node.symbol, node.summary])
        ).lower()
        for kw in keywords_lower:
            if kw in searchable:
                matched[node.id] = node
                break

    return list(matched.values())


def find_nodes_by_path(graph: SystemGraph, path: str) -> list[SystemNode]:
    """Return all nodes whose path matches exactly or contains the given path fragment.

    Args:
        graph: The SystemGraph to search.
        path: File path or path fragment.

    Returns:
        Matching SystemNode objects.
    """
    path_lower = path.lower()
    return [n for n in graph.nodes if n.path and path_lower in n.path.lower()]


def get_neighbors(
    graph: SystemGraph,
    node_id: str,
    edge_types: list[str] | None = None,
    direction: str = "both",
    hops: int = 1,
) -> list[SystemNode]:
    """Return neighboring nodes within ``hops`` traversal steps.

    Args:
        graph: The SystemGraph to traverse.
        node_id: Starting node ID.
        edge_types: If provided, only traverse edges of these types.
        direction: ``'out'`` (follow source→target), ``'in'`` (follow target→source),
                   or ``'both'``.
        hops: Number of traversal steps (1 = immediate neighbors).

    Returns:
        List of neighboring SystemNode objects (excluding the starting node).
    """
    visited: set[str] = {node_id}
    frontier: set[str] = {node_id}

    for _ in range(hops):
        next_frontier: set[str] = set()
        for nid in frontier:
            for edge in graph.edges:
                if edge_types and edge.type not in edge_types:
                    continue
                if direction in ("out", "both") and edge.source == nid:
                    if edge.target not in visited:
                        next_frontier.add(edge.target)
                if direction in ("in", "both") and edge.target == nid:
                    if edge.source not in visited:
                        next_frontier.add(edge.source)
        visited.update(next_frontier)
        frontier = next_frontier

    result_ids = visited - {node_id}
    node_map = {n.id: n for n in graph.nodes}
    return [node_map[nid] for nid in result_ids if nid in node_map]


def get_test_nodes_for(graph: SystemGraph, node_id: str) -> list[SystemNode]:
    """Return test nodes that directly test the given node.

    Follows edges of type ``tests`` or ``covers`` pointing TO the given node_id,
    and returns the source nodes (the test nodes).

    Args:
        graph: The SystemGraph.
        node_id: ID of the node being tested.

    Returns:
        List of test SystemNode objects.
    """
    test_edge_types = {"tests", "covers"}
    test_node_ids = {
        e.source for e in graph.edges if e.type in test_edge_types and e.target == node_id
    }
    node_map = {n.id: n for n in graph.nodes}
    return [node_map[nid] for nid in test_node_ids if nid in node_map]


def extract_keywords_from_change_request(text: str) -> list[str]:
    """Extract likely identifier keywords from a change request description.

    Splits on whitespace and punctuation, removes stop words, and returns
    terms that look like code identifiers (camelCase, snake_case, or PascalCase).

    Args:
        text: Plain-English change request text.

    Returns:
        List of candidate keywords for graph search.
    """
    # Extract words that look like code identifiers.
    tokens = re.findall(r"\b[a-zA-Z][a-zA-Z0-9_]{2,}\b", text)

    stop_words = {
        # Articles / conjunctions / prepositions
        "the",
        "and",
        "for",
        "with",
        "from",
        "this",
        "that",
        "into",
        "onto",
        "upon",
        "about",
        "after",
        "before",
        "during",
        "without",
        "within",
        "between",
        "through",
        "against",
        "across",
        "around",
        "along",
        "its",
        "our",
        "their",
        "also",
        "both",
        # Modals / auxiliaries
        "are",
        "has",
        "have",
        "had",
        "was",
        "were",
        "been",
        "being",
        "will",
        "would",
        "should",
        "could",
        "shall",
        "might",
        "must",
        "need",
        "needs",
        "can",
        "may",
        # Common action verbs (not code identifiers)
        "add",
        "added",
        "adding",
        "update",
        "updated",
        "updating",
        "change",
        "changed",
        "changing",
        "remove",
        "removed",
        "removing",
        "delete",
        "deleted",
        "deleting",
        "create",
        "created",
        "creating",
        "implement",
        "implemented",
        "implementing",
        "make",
        "makes",
        "making",
        "use",
        "used",
        "using",
        "modify",
        "modified",
        "modifying",
        "support",
        "supports",
        "supported",
        "accept",
        "accepts",
        "accepted",
        "preserve",
        "preserved",
        "preserving",
        "remain",
        "remains",
        "remained",
        "ensure",
        "ensures",
        "ensured",
        "allow",
        "allows",
        "allowed",
        "return",
        "returns",
        "returned",
        "include",
        "includes",
        "included",
        "provide",
        "provides",
        "provided",
        "handle",
        "handles",
        "handled",
        "expose",
        "exposes",
        "exposed",
        "enable",
        "enables",
        "enabled",
        # Common English words that are not identifiers
        "new",
        "old",
        "all",
        "any",
        "each",
        "some",
        "one",
        "two",
        "when",
        "where",
        "what",
        "which",
        "who",
        "how",
        "not",
        "only",
        "just",
        "now",
        "then",
        "here",
        "there",
        "based",
        "given",
        "done",
        "same",
        "like",
        "well",
        "still",
        "intact",
        "valid",
        "invalid",
        "alongside",
        "password",
        "issuance",
        "code",
        # Generic technical words that match too many nodes
        "function",
        "method",
        "class",
        "module",
        "file",
        "service",
        "time",
        "via",
        "endpoint",
        "request",
        "response",
        "data",
        "type",
        "value",
        "list",
        "dict",
        "set",
        "map",
        "key",
    }

    return [t for t in tokens if t.lower() not in stop_words]
