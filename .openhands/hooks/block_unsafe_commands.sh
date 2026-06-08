#!/usr/bin/env bash
# Agile-V Hook: block_unsafe_commands
# Block destructive or policy-forbidden terminal commands

set -euo pipefail

# Read JSON input from stdin
INPUT=$(cat)

# Extract command
COMMAND=$(echo "$INPUT" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('tool_args', {}).get('command', ''))" 2>/dev/null || echo "")

# Dangerous patterns
DANGEROUS_PATTERNS=(
    "rm -rf /"
    "dd if="
    "mkfs"
    ":(){ :|:& };:"
    "chmod 777"
    "> /dev/sd"
    "curl .* | sudo bash"
    "wget .* | sudo sh"
)

# Check against patterns
for pattern in "${DANGEROUS_PATTERNS[@]}"; do
    if [[ "$COMMAND" =~ $pattern ]]; then
        cat <<EOF
{
  "decision": "deny",
  "reason": "Command matches dangerous pattern '$pattern' and is forbidden by policy"
}
EOF
        exit 2
    fi
done

# Allow
cat <<EOF
{
  "decision": "allow",
  "reason": "Command passes safety check"
}
EOF
exit 0
