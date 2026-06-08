#!/bin/bash
# Validate firmware scope during development.
#
# Ensures firmware tasks stay within allowed file paths and don't modify unrelated code.

set -e

HOOK_NAME="validate_firmware_scope"
PROJECT_DIR="${AGILEV_PROJECT_DIR:-firmware}"

# Check if this is a firmware task
if [ "${AGILEV_TASK_TYPE}" != "firmware" ]; then
    exit 0
fi

echo "[$HOOK_NAME] Validating firmware task scope..."

# Define allowed paths for firmware tasks
ALLOWED_PATHS=(
    "$PROJECT_DIR"
    "firmware/"
    ".agentic-agile-v/tasks/"
    ".agentic-agile-v/evidence/"
    "tests/firmware/"
    "docs/firmware/"
)

# Get changed files
CHANGED_FILES=$(git diff --cached --name-only 2>/dev/null || echo "")

if [ -z "$CHANGED_FILES" ]; then
    echo "[$HOOK_NAME] No changes detected"
    exit 0
fi

# Check each changed file
VIOLATIONS=0
while IFS= read -r file; do
    # Skip if file is deleted
    if [ ! -f "$file" ] && [ ! -d "$file" ]; then
        continue
    fi
    
    # Check if file is in allowed paths
    ALLOWED=0
    for allowed_path in "${ALLOWED_PATHS[@]}"; do
        if [[ "$file" == "$allowed_path"* ]]; then
            ALLOWED=1
            break
        fi
    done
    
    if [ $ALLOWED -eq 0 ]; then
        echo "[$HOOK_NAME] ERROR: Firmware task modifying file outside allowed scope: $file"
        echo "[$HOOK_NAME]        Allowed paths: ${ALLOWED_PATHS[*]}"
        VIOLATIONS=$((VIOLATIONS + 1))
    fi
done <<< "$CHANGED_FILES"

if [ $VIOLATIONS -gt 0 ]; then
    echo "[$HOOK_NAME] ERROR: $VIOLATIONS scope violation(s) detected"
    echo "[$HOOK_NAME] Firmware tasks must only modify firmware-related files"
    exit 1
fi

echo "[$HOOK_NAME] ✓ All changes within firmware scope"
exit 0
