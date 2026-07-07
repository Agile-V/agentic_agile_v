# OpenWiki Integration

**Status:** Active
**Integration Type:** Repository Knowledge Layer
**Agile-V Version:** ≥0.1.0
**OpenWiki:** [langchain-ai/openwiki](https://github.com/langchain-ai/openwiki) (npm CLI, MIT licensed)

---

## Overview

[OpenWiki](https://github.com/langchain-ai/openwiki) is a CLI that writes and
maintains agent-facing documentation for a codebase (`openwiki --init`,
`openwiki --update`, `openwiki -p "<prompt>"`), generating it into an
`openwiki/` directory and injecting guidance into `AGENTS.md`/`CLAUDE.md`.

This integration treats that generated documentation as a **fundamental
Agile-V repository knowledge layer**, not optional reading material:

- A required page structure that scales with the repository's detected
  domains (software/OpenHands, PCB, firmware, embedded, cross-domain
  co-verification).
- A manifest, source map, freshness, and validation model under
  `.agile-v/wiki/`, mirroring the pattern already used by
  `.agile-v/impact/`, `.agile-v/traceability/`, and
  `.agile-v/understanding/`.
- A CLI surface (`agilev wiki init|update|validate|status|snapshot`).
- Evidence bundle integration (`knowledge_snapshot`).
- An advisory (never-blocking) OpenHands `session_start` hook.
- CI enforcement: PR validation + a scheduled update-PR workflow.

**Key principle:** `openwiki` generates; Agile-V tracks, validates, and
proves.

---

## Architecture

```text
openwiki (external CLI)  = generates/refreshes openwiki/ content (LLM-backed)
agilev.wiki (this package) = tracks, validates, and proves that content
.agile-v/wiki/             = manifest.json, source_map.json, freshness.json,
                              validation.json (Agile-V's own bookkeeping)
CI                         = PR validation (structure) + scheduled update PR
Evidence bundle            = knowledge_snapshot (proof the layer was valid
                              and current at evidence-collection time)
```

`agilev` never vendors or reimplements `openwiki`. `agilev.wiki.runner.OpenWikiRunner`
is a thin, dependency-injectable subprocess wrapper used only when a caller
explicitly opts in (`--run-openwiki`); by default, `agilev wiki init/update`
only manage Agile-V's own scaffolding and bookkeeping, so `pytest` and CI
structure checks never require the `openwiki` npm package, a network
connection, or an LLM API key.

---

## Package Layout (`src/agilev/wiki/`)

| Module | Purpose |
|---|---|
| `constants.py` | `openwiki/` and `.agile-v/wiki/` paths; base/domain required-page lists |
| `domains.py` | Detects PCB/firmware/embedded presence to extend the required-page list |
| `page_templates.py` | Canonical Markdown content for required page skeletons (single source of truth) |
| `scaffolder.py` | Writes required page skeletons into `openwiki/` (never overwrites without `--force`) |
| `frontmatter.py` | Minimal YAML front-matter parser (title/sources/owners/last_reviewed) |
| `manifest.py` | `WikiManifest`: per-page hash/title/sources snapshot, persisted to `.agile-v/wiki/manifest.json` |
| `source_map.py` | Reverse index: source path → wiki pages that declare it, persisted to `.agile-v/wiki/source_map.json` |
| `freshness.py` | Compares declared sources' mtimes against the manifest timestamp, persisted to `.agile-v/wiki/freshness.json` |
| `validator.py` | Structural validation (missing pages, manifest/disk drift); persisted to `.agile-v/wiki/validation.json` |
| `runner.py` | Subprocess wrapper for the real `openwiki` binary (opt-in, mockable) |
| `snapshot.py` | Builds/merges a `knowledge_snapshot` evidence object into a task's evidence file |
| `cli.py` | `agilev wiki init/update/validate/status/snapshot` |

---

## Required Page Structure

Base pages (always required):

```text
openwiki/
├── README.md              # Index
├── ARCHITECTURE.md
├── ONBOARDING.md
├── domains/
│   └── software.md        # OpenHands / agilev CLI backend
└── ci-and-release.md       # CI, evidence bundles, task briefs, release gates
```

Domain pages (required only when detected — see `agilev.wiki.domains`):

| Page | Required when |
|---|---|
| `domains/pcb.md` | `src/agilev/pcb/` or `examples/pcb/` exists |
| `domains/firmware.md` | `src/agilev/firmware/` exists |
| `domains/embedded.md` | `src/agilev/embedded/` exists |
| `co-verification.md` | Two or more of {pcb, firmware, embedded} are present |

Reference copies of the scaffolded content live in `templates/openwiki/`
for human browsing; the CLI reads from `agilev.wiki.page_templates` (the
single source of truth) so scaffolding works identically whether `agilev`
is run from a repo checkout or an installed package.

Each page carries YAML front-matter:

```yaml
---
title: Architecture Overview
sources:
  - src/agilev
  - pyproject.toml
owners:
  - agile-v-core
last_reviewed: null
---
```

`sources:` entries drive the source map and freshness checks.

---

## CLI

```bash
agilev wiki init [--force] [--run-openwiki]
agilev wiki update [--run-openwiki]
agilev wiki validate [--json]
agilev wiki status [--json]
agilev wiki snapshot --task AAV-XXXX
```

- `init` scaffolds required pages (skipping existing ones unless `--force`)
  and records an initial manifest/source-map/freshness snapshot.
- `update` recomputes the manifest/source-map/freshness from whatever is
  currently in `openwiki/` — this is what CI's scheduled workflow runs
  after the real `openwiki --update` refreshes content.
- `validate` **fails** (exit 1) only on structural problems: a required
  page is missing, or the manifest no longer matches what's on disk
  (meaning `agilev wiki update` wasn't run after an edit). Staleness
  relative to declared source files is a **warning** only (exit 0),
  since code changes between OpenWiki refresh cycles are normal.
- `status` prints (or emits as JSON) a freshness/validation summary.
- `snapshot` writes a `knowledge_snapshot` object into a task's
  `evidence.json`/`evidence_bundle.json` (whichever exists; prefers the
  richer `evidence_bundle.json`).
- `--run-openwiki` on `init`/`update` optionally shells out to the real
  `openwiki` binary first (best-effort; a missing binary only produces a
  warning, since it is not part of the `agilev` package).

---

## Evidence Bundle Integration

`schemas/evidence_bundle.schema.json` gains an optional `knowledge_snapshot`
object (`wiki_dir`, `manifest_generated_at`, `page_count`, `pages`,
`required_pages`, `validation_passed`, `validation_errors`,
`validation_warnings`, `stale_pages`, `captured_at`).

`agilev.openhands.evidence_adapter.EvidenceAdapter.collect_evidence()` will
automatically include a `knowledge_snapshot` when `openwiki/` exists in the
repository, in addition to the explicit `agilev wiki snapshot --task
AAV-XXXX` command.

---

## OpenHands Hook

`session_start` gains an additional, **advisory-only** hook,
`check_wiki_freshness.sh`: it runs `agilev wiki validate` and reports the
result as part of the session-start decision payload, but **always returns
`"decision": "allow"`**. A missing or stale knowledge layer is a signal to
the agent, not a reason to block a session — the existing
`enforce_task_brief.sh` and `validate_evidence_on_stop.sh` hooks remain the
only blocking gates.

---

## CI Workflows

### `.github/workflows/openwiki-validate.yml` (PR gate)

Runs `agilev wiki validate` on every PR. No `openwiki` install, no network
calls, no API key required — this only checks structure and manifest/disk
consistency of whatever is already committed.

### `.github/workflows/openwiki-update.yml` (scheduled update PR)

Mirrors upstream's
[`examples/openwiki-update.yml`](https://github.com/langchain-ai/openwiki/blob/main/examples/openwiki-update.yml):
installs `openwiki` via npm, runs `openwiki --update --print` against a
configured inference provider, then additionally runs `agilev wiki update`
to recompute the Agile-V manifest/source-map/freshness records, and opens a
PR via `peter-evans/create-pull-request`.

**Configuration required before this workflow can succeed:**

| Secret | Purpose |
|---|---|
| `OPENROUTER_API_KEY` (or your preferred provider's key) | LLM inference for `openwiki --update` |
| `LANGSMITH_API_KEY` (optional) | Tracing (`openwiki` supports LangSmith) |

Until these secrets are configured, the workflow will fail at the
`openwiki --update` step — this is expected and does not block merging the
workflow definition itself (the PR-validation workflow is independent and
requires no secrets).

---

## GitHub Wiki Mirroring: Explicitly Out of Scope

This integration deliberately does **not** mirror `openwiki/` into the
separate GitHub Wiki (the `.wiki.git` repository GitHub provides per
repository). Repository-local docs under version control are reviewable
through normal pull requests and this repo's existing CI quality gates;
GitHub's own docs position the wiki feature as long-form repository
documentation, not as a review-gated artifact. If a future need for a
public-facing mirror emerges, it should be a separate, explicitly-scoped
follow-up (e.g., a CI step that pushes `openwiki/` to the wiki repo after
merge), not a requirement of this integration.

---

## Backlog

- [ ] **OW-1** — Land `src/agilev/wiki/` package + CLI (this change).
- [ ] **OW-2** — Configure `OPENROUTER_API_KEY` (or equivalent) repository
      secret so `openwiki-update.yml` can actually run `openwiki --update`.
- [ ] **OW-3** — Run `openwiki --init` (interactive, one-time) to replace
      the Agile-V-scaffolded page stubs with real generated content.
- [ ] **OW-4** — Extend `validate_scope.sh` / control-matrix policy (once
      merged) to treat `openwiki/**` as always-allowed, low-risk paths.
- [ ] **OW-5** — Add a PCB/firmware/embedded co-verification worked example
      to `co-verification.md` once those backends have real implementations
      (`src/agilev/firmware/`, `src/agilev/embedded/` do not exist yet on
      `main` as of this writing; only `src/agilev/pcb/` does).
- [ ] **OW-6** — Revisit GitHub Wiki mirroring if a public-facing,
      non-review-gated documentation surface becomes a real requirement.

## Acceptance Criteria

- `pytest tests/unit/wiki/` passes.
- `ruff check src/agilev/wiki` passes.
- `agilev wiki init` on an empty repository creates `openwiki/` with all
  base required pages and `.agile-v/wiki/manifest.json`.
- `agilev wiki validate` returns exit 1 with a clear error when a required
  page is deleted, and exit 0 (with warnings) when a declared source file
  changes without a corresponding `agilev wiki update`.
- `agilev wiki snapshot --task <id>` adds a `knowledge_snapshot` object to
  that task's evidence file.
- `evidence_bundle.schema.json` validates an evidence bundle containing
  `knowledge_snapshot`, and continues to validate bundles without it.
- `agilev --help` lists the `wiki` command group.

## Test Plan

| Layer | Command | Covers |
|---|---|---|
| Unit | `pytest tests/unit/wiki/test_domains.py` | Domain detection, required-page scaling |
| Unit | `pytest tests/unit/wiki/test_manifest.py` | Manifest scan/save/load/hashing |
| Unit | `pytest tests/unit/wiki/test_source_map.py` | Reverse source→page index, prefix matching |
| Unit | `pytest tests/unit/wiki/test_freshness.py` | Stale/missing source detection |
| Unit | `pytest tests/unit/wiki/test_validator.py` | Structural pass/fail, manifest drift detection |
| Unit | `pytest tests/unit/wiki/test_scaffolder.py` | Idempotent scaffolding, `--force` behavior |
| Unit | `pytest tests/unit/wiki/test_runner.py` | Subprocess wrapper with injected fake `run_fn` (no real process/network) |
| Unit | `pytest tests/unit/wiki/test_snapshot.py` | Snapshot building, evidence-file merge |
| Unit | `pytest tests/unit/wiki/test_evidence_schema.py` | Schema accepts/rejects `knowledge_snapshot` correctly |
| CLI smoke | `pytest tests/unit/wiki/test_wiki_cli.py` | Full `init → update → validate → status → snapshot` flow via `agilev.cli.main` |
| Regression | `pytest` (full suite) | No existing test broken by additive changes |
| Lint/type | `ruff check src/ tests/`, `mypy src/agilev` | No new violations |

## Definition of Done

- All items in **Acceptance Criteria** are met and verified locally.
- Full existing `pytest` suite still passes (no regressions).
- `ruff check` and `mypy` pass on touched files.
- `openwiki/` and `.agile-v/wiki/` are scaffolded and committed for this
  repository (dogfooding: `agilev wiki validate` passes on `main` after
  merge).
- `AAV-0001`'s evidence file records a `knowledge_snapshot`
  (`agilev wiki snapshot --task AAV-0001`).
- This document and the task brief/plan/impact analysis under
  `.agentic-agile-v/tasks/AAV-0001/` are up to date.
- Residual risks below are acknowledged, not silently dropped.

## Residual Risks

- The required-page/front-matter conventions here are an Agile-V layer on
  top of `openwiki`, not a reverse-engineered spec of upstream's internal
  output format. If upstream changes its own generated structure
  significantly, `agilev wiki validate`/`scaffolder.py` may need follow-up.
- `openwiki --update` requires an LLM provider API key; the scheduled CI
  workflow will not produce real content until secrets are configured
  (see Backlog OW-2).
- Only `src/agilev/pcb/` exists in this repository today; the firmware and
  embedded domain pages will scaffold once those backends land, but have
  no real implementation to document yet (see Backlog OW-5).
