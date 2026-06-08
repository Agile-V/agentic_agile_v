---
name: agile-v-builder
description: Implementation behavior for OpenHands builder sessions.
---

# Agile-V Builder

## Role

Implement the change described in the task brief.

## Workflow

1. **Inspect** repository structure and relevant code
2. **Plan** minimal implementation that satisfies acceptance criteria
3. **Edit** only files within allowed paths
4. **Test** narrow tests first, then broader tests
5. **Check** run lint, typecheck, build as applicable
6. **Document** update evidence bundle with changed files, test results
7. **Summarize** produce implementation summary

## Minimize Scope

- Make the smallest change that satisfies acceptance criteria
- Do not refactor unrelated code
- Do not change public APIs unless brief allows
- Do not add dependencies unless brief allows

## Test-First Mindset

For L1+:
- Add or update tests before claiming completion
- Run tests and record results
- If tests cannot be added, document test rationale

For L2+:
- Tests must pass
- Lint and typecheck must pass
- Evidence bundle must record passing results

## Evidence Collection

Update evidence bundle (`.agentic-agile-v/tasks/AAV-XXXX/evidence_bundle.json`):
- `changed_files`: List of modified files
- `tests.added`: Tests added
- `tests.modified`: Tests modified
- `tests.run`: Test commands executed
- `tests.results`: Pass/fail status
- `checks`: Lint, typecheck, build results

## Known Risks

Document residual risks in implementation summary:
- Edge cases not yet tested
- Performance concerns
- Rollback considerations
- Dependency version constraints

## Implementation Summary

Produce `.agentic-agile-v/tasks/AAV-XXXX/implementation_summary.md`:
- What was implemented
- Why (acceptance criteria mapping)
- Changed files
- Tests added/modified
- Test results
- Residual risks
