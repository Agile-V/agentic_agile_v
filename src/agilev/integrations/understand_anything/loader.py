"""Tolerant JSON loader for Understand Anything knowledge graph files.

The loader does not assume a specific schema. It:
1. Reads JSON with UTF-8 (falling back to Latin-1).
2. Detects likely node and edge arrays using a prioritized search strategy.
3. Returns the raw parsed dict for the normalizer to process.
4. Records warnings for anything unexpected.

This approach protects Agile-V from Understand Anything schema changes.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from .errors import GraphLoadError

logger = logging.getLogger(__name__)

# Search keys for node arrays, in priority order.
_NODE_KEYS = ["nodes", "graph.nodes", "files", "functions", "classes", "entities"]

# Search keys for edge arrays, in priority order.
_EDGE_KEYS = ["edges", "relationships", "links", "dependencies"]

# Warn if the graph is larger than this threshold.
_LARGE_GRAPH_BYTES = 50 * 1024 * 1024  # 50 MB


def load_graph_json(path: str | Path) -> dict[str, Any]:
    """Load and return the raw knowledge graph JSON as a Python dict.

    Args:
        path: Path to the ``.json`` graph file.

    Returns:
        The parsed JSON document as a dict.

    Raises:
        GraphLoadError: If the file cannot be read or is not valid JSON.
    """
    path = Path(path)

    # Warn about large files.
    try:
        size = path.stat().st_size
        if size > _LARGE_GRAPH_BYTES:
            logger.warning(
                "[LARGE GRAPH] %s is %.1f MB. Only relevant subgraphs will be "
                "passed to agent context windows.",
                path,
                size / (1024 * 1024),
            )
    except OSError:
        pass

    # Try UTF-8 first, fall back to Latin-1.
    try:
        for encoding in ("utf-8", "latin-1"):
            try:
                text = path.read_text(encoding=encoding)
                if encoding == "latin-1":
                    logger.warning(
                        "[WARN] Graph file %s is not UTF-8; loaded with Latin-1 fallback. "
                        "Some characters may be incorrect.",
                        path,
                    )
                break
            except UnicodeDecodeError:
                continue
        else:
            raise GraphLoadError(str(path), "File is not UTF-8 or Latin-1 encoded.")
    except OSError as exc:
        raise GraphLoadError(str(path), str(exc)) from exc

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise GraphLoadError(str(path), f"Invalid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise GraphLoadError(
            str(path),
            f"Expected a JSON object at the top level, got {type(data).__name__}.",
        )

    return data


def detect_nodes(data: dict[str, Any]) -> tuple[list[Any], str | None]:
    """Detect the node array from the raw graph dict.

    Searches keys in priority order. Handles the ``graph.nodes`` nested case.

    Args:
        data: Raw JSON dict from ``load_graph_json``.

    Returns:
        A tuple of (node_list, detected_key). If no nodes are found, returns
        ([], None) and logs a warning.
    """
    for key in _NODE_KEYS:
        if "." in key:
            # Nested key, e.g. "graph.nodes"
            outer, inner = key.split(".", 1)
            outer_val = data.get(outer)
            if isinstance(outer_val, dict):
                val = outer_val.get(inner)
                if isinstance(val, list):
                    return val, key
        else:
            val = data.get(key)
            if isinstance(val, list):
                return val, key

    logger.warning(
        "[WARN] No recognizable node array found in graph. "
        "Checked keys: %s. Returning empty node list.",
        _NODE_KEYS,
    )
    return [], None


def detect_edges(data: dict[str, Any]) -> tuple[list[Any], str | None]:
    """Detect the edge array from the raw graph dict.

    Args:
        data: Raw JSON dict from ``load_graph_json``.

    Returns:
        A tuple of (edge_list, detected_key). If no edges are found, returns
        ([], None) and logs an info message (missing edges is not a warning).
    """
    # Also check graph.edges nested form.
    graph_obj = data.get("graph")
    if isinstance(graph_obj, dict):
        for key in _EDGE_KEYS:
            val = graph_obj.get(key)
            if isinstance(val, list):
                return val, f"graph.{key}"

    for key in _EDGE_KEYS:
        val = data.get(key)
        if isinstance(val, list):
            return val, key

    logger.info(
        "No edge array found in graph. Checked keys: %s. Continuing without edges.",
        _EDGE_KEYS,
    )
    return [], None
