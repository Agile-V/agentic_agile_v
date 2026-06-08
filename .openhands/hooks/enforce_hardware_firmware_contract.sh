#!/bin/bash
# Enforce hardware-firmware contract during firmware development.
#
# This hook validates that firmware changes don't violate the hardware-firmware contract.

set -e

HOOK_NAME="enforce_hardware_firmware_contract"
CONTRACT_PATH="${AGILEV_CONTRACT_PATH:-.agentic-agile-v/contracts/hardware_firmware_contract.yaml}"

# Check if this is a firmware task
if [ "${AGILEV_TASK_TYPE}" != "firmware" ]; then
    # Not a firmware task, skip
    exit 0
fi

echo "[$HOOK_NAME] Validating firmware changes against hardware-firmware contract..."

# Check if contract exists
if [ ! -f "$CONTRACT_PATH" ]; then
    echo "[$HOOK_NAME] ERROR: Hardware-firmware contract not found: $CONTRACT_PATH"
    echo "[$HOOK_NAME] Firmware tasks require a valid hardware-firmware contract."
    exit 1
fi

# Validate contract schema
if command -v agilev &> /dev/null; then
    echo "[$HOOK_NAME] Validating contract schema..."
    if ! agilev firmware contract validate "$CONTRACT_PATH" --type hardware-firmware; then
        echo "[$HOOK_NAME] ERROR: Contract validation failed"
        exit 1
    fi
    echo "[$HOOK_NAME] ✓ Contract validation passed"
else
    echo "[$HOOK_NAME] WARNING: agilev CLI not available, skipping contract validation"
fi

# Check for forbidden changes
echo "[$HOOK_NAME] Checking for contract violations..."

# Detect if firmware is trying to modify contract files
if git diff --cached --name-only 2>/dev/null | grep -q "hardware_firmware_contract.yaml"; then
    echo "[$HOOK_NAME] ERROR: Firmware tasks cannot modify hardware-firmware contracts"
    echo "[$HOOK_NAME] Contract changes must be initiated from PCB tasks"
    exit 1
fi

# Detect if firmware is trying to modify PCB files
if git diff --cached --name-only 2>/dev/null | grep -qE "\.(kicad_|sch|pcb)"; then
    echo "[$HOOK_NAME] ERROR: Firmware tasks cannot modify PCB design files"
    echo "[$HOOK_NAME] PCB changes must be done through PCB tasks"
    exit 1
fi

echo "[$HOOK_NAME] ✓ No contract violations detected"
exit 0
