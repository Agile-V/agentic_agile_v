# OpenHands Integration - Complete User Guide

**Version:** 2.0  
**Date:** 2026-06-08  
**Status:** Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Installation](#installation)
4. [Basic Usage](#basic-usage)
5. [Advanced Features](#advanced-features)
6. [CLI Reference](#cli-reference)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)
9. [Examples](#examples)

---

## Overview

The OpenHands integration brings agentic automation to Agile-V while maintaining strict evidence-based gates and scope control.

### Key Features

✅ **Automatic OpenHands Launching** - Run agents with `agilev openhands run`  
✅ **Builder/Verifier Pattern** - Two-agent workflow for quality  
✅ **Scope Enforcement** - Hooks prevent out-of-scope changes  
✅ **Evidence Collection** - Automatic evidence from sessions  
✅ **GitHub Actions Integration** - CI/CD workflows included  
✅ **Event Ledger** - Tamper-proof audit trail with hash chain  
✅ **Enhanced Reports** - Risk-level specific handoff documents  

### Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Agile-V CLI                        │
├─────────────────────────────────────────────────────┤
│  openhands run    │  Evidence      │  GitHub        │
│  Builder/Verifier │  Collection    │  Actions       │
└─────────────────────────────────────────────────────┘
           │                 │                 │
           ▼                 ▼                 ▼
┌──────────────────┐  ┌─────────────┐  ┌──────────────┐
│  Session Manager │  │ Event Ledger│  │  Workflows   │
│  - Launch agents │  │ - Hash chain│  │  - PR checks │
│  - Monitor exec  │  │ - Audit log │  │  - Evidence  │
└──────────────────┘  └─────────────┘  └──────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────┐
│              OpenHands Agent                        │
│  Guided by Skills   │   Constrained by Hooks        │
└─────────────────────────────────────────────────────┘
```

---

## Quick Start

### 5-Minute Setup

```bash
# 1. Initialize Agile-V
cd your-project
agilev init
agilev openhands init

# 2. Validate setup
agilev openhands doctor

# 3. Create a task
agilev new --title "Add retry logic" --risk L1

# 4. Edit task brief and add scope
vim .agentic-agile-v/tasks/AAV-0001/task_brief.md
# Add YAML frontmatter with allowed_paths

# 5. Run OpenHands
agilev openhands run --task AAV-0001 --prompt "Implement retry logic" --builder-verifier

# 6. Get handoff report
agilev openhands handoff --task AAV-0001
```

---

## Installation

### Prerequisites

- Python 3.11+
- Git
- OpenHands (Docker or local installation)

### Install Agile-V

```bash
pip install agilev
```

### Install OpenHands

**Option A: Docker (Recommended)**

```bash
docker pull ghcr.io/all-hands-ai/openhands:latest
```

**Option B: From Source**

```bash
git clone https://github.com/All-Hands-AI/OpenHands.git
cd OpenHands
make build
```

### Initialize Integration

```bash
cd your-repository
agilev openhands init
```

This creates:
- `.openhands/` - Configuration and hooks
- `.agents/skills/` - Agent guidance
- `.agentic-agile-v/openhands/` - Session data and logs

---

## Basic Usage

### Creating a Task with Scope

```bash
# Create task
agilev new --title "Implement file upload" --risk L2
# Output: Created task AAV-0042

# Edit task brief
vim .agentic-agile-v/tasks/AAV-0042/task_brief.md
```

Add YAML frontmatter:

```yaml
---
allowed_paths:
  - src/upload/**
  - tests/upload/**
blocked_paths:
  - src/auth/**
  - src/secrets/**
public_api_changes_allowed: false
dependency_changes_allowed: false
---

# Implement File Upload

Add retry logic to file upload...
```

### Running OpenHands (Standalone Mode)

```bash
agilev openhands run \
  --task AAV-0042 \
  --prompt "Implement file upload with retry logic"
```

### Running OpenHands (Builder/Verifier Mode)

```bash
agilev openhands run \
  --task AAV-0042 \
  --builder-verifier
```

This launches:
1. **Builder agent** - Implements changes
2. **Verifier agent** - Reviews implementation
3. **Iterates** - Up to 3 cycles until approved

### Collecting Evidence

```bash
# Automatic collection after session
agilev openhands evidence collect --task AAV-0042

# View evidence
cat .agentic-agile-v/tasks/AAV-0042/evidence/bundle.json
```

### Generating Handoff

```bash
agilev openhands handoff --task AAV-0042
```

Output: `handoff_report.md` with:
- Summary of changes
- Test results
- Scope compliance
- Recommendations
- Residual risks

---

## Advanced Features

### 1. Event Ledger

The event ledger provides a tamper-proof audit trail.

```bash
# View events
agilev openhands events --task AAV-0042

# Show full timeline
agilev openhands timeline --task AAV-0042

# Verify chain integrity
agilev openhands verify-chain
```

**Example Event:**

```json
{
  "event_id": "EVT-00000042",
  "event_type": "session_completed",
  "timestamp": "2026-06-08T14:30:00Z",
  "actor": "openhands",
  "actor_session_id": "AAV-0042_builder_20260608_143000",
  "task_id": "AAV-0042",
  "summary": "Completed builder session with status: completed",
  "details": {
    "iterations": 12,
    "tool_calls": 47,
    "duration_seconds": 342.5
  },
  "previous_hash": "sha256:abc123...",
  "event_hash": "sha256:def456..."
}
```

### 2. Session Management

```bash
# List sessions
agilev openhands sessions --task AAV-0042

# Show session details
agilev openhands session AAV-0042_builder_20260608_143000

# View session logs
cat .agentic-agile-v/openhands/sessions/AAV-0042_builder_20260608_143000/session.log
```

### 3. GitHub Actions

Generate CI/CD workflows:

```bash
agilev openhands github-actions
```

This creates:
- `.github/workflows/agilev-pr-validation.yml` - PR checks
- `.github/workflows/agilev-evidence-collection.yml` - Post-merge evidence
- `.github/workflows/agilev-handoff.yml` - Handoff on PR
- `.github/workflows/agilev-scope-check.yml` - Fast scope validation

**Example: PR Workflow**

```yaml
# Automatically runs on every PR
name: Agile-V PR Validation
on:
  pull_request:
    types: [opened, synchronize, reopened]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install agilev
      - run: agilev openhands validate --scope
```

### 4. Builder/Verifier Workflow

The builder/verifier pattern provides automatic code review:

```
┌─────────────┐
│   Builder   │ ← Implements changes
│   Agent     │
└─────────────┘
      │
      ▼
┌─────────────┐
│  Verifier   │ ← Reviews implementation
│   Agent     │
└─────────────┘
      │
      ├─ ✅ Approved → Done
      │
      └─ ❌ Rejected → Builder iterates
            (max 3 cycles)
```

**Builder Prompt:**

```
You are the BUILDER agent for task AAV-0042.

Implement file upload with retry logic according to the task brief.

Scope: Only modify files in src/upload/** and tests/upload/**

When done, summarize what you implemented and what tests you ran.
```

**Verifier Prompt:**

```
You are the VERIFIER agent for task AAV-0042.

Review the builder's implementation:
- Check task brief requirements are met
- Verify scope constraints respected  
- Run all tests
- Check code quality

Decision: APPROVE or REJECT with detailed reasons.
```

---

## CLI Reference

### Core Commands

```bash
# Initialize
agilev openhands init              # Set up integration
agilev openhands doctor             # Validate setup

# Run agents
agilev openhands run                # Launch OpenHands
  --task AAV-XXXX                   # Task ID (or use AGILEV_TASK_ID)
  --prompt "..."                    # Prompt for agent
  --builder-verifier                # Use builder/verifier workflow
  --max-iterations 50               # Max iterations (default: 50)
  --timeout 3600                    # Timeout in seconds
  --model gpt-4                     # Model to use

# Evidence & Reports
agilev openhands evidence collect   # Collect evidence
  --task AAV-XXXX

agilev openhands handoff            # Generate handoff report
  --task AAV-XXXX

agilev openhands validate           # Validate session
  --task AAV-XXXX
  --scope                           # Validate scope only

# Sessions
agilev openhands sessions           # List sessions
  --task AAV-XXXX                   # Filter by task

agilev openhands session SESSION_ID # Show session details

# Events
agilev openhands events             # List events
  --task AAV-XXXX                   # Filter by task
  --type session_started            # Filter by type
  --limit 50                        # Max events to show
  -v                                # Verbose output

agilev openhands timeline           # Show task timeline
  --task AAV-XXXX

agilev openhands verify-chain       # Verify event chain integrity

# GitHub Actions
agilev openhands github-actions     # Generate CI/CD workflows
```

---

## Troubleshooting

### OpenHands Not Found

**Problem:** `openhands: command not found`

**Solution:**

```bash
# Check Docker installation
docker images | grep openhands

# If not found, pull image
docker pull ghcr.io/all-hands-ai/openhands:latest

# Or install locally
git clone https://github.com/All-Hands-AI/OpenHands.git
cd OpenHands && make build
```

### Scope Violations

**Problem:** "Scope violation: File not in allowed_paths"

**Solution:**

Check task brief YAML frontmatter:

```yaml
---
allowed_paths:
  - src/upload/**      # Use ** for nested paths
  - tests/upload/**
blocked_paths:
  - src/auth/**
---
```

**Pattern Guide:**
- `src/**` - All files in src/ and subdirectories
- `src/*.py` - Only .py files directly in src/
- `src/upload/**` - All files in src/upload/ and below
- `**/test_*.py` - All test files anywhere

### Hook Not Running

**Problem:** Hooks don't execute

**Solution:**

```bash
# Check hook permissions
ls -l .openhands/hooks/

# Make executable
chmod +x .openhands/hooks/*.sh

# Test hook manually
echo '{"tool_name":"edit","tool_args":{"file_path":"test.py"}}' | \
  .openhands/hooks/validate_scope.sh
```

### Evidence Collection Fails

**Problem:** "No evidence found"

**Solution:**

```bash
# Check git history
git log --oneline -10

# Ensure changes are committed
git add .
git commit -m "Implement feature [AAV-0042]"

# Try collection again
agilev openhands evidence collect --task AAV-0042
```

---

## Best Practices

### 1. Task Brief Quality

**Good Task Brief:**

```yaml
---
allowed_paths:
  - src/upload/**
  - tests/upload/**
blocked_paths:
  - src/auth/**
public_api_changes_allowed: false
dependency_changes_allowed: false
---

# Add Retry Logic to File Upload

## Objectives

- Implement exponential backoff retry for failed uploads
- Add configurable max retry count
- Log all retry attempts

## Acceptance Criteria

- [ ] Upload retries up to 3 times by default
- [ ] Exponential backoff: 1s, 2s, 4s
- [ ] Tests cover success and failure cases
- [ ] No changes to authentication code
```

**Bad Task Brief:**

```markdown
# Fix upload

Make it better
```

### 2. Scope Definition

**Narrow Scope (Better):**

```yaml
allowed_paths:
  - src/services/upload/retry.py
  - tests/unit/test_upload_retry.py
```

**Broad Scope (Risky):**

```yaml
allowed_paths:
  - src/**  # Too permissive!
```

### 3. Risk Levels

- **L0-L1:** Low-risk changes, basic evidence
- **L2:** Medium risk, comprehensive tests required
- **L3-L4:** High risk, security review, gradual rollout

**High-risk example:**

```yaml
# L4 change - authentication system
---
allowed_paths:
  - src/auth/**
blocked_paths:
  - src/secrets/keys.py  # Never touch production keys!
public_api_changes_allowed: true
dependency_changes_allowed: true
---
```

### 4. Evidence Quality

**Good evidence:**
- All tests pass
- Linting/type checking clean
- Git commits show only intended changes
- No scope violations

**Bad evidence:**
- Tests missing or failing
- Linting errors
- Changes outside scope
- No verification

---

## Examples

### Example 1: Simple Feature Addition

```bash
# Task: Add logging to existing function

# 1. Create task
agilev new --title "Add logging to upload" --risk L1

# 2. Define scope
cat > .agentic-agile-v/tasks/AAV-0100/task_brief.md << 'EOF'
---
allowed_paths:
  - src/services/upload.py
  - tests/test_upload.py
public_api_changes_allowed: false
dependency_changes_allowed: false
---

# Add Logging to Upload Function

Add debug logging to track upload progress.
EOF

# 3. Run OpenHands
agilev openhands run \
  --task AAV-0100 \
  --prompt "Add logging statements to upload function"

# 4. Review and get handoff
agilev openhands handoff --task AAV-0100
```

### Example 2: Complex Refactoring with Builder/Verifier

```bash
# Task: Refactor upload module

# 1. Create high-risk task
agilev new --title "Refactor upload module" --risk L2

# 2. Define comprehensive scope
cat > .agentic-agile-v/tasks/AAV-0101/task_brief.md << 'EOF'
---
allowed_paths:
  - src/upload/**
  - tests/upload/**
blocked_paths:
  - src/upload/legacy/**  # Don't touch legacy code
public_api_changes_allowed: false
dependency_changes_allowed: false
---

# Refactor Upload Module

Extract retry logic into separate class.

## Acceptance Criteria
- [ ] RetryHandler class created
- [ ] All existing tests still pass
- [ ] New tests for RetryHandler
- [ ] No public API changes
- [ ] Code coverage >= 90%
EOF

# 3. Run with builder/verifier
agilev openhands run \
  --task AAV-0101 \
  --builder-verifier

# This runs:
# - Builder implements refactoring
# - Verifier reviews code
# - Up to 3 cycles until approved

# 4. Check results
agilev openhands sessions --task AAV-0101
agilev openhands timeline --task AAV-0101
agilev openhands handoff --task AAV-0101
```

### Example 3: CI/CD Integration

```bash
# 1. Generate workflows
agilev openhands github-actions

# 2. Commit workflows
git add .github/workflows/agilev-*.yml
git commit -m "Add Agile-V CI/CD workflows"
git push

# 3. Create PR with task ID in title
git checkout -b feature/AAV-0102-add-caching
# ... make changes ...
git commit -m "Add caching [AAV-0102]"
git push -u origin feature/AAV-0102-add-caching

# Create PR with title: "AAV-0102: Add caching to uploads"

# GitHub Actions will:
# ✅ Extract task ID from PR title
# ✅ Validate task brief exists
# ✅ Check scope compliance
# ✅ Post handoff report to PR
```

### Example 4: Audit Trail Verification

```bash
# After implementation, verify audit trail

# 1. View all events for task
agilev openhands timeline --task AAV-0103

# Output:
# [14:30:00] EVT-00000123
#   Type: session_started
#   Actor: openhands
#   Summary: Started builder session...
#
# [14:35:42] EVT-00000124
#   Type: session_completed
#   Actor: openhands
#   Summary: Completed builder session...

# 2. Verify chain integrity
agilev openhands verify-chain

# Output:
# ✅ Event chain is valid!
# Chain summary:
#   Total events: 156
#   First event: EVT-00000001 (2026-06-01T10:00:00)
#   Last event: EVT-00000156 (2026-06-08T14:35:42)
#   Head hash: sha256:abc123...
#   Tail hash: sha256:def456...

# 3. Export task timeline for compliance
agilev openhands timeline --task AAV-0103 > AAV-0103-audit.txt
```

---

## Next Steps

1. **Try the Quick Start** - Get hands-on in 5 minutes
2. **Review Examples** - Learn from real scenarios
3. **Set Up CI/CD** - Automate with GitHub Actions
4. **Read Integration Guide** - Deep dive: `docs/integrations/openhands.md`
5. **Customize** - Adjust hooks and skills for your needs

---

## Support

- **Documentation:** `docs/integrations/openhands.md`
- **Quick Start:** `OPENHANDS_QUICKSTART.md`
- **Troubleshooting:** `agilev openhands doctor`
- **Issues:** Report at your repository issue tracker

---

**Version:** 2.0  
**Last Updated:** 2026-06-08  
**Status:** ✅ Production Ready
