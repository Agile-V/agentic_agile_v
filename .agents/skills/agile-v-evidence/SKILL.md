---
name: agile-v-evidence
description: Evidence collection and update behavior for Agile-V task lifecycle.
---

# Agile-V Evidence Collection

## Purpose

Maintain an accurate, real-time evidence bundle throughout the task lifecycle. Evidence is collected from Git and CI — not from agent memory.

## Golden Rule

**Collect evidence before claiming the task is done.** Do not write "tests pass" until you have run them and recorded the output. Do not write "lint passes" until you have run the lint command.

## Evidence Bundle Location

`.agentic-agile-v/tasks/AAV-XXXX/evidence_bundle.json`

## Required Fields

```json
{
  "task_id": "AAV-XXXX",
  "risk_level": "L1|L2|L3|L4",
  "changed_files": [],
  "tests": {
    "added": [],
    "modified": [],
    "run": [],
    "results": []
  },
  "checks": {
    "lint": {},
    "typecheck": {},
    "build": {}
  }
}
```

## Collect Evidence From (Sources of Truth)

- **Changed files:** `git diff --name-only HEAD` or `git status`
- **Test results:** Capture the actual command output, not a summary from memory
- **CI results:** Read from GitHub Actions / CI output directly
- **Build results:** Capture compiler/build tool stdout and stderr

Never paraphrase CI or test output. Paste the relevant lines verbatim into the evidence bundle.

## OpenHands Extensions

If using OpenHands, also add:

```json
{
  "agent_execution": {
    "engine": "openhands",
    "mode": "builder|verifier",
    "session_id": "...",
    "tool_log_path": "logs/openhands_tool_log.jsonl"
  },
  "scope_control": {
    "allowed_paths": [],
    "blocked_paths": [],
    "changed_files_within_scope": true
  }
}
```

## Update After Each

- File edit — add file to `changed_files`
- Test run — add command and output to `tests.run` and `tests.results`
- Check run (lint, typecheck, build) — add command and result to `checks`
- Scope check — confirm changed files are within `allowed_paths`
- Session end — ensure bundle is complete before closing

## Never Fabricate

- Do not write `"pass"` for a test you have not run
- Do not write `"no issues"` for a lint check you have not run
- Do not claim a file was changed if Git does not show it
- If a test is skipped with rationale, record `"skipped"` and the rationale — not `"pass"`
