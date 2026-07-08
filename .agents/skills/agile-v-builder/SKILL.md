---
name: agile-v-builder
description: Implementation behavior for builder sessions following the Agile-V process.
---

# Agile-V Builder

## Role

Implement the change described in the task brief. You do not verify your own work — that is the verifier's job.

## Workflow

1. **Inspect** the repository structure and relevant code before writing anything
2. **Plan** the minimal implementation that satisfies the acceptance criteria; for L2+ tasks, write the plan to `.agentic-agile-v/tasks/AAV-XXXX/agent_plan.md` before editing
3. **Edit** only files within `allowed_paths`
4. **Test** — write or update tests before claiming completion; run tests and record real output
5. **Check** — run lint, typecheck, build as applicable; record real output
6. **Document** — update evidence bundle with changed files, actual test results, actual check results
7. **Summarize** — produce an implementation summary

## Test-First Rule

For L1+: Add or update tests **before** marking the task complete. If tests cannot be added, document a concrete test rationale explaining what would need to be tested and why it cannot be automated.

For L2+: Tests must pass. Lint and typecheck must pass. Evidence bundle must record the actual command output showing passing results — not a claim that they passed.

## Minimize Scope

- Make the smallest change that satisfies acceptance criteria
- Do not refactor unrelated code — log observations instead
- Do not change public APIs unless the brief explicitly allows it
- Do not add dependencies unless the brief explicitly allows it
- Do not fix adjacent bugs unless they are within `allowed_paths` and explicitly in scope

## Auto-Fix vs Halt

**Fix automatically** (no human gate needed): syntax errors, missing imports, broken indentation, test assertions on unrelated behavior.

**Halt and ask**: architectural changes, scope expansion, conflicting acceptance criteria, security-sensitive changes, L3/L4 ambiguity. Maximum 3 auto-fix attempts per failure; then escalate.

## Evidence Collection

Update `.agentic-agile-v/tasks/AAV-XXXX/evidence_bundle.json` after each action:

- `changed_files`: list from `git diff --name-only`
- `tests.added`: new test files
- `tests.modified`: modified test files
- `tests.run`: exact commands executed
- `tests.results`: exact pass/fail output (copy from terminal, not from memory)
- `checks`: lint, typecheck, build — exact commands and results

## Implementation Summary

Write `.agentic-agile-v/tasks/AAV-XXXX/implementation_summary.md`:

- What was implemented (mapped to acceptance criteria)
- Files changed
- Tests added/modified and their results
- Residual risks (edge cases not tested, performance concerns, rollback considerations)
- Next recommended action
