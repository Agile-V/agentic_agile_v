"""Agile-V normalized graph data models.

These dataclasses define the stable internal schema that all Agile-V graph
consumers use. They are independent of the external graph format.

Schema version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

# Valid node type literals.
NodeType = Literal[
    "file", "function", "class", "module", "domain", "flow", "step", "test", "doc", "unknown"
]

# Valid edge type literals.
EdgeType = Literal[
    "imports",
    "calls",
    "contains",
    "extends",
    "implements",
    "uses",
    "tests",
    "documents",
    "depends_on",
    "unknown",
]

# Valid confidence levels.
ConfidenceLevel = Literal["high", "medium", "low"]

# Valid impact types.
ImpactType = Literal["modify", "add", "remove", "review", "test-only", "doc-only"]

SCHEMA_VERSION = "1.0.0"


@dataclass
class SystemNode:
    """A normalized node in the system knowledge graph.

    Attributes:
        id: Unique node identifier (from source or synthetic).
        type: Normalized node type.
        name: Human-readable name (function name, class name, file basename, etc.).
        path: File path relative to the repository root, if applicable.
        symbol: Qualified symbol name (e.g. ``AuthController.login``).
        language: Programming language (e.g. ``typescript``, ``python``).
        layer: Architectural layer (e.g. ``api``, ``service``, ``data``).
        summary: Plain-English description of the node, if available.
        tags: List of tags or labels from the source graph.
        raw: The original source dict, preserved for debugging and adapter upgrades.
    """

    id: str
    type: str  # NodeType — not enforced at runtime; validated by schema
    name: str
    path: str | None = None
    symbol: str | None = None
    language: str | None = None
    layer: str | None = None
    summary: str | None = None
    tags: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-serializable dict (excluding raw)."""
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "path": self.path,
            "symbol": self.symbol,
            "language": self.language,
            "layer": self.layer,
            "summary": self.summary,
            "tags": self.tags,
        }


@dataclass
class SystemEdge:
    """A normalized edge (relationship) between two nodes in the system graph.

    Attributes:
        id: Unique edge identifier.
        source: ID of the source node.
        target: ID of the target node.
        type: Normalized relationship type.
        confidence: Confidence level of this edge (from the source graph or inferred).
        raw: The original source dict.
    """

    id: str
    source: str
    target: str
    type: str  # EdgeType
    confidence: str = "high"  # ConfidenceLevel
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-serializable dict (excluding raw)."""
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "type": self.type,
            "confidence": self.confidence,
        }


@dataclass
class SystemGraph:
    """The normalized Agile-V system graph.

    This is the central data structure produced by the adapter and consumed by
    impact analysis, traceability, and evidence export.

    Attributes:
        source: The external tool that produced the original graph.
        source_graph_path: Path to the original graph file.
        source_graph_hash: SHA-256 hash of the original graph file.
        generated_at: ISO-8601 timestamp when this graph was normalized.
        nodes: List of normalized system nodes.
        edges: List of normalized system edges.
        metadata: Adapter metadata including warnings.
        schema_version: Version of this schema.
    """

    source: str
    source_graph_path: str
    source_graph_hash: str
    generated_at: str
    nodes: list[SystemNode] = field(default_factory=list)
    edges: list[SystemEdge] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-serializable dict."""
        return {
            "schema_version": self.schema_version,
            "source": self.source,
            "source_graph_path": self.source_graph_path,
            "source_graph_hash": self.source_graph_hash,
            "generated_at": self.generated_at,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "metadata": self.metadata,
        }

    def node_by_id(self, node_id: str) -> SystemNode | None:
        """Return the node with the given ID, or None."""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def nodes_by_path(self, path: str) -> list[SystemNode]:
        """Return all nodes with the given file path."""
        return [n for n in self.nodes if n.path == path]

    def edges_from(self, node_id: str) -> list[SystemEdge]:
        """Return all edges originating from the given node ID."""
        return [e for e in self.edges if e.source == node_id]

    def edges_to(self, node_id: str) -> list[SystemEdge]:
        """Return all edges targeting the given node ID."""
        return [e for e in self.edges if e.target == node_id]


