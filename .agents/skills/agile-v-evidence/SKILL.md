---
name: agile-v-evidence
description: Evidence collection and update behavior.
---

# Agile-V Evidence Collection

## Purpose

Maintain accurate evidence bundle throughout the task lifecycle.

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

## OpenHands Extensions

If using OpenHands, add:
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

## Collect Evidence From

- Git: `git diff --name-only` for changed files
- Test output: Parse test command output
- CI results: Parse GitHub Actions / CI output
- Tool logs: OpenHands tool usage log

## Never Fabricate

- Do not claim tests passed if they failed
- Do not claim tests exist if they don't
- Do not claim checks passed if they failed
- Use Git/CI as source of truth, not agent memory

## Update After

- File edits
- Test runs
- Check runs (lint, typecheck, build)
- Session end
