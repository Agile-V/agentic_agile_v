#!/usr/bin/env bash
# Agile-V Hook: enforce_task_brief
# Block implementation without task ID or task brief

set -euo pipefail

# Read JSON input from stdin
INPUT=$(cat)

# Extract prompt
PROMPT=$(echo "$INPUT" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('prompt', ''))" 2>/dev/null || echo "")

# Try to find task ID from various sources
TASK_ID=""

# 1. Environment variable
if [ -n "${AGILEV_TASK_ID:-}" ]; then
    TASK_ID="$AGILEV_TASK_ID"
fi

# 2. Git branch name (aav-0001-* pattern)
if [ -z "$TASK_ID" ]; then
    BRANCH=$(git branch --show-current 2>/dev/null || echo "")
    if [[ "$BRANCH" =~ ^aav-([0-9]+) ]]; then
        TASK_NUM="${BASH_REMATCH[1]}"
        TASK_ID="AAV-$(printf '%04d' $TASK_NUM)"
    fi
fi

# 3. Prompt contains AAV-XXXX
if [ -z "$TASK_ID" ]; then
    if [[ "$PROMPT" =~ AAV-([0-9]{4}) ]]; then
        TASK_ID="${BASH_REMATCH[0]}"
    fi
fi

# If no task ID found, deny
if [ -z "$TASK_ID" ]; then
    cat <<EOF
{
  "decision": "deny",
  "reason": "No task ID found. Create task brief first: agilev new --title '...' --risk L1"
}
EOF
    exit 2
fi

# Check if task brief exists
BRIEF_PATH=".agentic-agile-v/tasks/$TASK_ID/task_brief.md"
if [ ! -f "$BRIEF_PATH" ]; then
    cat <<EOF
{
  "decision": "deny",
  "reason": "Task brief not found at $BRIEF_PATH. Create it first: agilev new --title '...' --risk L1"
}
EOF
    exit 2
fi

# Task brief exists, allow
cat <<EOF
{
  "decision": "allow",
  "reason": "Task $TASK_ID has valid task brief"
}
EOF
exit 0
