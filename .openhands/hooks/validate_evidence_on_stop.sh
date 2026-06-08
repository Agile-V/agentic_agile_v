#!/usr/bin/env bash
# Agile-V Hook: validate_evidence_on_stop
# Block completion until evidence passes validation

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

# If no task ID, deny
if [ -z "$TASK_ID" ]; then
    cat <<EOF
{
  "decision": "deny",
  "reason": "No task ID found, cannot validate evidence"
}
EOF
    exit 2
fi

# Run agilev validate
if command -v agilev &> /dev/null; then
    if agilev validate --task "$TASK_ID" &> /dev/null; then
        cat <<EOF
{
  "decision": "allow",
  "reason": "Evidence validation passed for task $TASK_ID"
}
EOF
        exit 0
    else
        cat <<EOF
{
  "decision": "deny",
  "reason": "Evidence validation failed for task $TASK_ID. Run: agilev validate --task $TASK_ID"
}
EOF
        exit 2
    fi
else
    # agilev not available, allow with warning
    cat <<EOF
{
  "decision": "allow",
  "reason": "agilev CLI not available, skipping evidence validation"
}
EOF
    exit 0
fi
