"""Custom exceptions for the Understand Anything adapter."""


class UnderstandAnythingError(Exception):
    """Base class for all Understand Anything adapter errors."""


class GraphNotFoundError(UnderstandAnythingError):
    """Raised when no knowledge graph file can be found at the expected path.

    This is not a fatal error for Agile-V — the tool falls back to standalone mode.
    """

    def __init__(self, path: str) -> None:
        self.path = path
        super().__init__(f"Knowledge graph not found at: {path}")


class GraphLoadError(UnderstandAnythingError):
    """Raised when the knowledge graph file exists but cannot be read or parsed.

    Exit code 2: graph found but invalid/unreadable.
    """

    def __init__(self, path: str, reason: str) -> None:
        self.path = path
        self.reason = reason
        super().__init__(f"Cannot load knowledge graph at '{path}': {reason}")


class GraphHashError(UnderstandAnythingError):
    """Raised when the SHA-256 hash of the knowledge graph cannot be computed.

    This blocks evidence export, since the graph hash is required for reproducibility.
    """

    def __init__(self, path: str, reason: str) -> None:
        self.path = path
        self.reason = reason
        super().__init__(f"Cannot hash knowledge graph at '{path}': {reason}")
