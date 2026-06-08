#!/bin/bash
# Require firmware tests before task completion.
#
# Ensures firmware tasks include appropriate tests based on risk level.

set -e

HOOK_NAME="require_firmware_tests"
PROJECT_DIR="${AGILEV_PROJECT_DIR:-firmware}"
RISK_LEVEL="${AGILEV_RISK_LEVEL:-L2}"

# Check if this is a firmware task
if [ "${AGILEV_TASK_TYPE}" != "firmware" ]; then
    exit 0
fi

echo "[$HOOK_NAME] Checking firmware test requirements (Risk: $RISK_LEVEL)..."

# Check for test directory
if [ ! -d "$PROJECT_DIR/test" ]; then
    echo "[$HOOK_NAME] ERROR: No test directory found"
    echo "[$HOOK_NAME] Firmware tasks must include tests"
    exit 1
fi

# Count test files
HOST_TESTS=$(find "$PROJECT_DIR/test" -name "test_*.cpp" -o -name "test_*.c" 2>/dev/null | wc -l)

echo "[$HOOK_NAME] Found $HOST_TESTS test file(s)"

# Risk-based test requirements
case "$RISK_LEVEL" in
    L0)
        # Documentation only, no test requirement
        echo "[$HOOK_NAME] ✓ L0 task, no test requirement"
        ;;
    L1)
        # Low risk, at least one test
        if [ "$HOST_TESTS" -lt 1 ]; then
            echo "[$HOOK_NAME] ERROR: L1 tasks require at least 1 test file"
            exit 1
        fi
        echo "[$HOOK_NAME] ✓ L1 test requirement met"
        ;;
    L2|L3|L4)
        # Higher risk, require tests
        if [ "$HOST_TESTS" -lt 1 ]; then
            echo "[$HOOK_NAME] ERROR: $RISK_LEVEL tasks require comprehensive tests"
            echo "[$HOOK_NAME] Add tests to $PROJECT_DIR/test/"
            exit 1
        fi
        
        # For L3/L4, check for build evidence
        if [ "$RISK_LEVEL" = "L3" ] || [ "$RISK_LEVEL" = "L4" ]; then
            if [ ! -f "$PROJECT_DIR/.pio/build/target/firmware.bin" ] && [ ! -f "$PROJECT_DIR/build/firmware.bin" ]; then
                echo "[$HOOK_NAME] WARNING: No firmware binary found"
                echo "[$HOOK_NAME] Run 'agilev firmware build' before completing task"
            fi
        fi
        
        echo "[$HOOK_NAME] ✓ $RISK_LEVEL test requirement met"
        ;;
    *)
        echo "[$HOOK_NAME] WARNING: Unknown risk level: $RISK_LEVEL"
        ;;
esac

echo "[$HOOK_NAME] ✓ Test requirements satisfied"
exit 0
