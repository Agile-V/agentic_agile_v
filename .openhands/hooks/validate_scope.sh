#!/usr/bin/env bash
# Agile-V Hook: validate_scope
# Warn or block when action appears outside allowed scope

set -euo pipefail

# Read JSON input from stdin
INPUT=$(cat)

# Extract tool name and file path
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('tool_name', ''))" 2>/dev/null || echo "")
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('tool_args', {}).get('file_path', ''))" 2>/dev/null || echo "")

# If no file path, allow (can't validate scope)
if [ -z "$FILE_PATH" ]; then
    cat <<EOF
{
  "decision": "allow",
  "reason": "No file path to validate"
}
EOF
    exit 0
fi

# Try to resolve task ID
TASK_ID="${AGILEV_TASK_ID:-}"
if [ -z "$TASK_ID" ]; then
    BRANCH=$(git branch --show-current 2>/dev/null || echo "")
    if [[ "$BRANCH" =~ ^aav-([0-9]+) ]]; then
        TASK_NUM="${BASH_REMATCH[1]}"
        TASK_ID="AAV-$(printf '%04d' $TASK_NUM)"
    fi
fi

# If no task ID, allow (will be caught by enforce_task_brief)
if [ -z "$TASK_ID" ]; then
    cat <<EOF
{
  "decision": "allow",
  "reason": "No task ID to validate scope against"
}
EOF
    exit 0
fi

# Check if task brief exists
BRIEF_PATH=".agentic-agile-v/tasks/$TASK_ID/task_brief.md"
if [ ! -f "$BRIEF_PATH" ]; then
    cat <<EOF
{
  "decision": "allow",
  "reason": "Task brief not found, cannot validate scope"
}
EOF
    exit 0
fi

# Use Python scope validator
RESULT=$(python3 -c "
import sys
sys.path.insert(0, 'src')
from agilev.openhands.scope import ScopeValidator

validator = ScopeValidator()
policy = validator.parse_task_brief_scope('$TASK_ID')

allowed, reason = policy.is_path_allowed('$FILE_PATH')

if allowed:
    print('allow')
else:
    print('deny')
    print(reason, file=sys.stderr)
" 2>&1)

DECISION=$(echo "$RESULT" | head -1)
REASON=$(echo "$RESULT" | tail -n +2)

if [ "$DECISION" = "deny" ]; then
    cat <<EOF
{
  "decision": "deny",
  "reason": "Scope violation for task $TASK_ID: $REASON"
}
EOF
    exit 2
else
    cat <<EOF
{
  "decision": "allow",
  "reason": "File within allowed scope: $FILE_PATH"
}
EOF
    exit 0
fi
