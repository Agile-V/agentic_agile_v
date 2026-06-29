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
# Set AGILEV_STRICT_MODE=1 to block all tool calls when the CLI is unavailable.
# Default: fail-open (warn only) so that repos without agilev installed are not blocked.
STRICT_MODE="${AGILEV_STRICT_MODE:-0}"

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
  LOG_FILE="$ROOT/.agile-v/logs/control-events.jsonl"
  TS="$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || echo 'unknown')"
  WARN_JSON="{\"timestamp\":\"$TS\",\"task_id\":\"$TASK_ID\",\"decision\":\"warn\",\"reason\":\"agilev CLI not found; control matrix enforcement skipped\"}"
  # Best-effort: append to log (ignore errors so the hook itself never blocks on log failure)
  mkdir -p "$ROOT/.agile-v/logs" 2>/dev/null && echo "$WARN_JSON" >> "$LOG_FILE" 2>/dev/null || true
  echo "$WARN_JSON" >&2
  if [ "$STRICT_MODE" = "1" ]; then
    exit 2
  fi
  exit 0
fi

# Delegate to the CLI
agilev controls check-tool --task "$TASK_ID" --tool "$TOOL_CLASS" --json
STATUS=$?

if [ $STATUS -ne 0 ]; then
  exit 2
fi
exit 0
