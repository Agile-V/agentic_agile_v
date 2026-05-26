# Agentic Agile-V Infrastructure

This repository scaffold operationalizes the paper framework **Agentic Agile-V: From Vibe Coding to Verified Engineering in Software and Hardware Development**.

The goal is simple:

> Conversation discovers intent. Structured artifacts control implementation. Evidence controls acceptance.

The scaffold gives teams a practical way to run AI agents inside a disciplined engineering process without turning development into uncontrolled "vibe coding".

## What is included

- `AGENTS.md`: repository-level rules for coding agents.
- `templates/`: feature, bug, hardware/firmware, test, review, and evidence templates.
- `docs/`: process documentation for Agile-V, SCOPE-V, testing, hardware, and evidence gates.
- `schemas/`: JSON schemas for task briefs, evidence bundles, system graph, impact map, and traceability.
- `scripts/`: local validation and task bootstrap tools.
- `.github/`: PR template, issue templates, and CI workflow for evidence gates.
- `examples/`: sample feature, bug, and hardware task packages.
- `src/agilev/`: Python runtime library — graph adapter, impact analysis, traceability.
- `tests/`: Unit tests for the Python runtime library.

## Recommended workflow

1. Start with a conversation to discover intent.
2. Convert the conversation into a structured task brief.
3. Classify risk level from L0 to L4.
4. Ask the agent to inspect the repository and produce a plan.
5. Approve the plan for non-trivial changes.
6. Implement in small slices.
7. Generate or update tests.
8. Produce an evidence bundle.
9. Run validation gates.
10. Merge only after human review and risk-appropriate evidence.

## Quick start

Create a new task package:

```bash
python scripts/new_task.py --type feature --id AAV-001 --title "Add device status endpoint"
```

Validate all evidence bundles:

```bash
python scripts/validate_evidence.py --root evidence
```

Validate one bundle:

```bash
python scripts/validate_evidence.py --bundle evidence/examples/feature/evidence_bundle.json
```

## Risk levels

| Level | Typical scope | Required evidence |
|---|---|---|
| L0 | Docs, comments, trivial internal cleanup | Brief, plan, reviewer note |
| L1 | Low-risk internal code | Tests or test rationale, lint/static check |
| L2 | Normal production feature or bug fix | Unit/integration tests, CI, reviewer gate |
| L3 | Security, customer-visible, data, APIs, persistent state | Regression tests, security/privacy check, rollback path, approval |
| L4 | Safety, hardware/firmware, regulated, money movement, critical infrastructure | Independent verification, HIL/simulation/formal evidence, traceability matrix, approval |

## Understand Anything Integration

Agile V can consume an [Understand Anything](https://github.com/Lum1104/Understand-Anything)
knowledge graph to add system context, impact analysis, graph traceability, and
regression-test selection to the Agile-V lifecycle.

```bash
# Install the runtime library
pip install -e .[dev]

# Run tests
make test
```

See `docs/understand-anything-integration.md` for full usage documentation.

The companion skill documentation is in `agile_v_skills/integrations/understand-anything/`.

## Principle

Do not let an agent implement from a long chat history. Let it implement from a reviewed, versioned brief.