@dataclass
class AffectedComponent:
    """A single component identified as affected by a change request.

    Attributes:
        component_id: The SystemNode ID.
        path: File path of the component.
        symbol: Function or class name, if applicable.
        impact_type: How the component is affected.
        reason: Why this component is in the impact map.
        confidence: Confidence level of this impact prediction.
    """

    component_id: str
    path: str
    symbol: str | None
    impact_type: str  # ImpactType
    reason: str
    confidence: str = "high"  # ConfidenceLevel

    def to_dict(self) -> dict[str, Any]:
        return {
            "component_id": self.component_id,
            "path": self.path,
            "symbol": self.symbol,
            "impact_type": self.impact_type,
            "reason": self.reason,
            "confidence": self.confidence,
        }


@dataclass
class ImpactRisk:
    """A risk identified during impact analysis.

    Attributes:
        risk_id: Unique risk identifier (e.g. RISK-001).
        description: Plain-English risk description.
        severity: High / Medium / Low.
        mitigation: Proposed mitigation strategy.
        verification: How to verify the mitigation worked.
    """

    risk_id: str
    description: str
    severity: str  # "high" | "medium" | "low"
    mitigation: str = ""
    verification: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "risk_id": self.risk_id,
            "description": self.description,
            "severity": self.severity,
            "mitigation": self.mitigation,
            "verification": self.verification,
        }


@dataclass
class ImpactMap:
    """The complete impact map for a change request.

    Attributes:
        schema_version: Version of the ImpactMap schema.
        change_request_id: ID of the change request (e.g. CR-001).
        summary: Plain-English summary of the change.
        direct_components: Components directly affected.
        indirect_components: Components indirectly affected.
        required_tests: Test paths that should be run.
        risks: Identified risks.
        assumptions: Assumptions made during analysis.
        confidence: Overall confidence level.
    """

    change_request_id: str
    summary: str
    direct_components: list[AffectedComponent] = field(default_factory=list)
    indirect_components: list[AffectedComponent] = field(default_factory=list)
    required_tests: list[str] = field(default_factory=list)
    risks: list[ImpactRisk] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    confidence: str = "medium"  # ConfidenceLevel
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "change_request_id": self.change_request_id,
            "summary": self.summary,
            "direct_components": [c.to_dict() for c in self.direct_components],
            "indirect_components": [c.to_dict() for c in self.indirect_components],
            "required_tests": self.required_tests,
            "risks": [r.to_dict() for r in self.risks],
            "assumptions": self.assumptions,
            "confidence": self.confidence,
        }

    @property
    def all_components(self) -> list[AffectedComponent]:
        """Return direct and indirect components combined."""
        return self.direct_components + self.indirect_components


@dataclass
class GraphTraceabilityLink:
    """A single traceability link: requirement → graph node → file → test.

    Attributes:
        requirement_id: Agile-V requirement ID (e.g. REQ-001).
        component_id: SystemNode ID of the affected component.
        path: File path of the component.
        symbol: Function or class name.
        test_id: Test case ID (e.g. TEST-001).
        test_path: File path of the test.
        evidence_path: Path to the test result evidence.
        status: Verification status.
    """

    requirement_id: str
    component_id: str
    path: str
    symbol: str | None = None
    test_id: str | None = None
    test_path: str | None = None
    evidence_path: str | None = None
    status: str = "missing"  # "verified" | "failed" | "missing" | "not_applicable"

    def to_dict(self) -> dict[str, Any]:
        return {
            "requirement_id": self.requirement_id,
            "component_id": self.component_id,
            "path": self.path,
            "symbol": self.symbol,
            "test_id": self.test_id,
            "test_path": self.test_path,
            "evidence_path": self.evidence_path,
            "status": self.status,
        }
