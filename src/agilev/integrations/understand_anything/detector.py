"""Detect Understand Anything output files in a repository.

This module provides functions to locate the knowledge graph and diff overlay
files that Understand Anything generates. It does not parse them — that is
the job of loader.py.
"""

from pathlib import Path

DEFAULT_GRAPH_PATH = ".understand-anything/knowledge-graph.json"
DEFAULT_DIFF_PATH = ".understand-anything/diff-overlay.json"

# Alternative paths to check if the default is not found.
ALTERNATIVE_GRAPH_PATHS = [
    ".understand-anything/graph.json",
    ".understand-anything/knowledge_graph.json",
    "understand-anything/knowledge-graph.json",
]


def find_understand_graph(repo_root: str | Path) -> Path | None:
    """Return the path to the Understand Anything knowledge graph, or None.

    Checks the default path first, then alternative paths.

    Args:
        repo_root: Root directory of the repository.

    Returns:
        Path to the graph file if found, or None.
    """
    root = Path(repo_root)
    default = root / DEFAULT_GRAPH_PATH
    if default.exists():
        return default
    for alt in ALTERNATIVE_GRAPH_PATHS:
        candidate = root / alt
        if candidate.exists():
            return candidate
    return None


def find_understand_diff(repo_root: str | Path) -> Path | None:
    """Return the path to the Understand Anything diff overlay, or None.

    Args:
        repo_root: Root directory of the repository.

    Returns:
        Path to the diff overlay file if found, or None.
    """
    root = Path(repo_root)
    path = root / DEFAULT_DIFF_PATH
    return path if path.exists() else None


def graph_is_available(repo_root: str | Path) -> bool:
    """Return True if a knowledge graph is available in the repository.

    Args:
        repo_root: Root directory of the repository.
    """
    return find_understand_graph(repo_root) is not None
