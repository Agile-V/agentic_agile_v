---
name: agile-v-core
description: Apply Agentic Agile-V process control, task briefs, risk-based evidence gates, and human approval rules.
---

# Agile-V Core Rules

## Operating Principle

Conversation is allowed for discovery. Implementation requires a structured task brief.

Do not implement from an ambiguous chat history. Do not expand scope beyond the task brief.

## Before Editing Code

1. Locate the task brief (`.agentic-agile-v/tasks/AAV-XXXX/task_brief.md`)
2. Confirm risk level (L0-L4)
3. Confirm allowed and blocked paths
4. Confirm acceptance criteria
5. Produce a short plan and wait for acknowledgement on L2+ tasks

## Context Engineering

Keep context lean. Pass file paths, not file contents, to sub-agents. Spawn a fresh context per major phase (requirements, build, verify). Size tasks to fit ≤50% of available context. When context exceeds 70%, stop and summarize state before continuing.

## Completion Criteria

A change is complete only when the evidence bundle satisfies the required risk level.

Generating code is not completion. Passing evidence validation is completion.

## Never

- Remove tests to make a build pass
- Weaken security controls (auth, crypto, input validation)
- Add dependencies without approval
- Modify public APIs unless explicitly requested
- Self-approve high-risk work (L3/L4)
- Expand scope beyond allowed paths — if you notice adjacent issues, log them as observations, do not fix them
- Commit secrets, tokens, credentials, or personal data
- Bypass task brief requirements
- Claim tests pass without running them
- Claim CI passes without evidence from CI output

## Evidence Requirements by Risk Level

| Level | Tests | Verifier | Approval | Special |
|-------|-------|----------|----------|---------|
| L0 | Optional | No | No | - |
| L1 | Required or rationale | No | No | - |
| L2 | Passing tests | Yes | Reviewer | - |
| L3 | Passing tests | Yes | Domain owner | Rollback path |
| L4 | Passing tests | Yes | Formal approval | Traceability + simulation/HIL/formal |

## Scope Control

Changed files must be within `allowed_paths` from the task brief.

Files in `blocked_paths` must not be modified.

Dependency changes require explicit approval in the task brief.

If you identify a change needed outside `allowed_paths`, stop, document it as an observation in the evidence bundle, and ask the human whether to expand scope.

## Halt Conditions

Stop and ask before proceeding when:
- The task brief is missing or ambiguous
- Acceptance criteria cannot be mapped to a concrete test
- A required change is outside `allowed_paths`
- Risk level is unclear (default to the higher level)
- An L3/L4 change lacks explicit human approval

## Handoff

On session end, generate a handoff summary:
- Current objective
- Changed files
- Tests run and their results
- Open risks
- Next recommended action
