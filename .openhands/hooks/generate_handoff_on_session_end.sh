#!/usr/bin/env bash
# Agile-V Hook: generate_handoff_on_session_end
# Generate handoff summary at session end

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

TASK_DIR=".agentic-agile-v/tasks/$TASK_ID"
HANDOFF_PATH="$TASK_DIR/openhands_handoff.md"

# Get changed files
CHANGED_FILES=$(git diff --name-only 2>/dev/null | head -20 || echo "Unable to determine")

# Generate handoff
cat > "$HANDOFF_PATH" <<EOF
# OpenHands Session Handoff: $TASK_ID

**Session ID:** ${OPENHANDS_SESSION_ID:-unknown}
**Ended:** $(date -u +"%Y-%m-%dT%H:%M:%SZ")

## Changed Files

```
$CHANGED_FILES
```

## Next Steps

1. Review changed files
2. Run: agilev validate --task $TASK_ID
3. If L2+, run verifier: agilev openhands verify --task $TASK_ID
4. Create pull request

## Evidence Location

- Task brief: $TASK_DIR/task_brief.md
- Evidence bundle: $TASK_DIR/evidence_bundle.json
- Tool log: $TASK_DIR/logs/openhands_tool_log.jsonl
EOF

exit 0
