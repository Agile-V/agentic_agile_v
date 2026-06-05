#!/usr/bin/env bash
# Agent Setup Script for Agentic Agile-V
# Auto-detects AI coding tool environment and installs appropriate configurations

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "🤖 Agentic Agile-V Setup"
echo "========================"
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

# Detect which AI coding tool is running
detect_environment() {
    # OpenCode detection
    if [ -n "$OPENCODE_SESSION" ] || [ -n "$OPENCODE_VERSION" ]; then
        echo "opencode"
        return
    fi
    
    # Cursor detection
    if [ -n "$CURSOR_SESSION" ] || [ -n "$CURSOR_VERSION" ] || pgrep -f "Cursor" > /dev/null 2>&1; then
        echo "cursor"
        return
    fi
    
    # Windsurf detection
    if [ -n "$WINDSURF_SESSION" ] || pgrep -f "Windsurf" > /dev/null 2>&1; then
        echo "windsurf"
        return
    fi
    
    # Cline detection (runs in VS Code)
    if [ -n "$CLINE_SESSION" ]; then
        echo "cline"
        return
    fi
    
    # VS Code + Continue detection
    if [ -n "${VSCODE_PID:-}" ] || [ "${TERM_PROGRAM:-}" = "vscode" ]; then
        echo "vscode"
        return
    fi
    
    # Default - ask user
    echo "unknown"
}

# Install submodule if not already present
install_submodule() {
    local repo_url="$1"
    local target_path="$2"
    local tool_name="$3"
    
    if [ -d "$target_path" ]; then
        echo "✅ $tool_name configuration already installed at $target_path"
        return 0
    fi
    
    echo "📦 Installing $tool_name configuration..."
    
    # Check if submodule already exists in .gitmodules
    if git config -f .gitmodules "submodule.$target_path.url" > /dev/null 2>&1; then
        echo "   Initializing existing submodule..."
        git submodule update --init --recursive "$target_path"
    else
        echo "   Adding new submodule..."
        git submodule add "$repo_url" "$target_path" 2>/dev/null || {
            echo "   Submodule might already exist, trying update..."
            git submodule update --init --recursive "$target_path"
        }
    fi
    
    echo "✅ $tool_name configuration installed successfully!"
}

# Main setup logic
ENVIRONMENT=$(detect_environment)

echo "Detected environment: $ENVIRONMENT"
echo ""

case "$ENVIRONMENT" in
    opencode)
        echo "🔧 Setting up OpenCode skills..."
        install_submodule \
            "git@github.com:Agile-V/agile_v_skills.git" \
            ".opencode/skills" \
            "OpenCode"
        echo ""
        echo "✨ Setup complete! Please reload your OpenCode session to activate the skills."
        ;;
        
    cursor)
        echo "🔧 Setting up Cursor configuration..."
        install_submodule \
            "git@github.com:Agile-V/agile_v_cursor_config.git" \
            ".cursor" \
            "Cursor"
        echo ""
        echo "✨ Setup complete! Please reload your Cursor session to activate the configuration."
        ;;
        
    vscode)
        echo "🔧 Setting up VS Code + Continue configuration..."
        install_submodule \
            "git@github.com:Agile-V/agile_v_continue_config.git" \
            ".continue" \
            "Continue"
        echo ""
        echo "✨ Setup complete! Please reload VS Code to activate the configuration."
        ;;
        
    windsurf)
        echo "🔧 Setting up Windsurf configuration..."
        install_submodule \
            "git@github.com:Agile-V/agile_v_windsurf_config.git" \
            ".windsurf" \
            "Windsurf"
        echo ""
        echo "✨ Setup complete! Please reload Windsurf to activate the configuration."
        ;;
        
    cline)
        echo "🔧 Setting up Cline configuration..."
        install_submodule \
            "git@github.com:Agile-V/agile_v_cline_config.git" \
            ".cline" \
            "Cline"
        echo ""
        echo "✨ Setup complete! Please reload your VS Code session to activate the configuration."
        ;;
        
    unknown)
        echo "⚠️  Could not auto-detect your AI coding tool."
        echo ""
        echo "Please select your tool:"
        echo "  1) OpenCode"
        echo "  2) Cursor / Claude Code"
        echo "  3) VS Code + Continue"
        echo "  4) Windsurf"
        echo "  5) Cline"
        echo "  6) Skip setup"
        echo ""
        read -p "Enter choice (1-6): " choice
        
        case "$choice" in
            1)
                install_submodule \
                    "git@github.com:Agile-V/agile_v_skills.git" \
                    ".opencode/skills" \
                    "OpenCode"
                ;;
            2)
                install_submodule \
                    "git@github.com:Agile-V/agile_v_cursor_config.git" \
                    ".cursor" \
                    "Cursor"
                ;;
            3)
                install_submodule \
                    "git@github.com:Agile-V/agile_v_continue_config.git" \
                    ".continue" \
                    "Continue"
                ;;
            4)
                install_submodule \
                    "git@github.com:Agile-V/agile_v_windsurf_config.git" \
                    ".windsurf" \
                    "Windsurf"
                ;;
            5)
                install_submodule \
                    "git@github.com:Agile-V/agile_v_cline_config.git" \
                    ".cline" \
                    "Cline"
                ;;
            6)
                echo "⏭️  Skipping setup. You can run this script again later."
                exit 0
                ;;
            *)
                echo "❌ Invalid choice. Exiting."
                exit 1
                ;;
        esac
        ;;
esac

echo ""
echo "📚 Next steps:"
echo "   1. Reload your agent session"
echo "   2. Read the task brief in tasks/ or evidence/"
echo "   3. Follow the Agentic Agile-V workflow in AGENTS.md"
echo ""
