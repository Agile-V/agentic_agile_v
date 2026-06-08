#!/bin/bash
# Collect firmware evidence after development session.
#
# Gathers build logs, test results, and other evidence artifacts.

set -e

HOOK_NAME="collect_firmware_evidence"
PROJECT_DIR="${AGILEV_PROJECT_DIR:-firmware}"
TASK_ID="${AGILEV_TASK_ID:-unknown}"
EVIDENCE_DIR=".agentic-agile-v/tasks/$TASK_ID/evidence"

# Check if this is a firmware task
if [ "${AGILEV_TASK_TYPE}" != "firmware" ]; then
    exit 0
fi

echo "[$HOOK_NAME] Collecting firmware evidence..."

# Create evidence directory
mkdir -p "$EVIDENCE_DIR"

# Collect build artifacts
if [ -f "$PROJECT_DIR/.pio/build/target/firmware.bin" ]; then
    echo "[$HOOK_NAME] Found firmware binary"
    cp "$PROJECT_DIR/.pio/build/target/firmware.bin" "$EVIDENCE_DIR/" 2>/dev/null || true
    
    # Calculate hash
    if command -v sha256sum &> /dev/null; then
        sha256sum "$EVIDENCE_DIR/firmware.bin" > "$EVIDENCE_DIR/firmware.bin.sha256"
    elif command -v shasum &> /dev/null; then
        shasum -a 256 "$EVIDENCE_DIR/firmware.bin" > "$EVIDENCE_DIR/firmware.bin.sha256"
    fi
fi

# Collect build logs
if [ -d "$PROJECT_DIR/.pio/build/target" ]; then
    find "$PROJECT_DIR/.pio/build/target" -name "*.log" -exec cp {} "$EVIDENCE_DIR/" \; 2>/dev/null || true
fi

# Collect test results
if [ -d "$PROJECT_DIR/.pio/test" ]; then
    find "$PROJECT_DIR/.pio/test" -name "*.xml" -o -name "*.log" | while read -r file; do
        cp "$file" "$EVIDENCE_DIR/" 2>/dev/null || true
    done
fi

# Create evidence manifest
cat > "$EVIDENCE_DIR/manifest.txt" <<EOF
Firmware Evidence Collection
Task ID: $TASK_ID
Collection Time: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
Project Directory: $PROJECT_DIR

Artifacts Collected:
EOF

ls -lh "$EVIDENCE_DIR" >> "$EVIDENCE_DIR/manifest.txt"

echo "[$HOOK_NAME] ✓ Evidence collected to $EVIDENCE_DIR"
echo "[$HOOK_NAME] Manifest:"
cat "$EVIDENCE_DIR/manifest.txt"

exit 0
