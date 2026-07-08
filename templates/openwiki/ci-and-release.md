---
title: CI, Evidence Bundles, Task Briefs, and Release Gates
sources:
  - .github/workflows
  - schemas/evidence_bundle.schema.json
  - schemas/task_brief.schema.json
owners:
  - agile-v-core
last_reviewed: null
---

# CI, Evidence Bundles, Task Briefs, and Release Gates

Describes the task brief lifecycle (`.agentic-agile-v/tasks/AAV-XXXX/`),
evidence bundle schema (`schemas/evidence_bundle.schema.json`), the CI
quality gates (`.github/workflows/agentic-agile-v-gates.yml`), the
control matrix enforcement layer, and the risk-based (L0-L4) human
approval/release gates.

## Knowledge layer as evidence

`agilev wiki snapshot --task AAV-XXXX` writes a `knowledge_snapshot` object
into that task's evidence bundle, recording whether the knowledge layer was
valid and current at evidence-collection time.

> Populate the narrative sections of this page via `openwiki --update`.
