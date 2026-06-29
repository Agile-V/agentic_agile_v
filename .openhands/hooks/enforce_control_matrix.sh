#!/usr/bin/env bash
# enforce_control_matrix.sh — pre_tool_use hook
# Checks the control matrix before every tool call.
# Exits 2 to block; exits 0 to allow.
set -euo pipefail

# Resolve repo root via git, fall back to CWD
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

TOOL_CLASS="${AGILEV_TOOL_CLASS:-}"
TASK_ID="${AGILEV_TASK_ID:-}"

# If no tool class is provided, skip (non-matrix tool calls pass through)
if [ -z "$TOOL_CLASS" ]; then
  exit 0
fi

# Require a task ID for matrix enforcement
if [ -z "$TASK_ID" ]; then
  echo '{"decision":"deny","reason":"AGILEV_TASK_ID missing; cannot resolve control entry"}' >&2
  exit 2
fi

# Check whether the agilev CLI is available
if ! command -v agilev &>/dev/null; then
  # Graceful degradation: warn but do not block if CLI is not installed
  echo '{"decision":"warn","reason":"agilev CLI not found; control matrix enforcement skipped"}' >&2
  exit 0
fi

# Delegate to the CLI
agilev controls check-tool --task "$TASK_ID" --tool "$TOOL_CLASS" --json
STATUS=$?

if [ $STATUS -ne 0 ]; then
  exit 2
fi
exit 0
