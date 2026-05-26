"""SHA-256 hashing utilities for Understand Anything graph files.

Every knowledge graph loaded by Agile-V must be hashed before use. The hash is:
- Stored in the SystemGraph.source_graph_hash field.
- Written to .agile-v/understanding/knowledge_graph_hash.txt.
- Included in the evidence bundle manifest.

This ensures that the evidence bundle references an immutable graph snapshot.
"""

import hashlib
from pathlib import Path

from .errors import GraphHashError


def sha256_file(path: str | Path) -> str:
    """Compute the SHA-256 hash of a file.

    Reads the file in 1 MB chunks to handle large graph files without loading
    them entirely into memory.

    Args:
        path: Path to the file to hash.

    Returns:
        A string in the format ``sha256:<hex-digest>``.

    Raises:
        GraphHashError: If the file cannot be read.
    """
    path = Path(path)
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
    except OSError as exc:
        raise GraphHashError(str(path), str(exc)) from exc
    return "sha256:" + h.hexdigest()


def write_hash_file(hash_value: str, output_path: str | Path) -> None:
    """Write a hash string to a text file.

    Args:
        hash_value: The hash string (e.g. ``sha256:abc123...``).
        output_path: Destination file path.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(hash_value + "\n", encoding="utf-8")
