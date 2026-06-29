#!/usr/bin/env bash
# validate_control_evidence_on_stop.sh — stop hook
# Validates that the evidence bundle includes control matrix results for L2+ tasks.
# Exits 2 to block session close; exits 0 when validation passes or is skipped.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

TASK_ID="${AGILEV_TASK_ID:-}"
RISK_LEVEL="${AGILEV_RISK_LEVEL:-}"

# No task ID or no risk level means we cannot enforce — skip gracefully
if [ -z "$TASK_ID" ] || [ -z "$RISK_LEVEL" ]; then
  exit 0
fi

# Only enforce for L2 and above
case "$RISK_LEVEL" in
  L0|L1) exit 0 ;;
esac

if ! command -v agilev &>/dev/null; then
  echo '{"decision":"warn","reason":"agilev CLI not found; stop-hook enforcement skipped"}' >&2
  exit 0
fi

# Run the evidence command; non-zero exit indicates a validation failure
if ! agilev controls evidence --task "$TASK_ID" --check-only --json; then
  echo '{"decision":"deny","reason":"Control matrix evidence validation failed for '"$TASK_ID"'"}' >&2
  exit 2
fi

exit 0
