"""Understand Anything integration adapter for Agile-V.

This package consumes Understand Anything knowledge graph outputs and normalizes
them into the Agile-V SystemGraph schema. It does NOT import or call any
Understand Anything Python code directly — it only reads the generated JSON files.

Usage::

    from agilev.integrations.understand_anything.adapter import UnderstandAnythingAdapter

    adapter = UnderstandAnythingAdapter(repo_root=".")
    result = adapter.load()
    if result.graph is not None:
        print(f"Loaded {len(result.graph.nodes)} nodes")
"""

from .adapter import AdapterResult, UnderstandAnythingAdapter
from .detector import find_understand_diff, find_understand_graph
from .errors import GraphHashError, GraphLoadError, GraphNotFoundError

__all__ = [
    "UnderstandAnythingAdapter",
    "AdapterResult",
    "find_understand_graph",
    "find_understand_diff",
    "GraphLoadError",
    "GraphHashError",
    "GraphNotFoundError",
]
