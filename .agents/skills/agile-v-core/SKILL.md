---
name: agile-v-core
description: Apply Agentic Agile-V process control, task briefs, risk-based evidence gates, and human approval rules.
---

# Agile-V Core Rules

## Operating Principle

Conversation is allowed for discovery. Implementation requires a structured task brief.

Do not implement from an ambiguous chat history.

## Before Editing Code

1. Locate the task brief (`.agentic-agile-v/tasks/AAV-XXXX/task_brief.md`)
2. Confirm risk level (L0-L4)
3. Confirm allowed and blocked paths
4. Confirm acceptance criteria
5. Produce a short plan

## Completion Criteria

A change is complete only when the evidence bundle satisfies the required risk level.

Generating code is not completion. Passing evidence validation is completion.

## Never

- Remove tests to make a build pass
- Weaken security controls (auth, crypto, input validation)
- Add dependencies without approval
- Modify public APIs unless explicitly requested
- Self-approve high-risk work (L3/L4)
- Expand scope beyond allowed paths
- Commit secrets, tokens, credentials, or personal data
- Bypass task brief requirements

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

## Handoff

On session end, generate a handoff summary:
- Current objective
- Changed files
- Tests run
- Open risks
- Next recommended action
