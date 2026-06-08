#!/usr/bin/env bash
# OpenHands setup script for Agentic Agile-V integration
# This script prepares the repository for OpenHands execution with Agile-V controls

set -euo pipefail

echo "🔧 Setting up OpenHands + Agile-V integration..."

# Check for required tools
command -v git >/dev/null 2>&1 || { echo "❌ git not found"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "❌ python3 not found"; exit 1; }

# Check for agilev CLI
if ! command -v agilev >/dev/null 2>&1; then
    echo "⚠️  agilev CLI not found. Install with: pip install -e ."
fi

# Ensure hook scripts are executable
if [ -d ".openhands/hooks" ]; then
    chmod +x .openhands/hooks/*.sh
    echo "✅ Hook scripts made executable"
fi

# Ensure log directories exist
mkdir -p .openhands/logs
echo "✅ Log directories created"

# Validate skills exist
SKILLS=(
    ".agents/skills/agile-v-core/SKILL.md"
    ".agents/skills/agile-v-builder/SKILL.md"
    ".agents/skills/agile-v-verifier/SKILL.md"
)

for skill in "${SKILLS[@]}"; do
    if [ ! -f "$skill" ]; then
        echo "⚠️  Skill not found: $skill"
        echo "   Run: agilev openhands init"
    fi
done

echo "✅ OpenHands + Agile-V setup complete"
echo ""
echo "Next steps:"
echo "  1. Create a task: agilev new --title 'Task name' --risk L1"
echo "  2. Edit task brief in .agentic-agile-v/tasks/AAV-XXXX/"
echo "  3. Run OpenHands with Agile-V skills and hooks active"
