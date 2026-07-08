# Implementation Plan: AAV-0001

## Goal

Wrap the external `openwiki` CLI (langchain-ai/openwiki) with an Agile-V
knowledge-layer package so `openwiki/` documentation is validated, tracked
for freshness, and surfaced as evidence.

## Steps

1. `src/agilev/wiki/constants.py` — path constants + required page list
   (base pages always required; domain pages required only when detected).
2. `src/agilev/wiki/domains.py` — detect pcb/firmware/embedded presence.
3. `src/agilev/wiki/manifest.py` — `WikiManifest` dataclass: per-page sha256,
   title, sources, timestamps. Load/save to `.agile-v/wiki/manifest.json`.
4. `src/agilev/wiki/source_map.py` — parse `sources:` front-matter from each
   `openwiki/**/*.md` page and build a reverse index; save to
   `.agile-v/wiki/source_map.json`.
5. `src/agilev/wiki/freshness.py` — compare current source file hashes to the
   manifest snapshot to flag stale pages; save to
   `.agile-v/wiki/freshness.json`.
6. `src/agilev/wiki/validator.py` — structural + freshness validation;
   save `.agile-v/wiki/validation.json`; returns `WikiValidationResult`.
7. `src/agilev/wiki/runner.py` — subprocess wrapper around the real
   `openwiki` binary (`--init`, `--update`, `-p`); dependency-injectable for
   tests (no real subprocess calls in unit tests).
8. `src/agilev/wiki/snapshot.py` — build a `knowledge_snapshot` dict and
   merge it into a task's `evidence.json` / `evidence_bundle.json`.
9. `src/agilev/wiki/cli.py` — `build_wiki_parser(subparsers)` with
   `init|update|validate|status|snapshot`, following `pcb/cli.py` style.
10. Wire `build_wiki_parser` into `src/agilev/cli.py`.
11. `templates/openwiki/*.md` — required page templates with YAML
    front-matter (`title`, `sources`, `owners`, `last_reviewed`).
12. Extend `schemas/evidence_bundle.schema.json` with optional
    `knowledge_snapshot`.
13. Extend `openhands/scaffold.py`: new `check_wiki_freshness.sh`
    session_start hook (advisory only, never blocks) + `doctor()` check.
14. Extend `openhands/evidence_adapter.py`: optional
    `_collect_knowledge_snapshot` merged into `collect_evidence()`.
15. `.github/workflows/openwiki-validate.yml` (PR gate, no external API
    calls — validates already-generated `openwiki/` structure).
16. `.github/workflows/openwiki-update.yml` (scheduled, mirrors upstream
    `examples/openwiki-update.yml`: `npm install -g openwiki`,
    `openwiki --update --print`, `peter-evans/create-pull-request`).
17. `docs/integrations/openwiki.md` — narrative documentation + backlog.
18. Tests: `tests/unit/wiki/test_*.py` for every module above; one CLI smoke
    test in `tests/unit/wiki/test_wiki_cli.py`.
19. Companion skill in the separate `agile_v_skills` repository (submoduled
    at `.opencode/skills`): `skills/openwiki-agent/` following existing
    skill conventions, plus a `SKILL_ROUTING_GUIDE.md` entry.

## Test-first mindset

Each module ships with unit tests using `tmp_path` fixtures; no real
`openwiki` binary or network access is required to pass `pytest`.

## Residual risks (tracked, not blocking)

- The real `openwiki` CLI's exact front-matter/page naming conventions are
  not publicly documented beyond `README.md`/`AGENTS.md` injection; the
  required-page list here is an Agile-V convention layered on top, not a
  reverse-engineered spec of upstream's internal output. If upstream diverges,
  `agilev wiki validate` will need a follow-up update.
- `openwiki --update` requires an LLM provider credential at generation
  time; CI update workflow will fail at the `openwiki --update` step
  until repository-level provider configuration is added. This is
  expected and documented in `docs/integrations/openwiki.md`.
