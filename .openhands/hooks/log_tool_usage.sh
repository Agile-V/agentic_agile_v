#!/usr/bin/env bash
# Agile-V Hook: log_tool_usage
# Append tool events to session log

set -euo pipefail

# Read JSON input from stdin
INPUT=$(cat)

# Try to resolve task ID
TASK_ID="${AGILEV_TASK_ID:-}"
if [ -z "$TASK_ID" ]; then
    BRANCH=$(git branch --show-current 2>/dev/null || echo "")
    if [[ "$BRANCH" =~ ^aav-([0-9]+) ]]; then
        TASK_NUM="${BASH_REMATCH[1]}"
        TASK_ID="AAV-$(printf '%04d' $TASK_NUM)"
    fi
fi

# If no task ID, skip logging
if [ -z "$TASK_ID" ]; then
    exit 0
fi

# Ensure log directory exists
LOG_DIR=".agentic-agile-v/tasks/$TASK_ID/logs"
mkdir -p "$LOG_DIR"

# Append to tool log
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
echo "$INPUT" | jq -c ". + {timestamp: \"$TIMESTAMP\"}" >> "$LOG_DIR/openhands_tool_log.jsonl" 2>/dev/null || true

exit 0
