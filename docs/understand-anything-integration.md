# Understand Anything Integration — Runtime Guide

## Overview

This document describes the `agilev` runtime adapter for Understand Anything.

The adapter:
1. Detects an Understand Anything knowledge graph at `.understand-anything/knowledge-graph.json`.
2. Hashes the file (SHA-256) for evidence reproducibility.
3. Loads the JSON tolerantly (handles multiple known graph shapes).
4. Normalizes nodes and edges into Agile-V `SystemGraph` schema.
5. Enables impact analysis, graph traceability, and evidence bundle generation.

---

## Installation

```bash
pip install -e .[dev]
```

This installs the `agilev` package from `src/` in editable mode, plus `pytest`, `ruff`, and
`mypy` for development.

Python 3.11+ is required.

---

## Supported modes

| Mode | Description |
|---|---|
| `standalone` | No graph found. Agile-V runs without codebase context. All standard skills work unchanged. |
| `consume-graph` | Graph found at `.understand-anything/knowledge-graph.json`. Adapter loads and normalizes it. |
| `invoke-understand` | (Future) Agile-V triggers Understand Anything before running. Not in v0.1. |

---

## Quick usage

### Python API

```python
from agilev.integrations.understand_anything import UnderstandAnythingAdapter
from agilev.graph.impact import analyze_impact
from agilev.graph.traceability import build_traceability

# 1. Load and normalize the graph.
adapter = UnderstandAnythingAdapter(repo_root=".")
result = adapter.load()

if result.graph is None:
    print("No graph found. Reason:", result.error)
else:
    graph = result.graph
    print(f"Loaded {len(graph.nodes)} nodes, {len(graph.edges)} edges")
    print(f"Graph hash: {graph.source_graph_hash}")

    # 2. Analyze impact of a change request.
    impact = analyze_impact(
        graph=graph,
        change_request_id="CR-001",
        change_request_text="Add rate limiting to the login endpoint",
    )
    print(f"Direct components: {len(impact.direct_components)}")
    print(f"Required tests: {impact.required_tests}")

    # 3. Build traceability matrix.
    traceability = build_traceability(
        graph=graph,
        impact_map=impact,
        requirements=[("REQ-001", "Rate limit repeated login attempts.")],
        changed_files=["src/auth/auth.controller.ts"],
        test_results={"tests/auth/auth.e2e-spec.ts": "pass"},
    )
    print(f"Traceability decision: {traceability.decision}")
```

---

## Package structure

```text
src/agilev/
  __init__.py
  integrations/
    __init__.py
    understand_anything/
      __init__.py
      adapter.py       ← high-level orchestrator
      detector.py      ← find graph/diff files
      loader.py        ← tolerant JSON loading
      normalizer.py    ← node/edge type mapping
      hashing.py       ← SHA-256 file hashing
      errors.py        ← custom exceptions
  graph/
    __init__.py
    model.py           ← SystemGraph, SystemNode, SystemEdge, ImpactMap, etc.
    queries.py         ← keyword search, neighbor traversal
    impact.py          ← analyze_impact()
    traceability.py    ← build_traceability()
```

---

## JSON schemas

Located in `schemas/`:

| Schema | Purpose |
|---|---|
| `system_graph.schema.json` | Validates the normalized SystemGraph JSON |
| `impact_map.schema.json` | Validates the ImpactMap JSON |
| `graph_traceability.schema.json` | Validates the GraphTraceabilityMatrix JSON |

---

## Running the tests

```bash
# Install dev dependencies
pip install -e .[dev]

# Run all unit tests
pytest tests/unit

# Run with coverage
pytest tests/unit --cov=agilev --cov-report=term-missing
```

Test files:

| Test file | What it tests |
|---|---|
| `tests/unit/test_understand_adapter.py` | Detection, loading, hashing, adapter end-to-end |
| `tests/unit/test_graph_normalizer.py` | Node/edge type mapping, synthetic IDs, warnings |
| `tests/unit/test_impact_analysis.py` | Keyword extraction, graph queries, analyze_impact |
| `tests/unit/test_traceability.py` | build_traceability, orphan detection, decision logic |

---

## Graph format tolerance

The adapter handles multiple Understand Anything graph shapes:

| Shape | Node key | Edge key |
|---|---|---|
| Standard | `nodes` | `edges` |
| Nested | `graph.nodes` | `graph.edges` |
| Domain-specific | `files` or `functions` or `classes` | `relationships` or `links` or `dependencies` |

Unknown node types are mapped to `"unknown"`. Unknown edge types are mapped to `"unknown"`.
All warnings are logged and included in `SystemGraph.metadata.normalization_warnings`.

---

## Evidence bundle integration

When `--include-understanding` is passed to the evidence export (Phase 3 CLI), the bundle
includes a new `00_understanding/` section:

```text
evidence_bundle/
  00_understanding/
    knowledge_graph_hash.txt
    normalized_graph.json
    system_overview.md
    architecture_map.md
    understanding_gate_decision.md
  01_impact/
    impact_map.md
    affected_components.json
    required_regression_tests.md
    change_risk_assessment.md
  07_traceability/
    graph_traceability_matrix.md
    req_to_component_links.json
    component_to_test_links.json
    diff_impact_report.md
```

---

## Exit codes (planned for CLI — Phase 3)

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | Graph not found (standalone mode) |
| 2 | Graph found but invalid/unreadable |
| 3 | Normalization failed |
| 4 | Sensitive data scan blocked export |

---

## Security notes

- Do not include raw `knowledge_graph.json` in external evidence bundles.
- Use the hash (`knowledge_graph_hash.txt`) to prove graph identity in audit contexts.
- The adapter does not execute any Understand Anything code; it only reads the JSON output.
- See `agile_v_skills/integrations/understand-anything/security_and_privacy.md` for full guidance.

---

## Troubleshooting

**"Knowledge graph not found"**
Run Understand Anything on the repository to generate `.understand-anything/knowledge-graph.json`.

**"Invalid JSON"**
The graph file may be corrupted or truncated. Re-run Understand Anything.

**"Unknown type warnings"**
The graph uses type labels not in the adapter's mapping table. Check
`normalization_warnings` in the graph metadata and update `normalizer.py` if needed.
Then increment `adapter_version`.

**"Low confidence impact"**
The change request keywords did not match any graph nodes. Try more specific terms that
match the node names, paths, or symbols in the graph.
