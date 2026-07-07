# Impact Analysis: AAV-0001

## Summary

Adds a new, additive `src/agilev/wiki/` package plus CLI subcommands,
templates, schema extension, CI workflows, and a companion skill. No
existing public API is changed; only additive fields/hooks are introduced.

## Affected Requirements

REQ-0001..REQ-0009 (see `brief.yaml`).

## Affected Components

- `src/agilev/wiki/` (new package)
- `src/agilev/cli.py` (additive: new `wiki` subparser registration)
- `src/agilev/openhands/scaffold.py` (additive hook + doctor check)
- `src/agilev/openhands/evidence_adapter.py` (additive optional evidence key)
- `schemas/evidence_bundle.schema.json` (additive optional property)
- `templates/openwiki/` (new)
- `docs/integrations/openwiki.md` (new)
- `.github/workflows/openwiki-validate.yml`, `openwiki-update.yml` (new)
- Separate repo `agile_v_skills`: `skills/openwiki-agent/` (new)

## Affected Files

See `brief.yaml` scope list.

## Affected Interfaces

- New public CLI surface: `agilev wiki init|update|validate|status|snapshot`.
- New optional `evidence_bundle.json` field: `knowledge_snapshot`.
- New optional OpenHands hook: `check_wiki_freshness.sh` (session_start,
  advisory, exit 0 always — never blocks a session).

## Affected Tests

New: `tests/unit/wiki/test_manifest.py`, `test_source_map.py`,
`test_freshness.py`, `test_validator.py`, `test_domains.py`,
`test_snapshot.py`, `test_runner.py`, `test_wiki_cli.py`.

## Required Regression Tests

Existing suite (`pytest`) must continue to pass unchanged, since no
existing module is modified in a breaking way (only additive edits to
`cli.py`, `scaffold.py`, `evidence_adapter.py`, and the evidence schema).

## Risk Implications

- L2: new feature surface, additive only, no security/auth/crypto/hardware
  changes, no breaking API changes, no destructive migrations.
- The session_start hook is intentionally advisory-only (never denies) to
  avoid introducing a new way to block agent sessions from a doc-only
  concern.

## Required Evidence

- `pytest` run (unit)
- `ruff check` on new package
- CLI smoke test (`agilev wiki init/status/validate/snapshot` against a
  temp repo)

## Open Questions

- Whether GitHub Wiki mirroring should ever become required is deferred —
  current decision (per task brief) is repo-local docs only, since PRs/CI
  are the review mechanism GitHub itself recommends long-form docs be
  paired with when review matters.
