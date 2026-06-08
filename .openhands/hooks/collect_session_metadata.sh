#!/usr/bin/env bash
# Agile-V Hook: collect_session_metadata
# Record session metadata at session start

set -euo pipefail

# Try to resolve task ID
TASK_ID="${AGILEV_TASK_ID:-}"
if [ -z "$TASK_ID" ]; then
    BRANCH=$(git branch --show-current 2>/dev/null || echo "")
    if [[ "$BRANCH" =~ ^aav-([0-9]+) ]]; then
        TASK_NUM="${BASH_REMATCH[1]}"
        TASK_ID="AAV-$(printf '%04d' $TASK_NUM)"
    fi
fi

# If no task ID, skip
if [ -z "$TASK_ID" ]; then
    exit 0
fi

# Ensure log directory exists
LOG_DIR=".agentic-agile-v/tasks/$TASK_ID/logs"
mkdir -p "$LOG_DIR"

# Record session metadata
SESSION_ID="${OPENHANDS_SESSION_ID:-unknown}"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

cat > "$LOG_DIR/openhands_session.json" <<EOF
{
  "task_id": "$TASK_ID",
  "session_id": "$SESSION_ID",
  "started_at": "$TIMESTAMP",
  "engine": "openhands"
}
EOF

exit 0
