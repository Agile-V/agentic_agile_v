"""High-level adapter: orchestrates detection, loading, hashing, and normalization.

Usage::

    adapter = UnderstandAnythingAdapter(repo_root=".")
    result = adapter.load()

    if result.graph is not None:
        print(f"Loaded {len(result.graph.nodes)} nodes, hash={result.graph.source_graph_hash}")
    else:
        print("No graph available; running in standalone mode.")
        print(result.error)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from ...graph.model import SystemGraph
from .detector import find_understand_graph, find_understand_diff
from .errors import GraphLoadError, GraphHashError, GraphNotFoundError
from .hashing import sha256_file
from .loader import load_graph_json, detect_nodes, detect_edges
from .normalizer import normalize_graph

logger = logging.getLogger(__name__)

ADAPTER_NAME = "understand-anything-adapter"
ADAPTER_VERSION = "0.1.0"


@dataclass
class AdapterResult:
    """Result of an adapter load attempt.

    Attributes:
        graph: The normalized SystemGraph, or None if the graph was not found or failed to load.
        graph_path: The path to the source graph file, if found.
        diff_path: The path to the diff overlay file, if found.
        graph_hash: SHA-256 hex digest of the source graph file (``sha256:<hex>``), or None.
        error: A human-readable error message if the graph could not be loaded.
        warnings: List of normalization warnings.
        mode: One of 'consume-graph' (graph found), 'standalone' (no graph).
    """

    graph: SystemGraph | None = None
    graph_path: Path | None = None
    diff_path: Path | None = None
    graph_hash: str | None = None
    error: str | None = None
    warnings: list[str] = field(default_factory=list)
    mode: str = "standalone"


class UnderstandAnythingAdapter:
    """Adapter that loads and normalizes an Understand Anything knowledge graph.

    This adapter:
    1. Detects the graph file location.
    2. Hashes the file for evidence reproducibility.
    3. Loads the JSON tolerantly.
    4. Normalizes nodes and edges into Agile-V schema types.
    5. Returns an AdapterResult.

    It does NOT import or call any Understand Anything Python code.

    Args:
        repo_root: Root directory of the repository. Defaults to the current directory.
    """

    def __init__(self, repo_root: str | Path = ".") -> None:
        self.repo_root = Path(repo_root)

    def load(self, graph_path: str | Path | None = None) -> AdapterResult:
        """Detect, hash, load, and normalize the knowledge graph.

        Args:
            graph_path: Optional explicit path to the knowledge graph JSON.
                If provided, skips auto-detection and loads this file directly.
                Useful for testing and for non-standard repository layouts.

        Returns:
            An ``AdapterResult``. The ``.graph`` field is None if no graph was found
            or if loading failed. Check ``.error`` for the reason.
        """
        result = AdapterResult()

        # 1. Detect graph file (or use the explicitly provided path).
        if graph_path is not None:
            graph_path = Path(graph_path)
            if not graph_path.exists():
                result.error = f"Specified graph path does not exist: {graph_path}"
                logger.error(result.error)
                return result
        else:
            graph_path = find_understand_graph(self.repo_root)

        if graph_path is None:
            logger.info(
                "No Understand Anything knowledge graph found in %s. "
                "Running Agile-V in standalone mode.",
                self.repo_root,
            )
            result.error = (
                f"Knowledge graph not found in {self.repo_root}. "
                "Run Understand Anything to generate one, or proceed without it."
            )
            return result

        result.graph_path = graph_path
        result.mode = "consume-graph"
        logger.info("Found knowledge graph: %s", graph_path)

        # 2. Detect diff overlay (optional).
        result.diff_path = find_understand_diff(self.repo_root)

        # 3. Hash the graph file.
        try:
            graph_hash = sha256_file(graph_path)
        except GraphHashError as exc:
            result.error = str(exc)
            logger.error("Failed to hash graph: %s", exc)
            return result

        result.graph_hash = graph_hash

        # 4. Load JSON tolerantly.
        try:
            raw_data = load_graph_json(graph_path)
        except GraphLoadError as exc:
            result.error = str(exc)
            logger.error("Failed to load graph: %s", exc)
            return result

        # 5. Detect node and edge arrays.
        raw_nodes, node_key = detect_nodes(raw_data)
        raw_edges, edge_key = detect_edges(raw_data)

        if node_key:
            logger.info("Detected %d nodes from key '%s'.", len(raw_nodes), node_key)
        if edge_key:
            logger.info("Detected %d edges from key '%s'.", len(raw_edges), edge_key)

        # 6. Normalize.
        nodes, edges, warnings = normalize_graph(raw_nodes, raw_edges)

        for w in warnings:
            logger.warning(w)

        result.warnings = warnings

        # 7. Thread any source-level metadata from the raw JSON (e.g. "meta", "metadata" keys).
        source_meta: dict = {}
        for meta_key in ("meta", "metadata", "info"):
            if isinstance(raw_data.get(meta_key), dict):
                source_meta = raw_data[meta_key]
                break

        # 8. Build the SystemGraph.
        result.graph = SystemGraph(
            source="understand-anything",
            source_graph_path=str(graph_path),
            source_graph_hash=graph_hash,
            generated_at=datetime.now(tz=timezone.utc).isoformat(),
            nodes=nodes,
            edges=edges,
            metadata={
                **source_meta,
                "adapter_name": ADAPTER_NAME,
                "adapter_version": ADAPTER_VERSION,
                "source": "Lum1104/Understand-Anything",
                "source_graph_path": str(graph_path),
                "source_graph_hash": graph_hash,
                "node_key_detected": node_key,
                "edge_key_detected": edge_key,
                "normalization_warnings": warnings,
            },
        )

        logger.info(
            "Graph normalized: %d nodes, %d edges, %d warnings.",
            len(nodes),
            len(edges),
            len(warnings),
        )

        return result
