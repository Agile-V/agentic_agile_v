"""OpenHands scaffold generator.

Generates integration files for OpenHands including skills, hooks,
configuration files, and policy templates.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class OpenHandsScaffold:
    """Generator for OpenHands integration files."""

    def __init__(self, repo_root: Path | None = None):
        """Initialize scaffold generator.

        Args:
            repo_root: Repository root directory (defaults to current directory)
        """
        self.repo_root = repo_root or Path.cwd()

    def init(self, force: bool = False) -> dict[str, Path]:
        """Initialize OpenHands integration structure.

        Args:
            force: Overwrite existing files if True

        Returns:
            Dictionary mapping component names to created file paths
        """
        created_files = {}

        # Create directory structure
        dirs = [
            ".agents/skills/agile-v-core",
            ".agents/skills/agile-v-builder",
            ".agents/skills/agile-v-verifier",
            ".agents/skills/agile-v-evidence",
            ".agents/skills/agile-v-risk-classifier",
            ".openhands/hooks",
            ".openhands/logs",
            "config/policies",
        ]

        for d in dirs:
            (self.repo_root / d).mkdir(parents=True, exist_ok=True)

        # Generate skills
        created_files.update(self._generate_skills(force))

        # Generate hooks
        created_files.update(self._generate_hooks(force))

        # Generate setup script
        created_files.update(self._generate_setup_script(force))

        # Generate policy files
        created_files.update(self._generate_policies(force))

        return created_files

    def _generate_skills(self, force: bool = False) -> dict[str, Path]:
        """Generate skill files."""
        skills_dir = self.repo_root / ".agents/skills"
        created = {}

        # agile-v-core skill
        core_skill = skills_dir / "agile-v-core/SKILL.md"
        if force or not core_skill.exists():
            core_skill.write_text(self._get_core_skill_content())
            created["skill_core"] = core_skill

        # agile-v-builder skill
        builder_skill = skills_dir / "agile-v-builder/SKILL.md"
        if force or not builder_skill.exists():
            builder_skill.write_text(self._get_builder_skill_content())
            created["skill_builder"] = builder_skill

        # agile-v-verifier skill
        verifier_skill = skills_dir / "agile-v-verifier/SKILL.md"
        if force or not verifier_skill.exists():
            verifier_skill.write_text(self._get_verifier_skill_content())
            created["skill_verifier"] = verifier_skill

        # agile-v-evidence skill
        evidence_skill = skills_dir / "agile-v-evidence/SKILL.md"
        if force or not evidence_skill.exists():
            evidence_skill.write_text(self._get_evidence_skill_content())
            created["skill_evidence"] = evidence_skill

        # agile-v-risk-classifier skill
        risk_skill = skills_dir / "agile-v-risk-classifier/SKILL.md"
        if force or not risk_skill.exists():
            risk_skill.write_text(self._get_risk_classifier_skill_content())
            created["skill_risk"] = risk_skill

        return created

    def _generate_hooks(self, force: bool = False) -> dict[str, Path]:
        """Generate hook files."""
        hooks_dir = self.repo_root / ".openhands/hooks"
        created = {}

        # hooks.json
        hooks_json = self.repo_root / ".openhands/hooks.json"
        if force or not hooks_json.exists():
            hooks_json.write_text(json.dumps(self._get_hooks_config(), indent=2))
            created["hooks_config"] = hooks_json

        # Hook scripts
        hook_scripts = {
            "enforce_task_brief.sh": self._get_enforce_task_brief_hook(),
            "block_unsafe_commands.sh": self._get_block_unsafe_commands_hook(),
            "validate_scope.sh": self._get_validate_scope_hook(),
            "log_tool_usage.sh": self._get_log_tool_usage_hook(),
            "collect_session_metadata.sh": self._get_collect_session_metadata_hook(),
            "check_wiki_freshness.sh": self._get_check_wiki_freshness_hook(),
            "validate_evidence_on_stop.sh": self._get_validate_evidence_on_stop_hook(),
            "generate_handoff_on_session_end.sh": self._get_generate_handoff_hook(),
        }

        for script_name, content in hook_scripts.items():
            script_path = hooks_dir / script_name
            if force or not script_path.exists():
                script_path.write_text(content)
                script_path.chmod(0o755)  # Make executable
                created[f"hook_{script_name.replace('.sh', '')}"] = script_path

        return created

    def _generate_setup_script(self, force: bool = False) -> dict[str, Path]:
        """Generate setup script."""
        setup_script = self.repo_root / ".openhands/setup.sh"
        if force or not setup_script.exists():
            setup_script.write_text(self._get_setup_script_content())
            setup_script.chmod(0o755)
            return {"setup_script": setup_script}
        return {}

    def _generate_policies(self, force: bool = False) -> dict[str, Path]:
        """Generate policy files."""
        policies_dir = self.repo_root / "config/policies"
        created = {}

        policy_files = {
            "openhands_dangerous_commands.yaml": self._get_dangerous_commands_policy(),
            "scope_policy.yaml": self._get_scope_policy(),
            "approval_policy.yaml": self._get_approval_policy(),
            "evidence_policy.yaml": self._get_evidence_policy(),
            "risk_level_policy.yaml": self._get_risk_level_policy(),
        }

        for filename, content in policy_files.items():
            policy_path = policies_dir / filename
            if force or not policy_path.exists():
                policy_path.write_text(content)
                created[f"policy_{filename.replace('.yaml', '')}"] = policy_path

        return created

    def doctor(self) -> dict[str, bool]:
        """Validate OpenHands integration setup.

        Returns:
            Dictionary mapping check names to pass/fail status
        """
        checks = {}

        # Check AGENTS.md
        checks["agents_md"] = (self.repo_root / "AGENTS.md").exists()

        # Check skills
        skills = [
            "agile-v-core",
            "agile-v-builder",
            "agile-v-verifier",
            "agile-v-evidence",
            "agile-v-risk-classifier",
        ]
        for skill in skills:
            skill_path = self.repo_root / f".agents/skills/{skill}/SKILL.md"
            checks[f"skill_{skill}"] = skill_path.exists()

        # Check setup script
        setup_script = self.repo_root / ".openhands/setup.sh"
        checks["setup_script"] = setup_script.exists() and setup_script.stat().st_mode & 0o111

        # Check hooks.json
        checks["hooks_config"] = (self.repo_root / ".openhands/hooks.json").exists()

        # Check hook scripts
        hook_scripts = [
            "enforce_task_brief.sh",
            "block_unsafe_commands.sh",
            "validate_scope.sh",
            "log_tool_usage.sh",
            "collect_session_metadata.sh",
            "check_wiki_freshness.sh",
            "validate_evidence_on_stop.sh",
            "generate_handoff_on_session_end.sh",
        ]
        for script in hook_scripts:
            script_path = self.repo_root / f".openhands/hooks/{script}"
            checks[f"hook_{script}"] = script_path.exists() and script_path.stat().st_mode & 0o111

        # Check config
        checks["openhands_config"] = (self.repo_root / "config/openhands.yaml").exists()

        # Check policies
        policies = [
            "openhands_dangerous_commands.yaml",
            "scope_policy.yaml",
            "approval_policy.yaml",
            "evidence_policy.yaml",
            "risk_level_policy.yaml",
        ]
        for policy in policies:
            policy_path = self.repo_root / f"config/policies/{policy}"
            checks[f"policy_{policy}"] = policy_path.exists()

        return checks

    # Content generation methods

    def _get_core_skill_content(self) -> str:
        return """---
name: agile-v-core
description: Apply Agentic Agile-V process control, task briefs, risk-based evidence gates, and human approval rules.
---

# Agile-V Core Rules

## Operating Principle

Conversation is allowed for discovery. Implementation requires a structured task brief.

Do not implement from an ambiguous chat history.

## Before Editing Code

1. Locate the task brief (`.agentic-agile-v/tasks/AAV-XXXX/task_brief.md`)
2. Confirm risk level (L0-L4)
3. Confirm allowed and blocked paths
4. Confirm acceptance criteria
5. Produce a short plan

## Completion Criteria

A change is complete only when the evidence bundle satisfies the required risk level.

Generating code is not completion. Passing evidence validation is completion.

## Never

- Remove tests to make a build pass
- Weaken security controls (auth, crypto, input validation)
- Add dependencies without approval
- Modify public APIs unless explicitly requested
- Self-approve high-risk work (L3/L4)
- Expand scope beyond allowed paths
- Commit secrets, tokens, credentials, or personal data
- Bypass task brief requirements

## Evidence Requirements by Risk Level

| Level | Tests | Verifier | Approval | Special |
|-------|-------|----------|----------|---------|
| L0 | Optional | No | No | - |
| L1 | Required or rationale | No | No | - |
| L2 | Passing tests | Yes | Reviewer | - |
| L3 | Passing tests | Yes | Domain owner | Rollback path |
| L4 | Passing tests | Yes | Formal approval | Traceability + simulation/HIL/formal |

## Scope Control

Changed files must be within `allowed_paths` from the task brief.

Files in `blocked_paths` must not be modified.

Dependency changes require explicit approval in the task brief.

## Handoff

On session end, generate a handoff summary:
- Current objective
- Changed files
- Tests run
- Open risks
- Next recommended action
"""

    def _get_builder_skill_content(self) -> str:
        return """---
name: agile-v-builder
description: Implementation behavior for OpenHands builder sessions.
---

# Agile-V Builder

## Role

Implement the change described in the task brief.

## Workflow

1. **Inspect** repository structure and relevant code
2. **Plan** minimal implementation that satisfies acceptance criteria
3. **Edit** only files within allowed paths
4. **Test** narrow tests first, then broader tests
5. **Check** run lint, typecheck, build as applicable
6. **Document** update evidence bundle with changed files, test results
7. **Summarize** produce implementation summary

## Minimize Scope

- Make the smallest change that satisfies acceptance criteria
- Do not refactor unrelated code
- Do not change public APIs unless brief allows
- Do not add dependencies unless brief allows

## Test-First Mindset

For L1+:
- Add or update tests before claiming completion
- Run tests and record results
- If tests cannot be added, document test rationale

For L2+:
- Tests must pass
- Lint and typecheck must pass
- Evidence bundle must record passing results

## Evidence Collection

Update evidence bundle (`.agentic-agile-v/tasks/AAV-XXXX/evidence_bundle.json`):
- `changed_files`: List of modified files
- `tests.added`: Tests added
- `tests.modified`: Tests modified
- `tests.run`: Test commands executed
- `tests.results`: Pass/fail status
- `checks`: Lint, typecheck, build results

## Known Risks

Document residual risks in implementation summary:
- Edge cases not yet tested
- Performance concerns
- Rollback considerations
- Dependency version constraints

## Implementation Summary

Produce `.agentic-agile-v/tasks/AAV-XXXX/implementation_summary.md`:
- What was implemented
- Why (acceptance criteria mapping)
- Changed files
- Tests added/modified
- Test results
- Residual risks
"""

    def _get_verifier_skill_content(self) -> str:
        return """---
name: agile-v-verifier
description: Independent review behavior for OpenHands verifier sessions.
---

# Agile-V Verifier

## Role

Independently verify that the implementation satisfies acceptance criteria.

## Fresh Context Requirement

Verifier runs in a separate session with no memory of builder session.

Read from scratch:
- Task brief
- Acceptance criteria
- Implementation diff
- Evidence bundle
- Test results

## Workflow

1. **Read** task brief and acceptance criteria
2. **Inspect** implementation diff
3. **Challenge** assumptions and look for edge cases
4. **Verify** each acceptance criterion has evidence
5. **Test** run or request additional tests if needed
6. **Scope** check changed files against allowed paths
7. **Report** produce verification report with pass/fail/needs-review

## Verification Checklist

For each acceptance criterion:
- [ ] Mapped to specific code changes
- [ ] Has test coverage or rationale
- [ ] Tests pass (for L2+)
- [ ] Edge cases considered
- [ ] Scope within allowed paths

## Look For

- Scope creep (changes outside allowed paths)
- Missing tests
- Weakened security controls
- Removed tests
- Fabricated evidence
- Unhandled edge cases
- Performance concerns
- Rollback path (L3+)

## Verification Result

Recommend one of:
- **pass**: All criteria satisfied, evidence complete
- **fail**: Criteria not met, evidence incomplete
- **needs-human-review**: Ambiguous or high-risk, escalate to human

## Verification Report

Produce `.agentic-agile-v/tasks/AAV-XXXX/verifier_report.md`:
- Criteria coverage (each criterion → evidence)
- Scope validation (changed files vs allowed paths)
- Test coverage assessment
- Edge cases identified
- Residual risks
- Recommendation (pass/fail/needs-review)

## Constraints

Verifier is read-only by default.

If issues found, produce report first. Builder can address issues in a separate iteration.

## Never

- Approve L3/L4 changes autonomously (human approval always required)
- Convert failing tests to passing without code fix
- Weaken criteria to make evidence pass
- Trust builder self-report alone (verify via Git/CI)
"""

    def _get_evidence_skill_content(self) -> str:
        return """---
name: agile-v-evidence
description: Evidence collection and update behavior.
---

# Agile-V Evidence Collection

## Purpose

Maintain accurate evidence bundle throughout the task lifecycle.

## Evidence Bundle Location

`.agentic-agile-v/tasks/AAV-XXXX/evidence_bundle.json`

## Required Fields

```json
{
  "task_id": "AAV-XXXX",
  "risk_level": "L1|L2|L3|L4",
  "changed_files": [],
  "tests": {
    "added": [],
    "modified": [],
    "run": [],
    "results": []
  },
  "checks": {
    "lint": {},
    "typecheck": {},
    "build": {}
  }
}
```

## OpenHands Extensions

If using OpenHands, add:
```json
{
  "agent_execution": {
    "engine": "openhands",
    "mode": "builder|verifier",
    "session_id": "...",
    "tool_log_path": "logs/openhands_tool_log.jsonl"
  },
  "scope_control": {
    "allowed_paths": [],
    "blocked_paths": [],
    "changed_files_within_scope": true
  }
}
```

## Collect Evidence From

- Git: `git diff --name-only` for changed files
- Test output: Parse test command output
- CI results: Parse GitHub Actions / CI output
- Tool logs: OpenHands tool usage log

## Never Fabricate

- Do not claim tests passed if they failed
- Do not claim tests exist if they don't
- Do not claim checks passed if they failed
- Use Git/CI as source of truth, not agent memory

## Update After

- File edits
- Test runs
- Check runs (lint, typecheck, build)
- Session end
"""

    def _get_risk_classifier_skill_content(self) -> str:
        return """---
name: agile-v-risk-classifier
description: Risk level classification guidance (L0-L4).
---

# Agile-V Risk Classification

## Risk Levels

### L0: Trivial
- Documentation changes
- Comments
- README updates
- No code execution changes

### L1: Low Risk
- Small bug fixes
- Internal refactors (no API change)
- New unit tests
- Logging additions

### L2: Moderate Risk
- New features (internal)
- API changes (non-breaking)
- Database schema changes (additive)
- New dependencies (vetted)

### L3: High Risk
- Breaking API changes
- Authentication/authorization changes
- Cryptography changes
- Data migration
- Security-sensitive changes
- Infra changes (production)

### L4: Critical Risk
- Safety-critical systems (hardware, firmware)
- Medical devices
- Aviation, automotive
- Financial transaction integrity
- Customer data deletion/migration

## Evidence Requirements

| Level | Tests | Verifier | Approval | Special |
|-------|-------|----------|----------|---------|
| L0 | Optional | No | No | - |
| L1 | Yes or rationale | No | No | - |
| L2 | Passing | Yes | Reviewer | - |
| L3 | Passing | Yes | Domain owner | Rollback path |
| L4 | Passing | Yes | Formal | Simulation/HIL/formal + traceability |

## When Unsure

Default to higher risk level.

L3/L4 classification requires explicit risk assessment document.
"""

    def _get_hooks_config(self) -> dict[str, Any]:
        return {
            "user_prompt_submit": [
                {
                    "matcher": "*",
                    "hooks": [{"command": ".openhands/hooks/enforce_task_brief.sh", "timeout": 30}],
                }
            ],
            "pre_tool_use": [
                {
                    "matcher": "terminal",
                    "hooks": [
                        {"command": ".openhands/hooks/block_unsafe_commands.sh", "timeout": 10}
                    ],
                },
                {
                    "matcher": "*",
                    "hooks": [{"command": ".openhands/hooks/validate_scope.sh", "timeout": 20}],
                },
            ],
            "post_tool_use": [
                {
                    "matcher": "*",
                    "hooks": [
                        {
                            "command": ".openhands/hooks/log_tool_usage.sh",
                            "timeout": 10,
                            "async": True,
                        }
                    ],
                }
            ],
            "session_start": [
                {
                    "matcher": "*",
                    "hooks": [
                        {
                            "command": ".openhands/hooks/collect_session_metadata.sh",
                            "timeout": 10,
                            "async": True,
                        },
                        {
                            "command": ".openhands/hooks/check_wiki_freshness.sh",
                            "timeout": 15,
                            "async": True,
                        },
                    ],
                }
            ],
            "stop": [
                {
                    "matcher": "*",
                    "hooks": [
                        {"command": ".openhands/hooks/validate_evidence_on_stop.sh", "timeout": 180}
                    ],
                }
            ],
            "session_end": [
                {
                    "matcher": "*",
                    "hooks": [
                        {
                            "command": ".openhands/hooks/generate_handoff_on_session_end.sh",
                            "timeout": 60,
                            "async": True,
                        }
                    ],
                }
            ],
        }

    def _get_enforce_task_brief_hook(self) -> str:
        return """#!/usr/bin/env bash
# Agile-V Hook: enforce_task_brief
# Block implementation without task ID or task brief

set -euo pipefail

# Read JSON input from stdin
INPUT=$(cat)

# Extract prompt
PROMPT=$(echo "$INPUT" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('prompt', ''))" 2>/dev/null || echo "")

# Try to find task ID from various sources
TASK_ID=""

# 1. Environment variable
if [ -n "${AGILEV_TASK_ID:-}" ]; then
    TASK_ID="$AGILEV_TASK_ID"
fi

# 2. Git branch name (aav-0001-* pattern)
if [ -z "$TASK_ID" ]; then
    BRANCH=$(git branch --show-current 2>/dev/null || echo "")
    if [[ "$BRANCH" =~ ^aav-([0-9]+) ]]; then
        TASK_NUM="${BASH_REMATCH[1]}"
        TASK_ID="AAV-$(printf '%04d' $TASK_NUM)"
    fi
fi

# 3. Prompt contains AAV-XXXX
if [ -z "$TASK_ID" ]; then
    if [[ "$PROMPT" =~ AAV-([0-9]{4}) ]]; then
        TASK_ID="${BASH_REMATCH[0]}"
    fi
fi

# If no task ID found, deny
if [ -z "$TASK_ID" ]; then
    cat <<EOF
{
  "decision": "deny",
  "reason": "No task ID found. Create task brief first: agilev new --title '...' --risk L1"
}
EOF
    exit 2
fi

# Check if task brief exists
BRIEF_PATH=".agentic-agile-v/tasks/$TASK_ID/task_brief.md"
if [ ! -f "$BRIEF_PATH" ]; then
    cat <<EOF
{
  "decision": "deny",
  "reason": "Task brief not found at $BRIEF_PATH. Create it first: agilev new --title '...' --risk L1"
}
EOF
    exit 2
fi

# Task brief exists, allow
cat <<EOF
{
  "decision": "allow",
  "reason": "Task $TASK_ID has valid task brief"
}
EOF
exit 0
"""

    def _get_block_unsafe_commands_hook(self) -> str:
        return """#!/usr/bin/env bash
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
"""

    def _get_validate_scope_hook(self) -> str:
        return """#!/usr/bin/env bash
# Agile-V Hook: validate_scope
# Warn or block when action appears outside allowed scope

set -euo pipefail

# Read JSON input from stdin
INPUT=$(cat)

# Extract tool name and file path
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('tool_name', ''))" 2>/dev/null || echo "")
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('tool_args', {}).get('file_path', ''))" 2>/dev/null || echo "")

# If no file path, allow (can't validate scope)
if [ -z "$FILE_PATH" ]; then
    cat <<EOF
{
  "decision": "allow",
  "reason": "No file path to validate"
}
EOF
    exit 0
fi

# Try to resolve task ID
TASK_ID="${AGILEV_TASK_ID:-}"
if [ -z "$TASK_ID" ]; then
    BRANCH=$(git branch --show-current 2>/dev/null || echo "")
    if [[ "$BRANCH" =~ ^aav-([0-9]+) ]]; then
        TASK_NUM="${BASH_REMATCH[1]}"
        TASK_ID="AAV-$(printf '%04d' $TASK_NUM)"
    fi
fi

# If no task ID, allow (will be caught by enforce_task_brief)
if [ -z "$TASK_ID" ]; then
    cat <<EOF
{
  "decision": "allow",
  "reason": "No task ID to validate scope against"
}
EOF
    exit 0
fi

# Check if task brief exists
BRIEF_PATH=".agentic-agile-v/tasks/$TASK_ID/task_brief.md"
if [ ! -f "$BRIEF_PATH" ]; then
    cat <<EOF
{
  "decision": "allow",
  "reason": "Task brief not found, cannot validate scope"
}
EOF
    exit 0
fi

# TODO: Parse allowed_paths and blocked_paths from task brief YAML frontmatter
# For MVP, allow all changes and log warning
cat <<EOF
{
  "decision": "allow",
  "reason": "Scope validation not yet implemented (MVP). File: $FILE_PATH"
}
EOF
exit 0
"""

    def _get_log_tool_usage_hook(self) -> str:
        return """#!/usr/bin/env bash
# Agile-V Hook: log_tool_usage
# Append tool events to session log

set -euo pipefail

# Read JSON input from stdin
INPUT=$(cat)

# Try to resolve task ID
TASK_ID="${AGILEV_TASK_ID:-}"
if [ -z "$TASK_ID" ]; then
    BRANCH=$(git branch --show-current 2>/dev/null || echo "")
    if [[ "$BRANCH" =~ ^aav-([0-9]+) ]]; then
        TASK_NUM="${BASH_REMATCH[1]}"
        TASK_ID="AAV-$(printf '%04d' $TASK_NUM)"
    fi
fi

# If no task ID, skip logging
if [ -z "$TASK_ID" ]; then
    exit 0
fi

# Ensure log directory exists
LOG_DIR=".agentic-agile-v/tasks/$TASK_ID/logs"
mkdir -p "$LOG_DIR"

# Append to tool log
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
echo "$INPUT" | jq -c ". + {timestamp: \\"$TIMESTAMP\\"}" >> "$LOG_DIR/openhands_tool_log.jsonl" 2>/dev/null || true

exit 0
"""

    def _get_collect_session_metadata_hook(self) -> str:
        return """#!/usr/bin/env bash
# Agile-V Hook: collect_session_metadata
# Record session metadata at session start

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

# Ensure log directory exists
LOG_DIR=".agentic-agile-v/tasks/$TASK_ID/logs"
mkdir -p "$LOG_DIR"

# Record session metadata
SESSION_ID="${OPENHANDS_SESSION_ID:-unknown}"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

cat > "$LOG_DIR/openhands_session.json" <<EOF
{
  "task_id": "$TASK_ID",
  "session_id": "$SESSION_ID",
  "started_at": "$TIMESTAMP",
  "engine": "openhands"
}
EOF

exit 0
"""

    def _get_check_wiki_freshness_hook(self) -> str:
        return """#!/usr/bin/env bash
# Agile-V Hook: check_wiki_freshness
# Advisory-only (never blocks): warn if the OpenWiki knowledge layer
# (openwiki/) is missing, stale, or fails structural validation.

set -euo pipefail

if ! command -v agilev &> /dev/null; then
    exit 0
fi

if [ ! -d "openwiki" ]; then
    cat <<EOF
{
  "decision": "allow",
  "reason": "openwiki/ not found. Run 'agilev wiki init' to scaffold the knowledge layer."
}
EOF
    exit 0
fi

if agilev wiki validate &> /tmp/agilev_wiki_validate.$$ 2>&1; then
    cat <<EOF
{
  "decision": "allow",
  "reason": "OpenWiki knowledge layer is valid."
}
EOF
else
    REASON=$(tr '\\n' ' ' < /tmp/agilev_wiki_validate.$$ | head -c 500)
    cat <<EOF
{
  "decision": "allow",
  "reason": "OpenWiki knowledge layer validation warnings/errors (non-blocking): ${REASON}"
}
EOF
fi
rm -f /tmp/agilev_wiki_validate.$$

exit 0
"""

    def _get_validate_evidence_on_stop_hook(self) -> str:
        return """#!/usr/bin/env bash
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
"""

    def _get_generate_handoff_hook(self) -> str:
        return """#!/usr/bin/env bash
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
"""

    def _get_setup_script_content(self) -> str:
        return """#!/usr/bin/env bash
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
"""

    def _get_dangerous_commands_policy(self) -> str:
        return """# Dangerous Commands Policy
# Commands that OpenHands must not execute

blocked_patterns:
  - pattern: "rm -rf /"
    reason: "Destructive filesystem operation"
  - pattern: "dd if="
    reason: "Low-level disk operation"
  - pattern: "mkfs"
    reason: "Filesystem creation can destroy data"
  - pattern: ":(){ :|:& };:"
    reason: "Fork bomb"
  - pattern: "chmod 777"
    reason: "Insecure permission setting"
  - pattern: "> /dev/sd"
    reason: "Direct disk write"
  - pattern: "curl .* | sudo bash"
    reason: "Execute untrusted remote code as root"
  - pattern: "wget .* | sudo sh"
    reason: "Execute untrusted remote code as root"
  - pattern: "sudo rm"
    reason: "Elevated destructive operation"
  - pattern: "git push --force"
    reason: "Can rewrite shared history"

allowed_exceptions:
  - pattern: "chmod 777"
    when: "Explicitly allowed in task brief"
    requires_approval: true
"""

    def _get_scope_policy(self) -> str:
        return """# Scope Policy
# Default scope control behavior for OpenHands

default_behavior: deny_out_of_scope

# Allow changes to task-related files
allow_task_files: true

# Allow changes to evidence files
allow_evidence_files: true

# Require explicit permission for public API changes
require_explicit_public_api_permission: true

# Require approval for dependency changes
require_dependency_approval: true

# Security-sensitive paths that require L3+ approval
security_sensitive_paths:
  - pattern: "**/auth/**"
    reason: "Authentication code"
  - pattern: "**/authorization/**"
    reason: "Authorization code"
  - pattern: "**/crypto/**"
    reason: "Cryptography code"
  - pattern: "**/secrets/**"
    reason: "Secrets management"
  - pattern: "**/security/**"
    reason: "Security controls"
  - pattern: "**/*password*"
    reason: "Password handling"
  - pattern: "**/*token*"
    reason: "Token handling"

# Infra paths that require approval
infrastructure_paths:
  - "infra/**"
  - "terraform/**"
  - "ansible/**"
  - ".github/workflows/**"
  - "Dockerfile"
  - "docker-compose.yml"
  - "k8s/**"
  - "kubernetes/**"

# Always allowed paths (even without task brief)
always_allowed:
  - "evidence/**"
  - ".agentic-agile-v/**"
  - "**/*.md"  # Documentation (L0)
"""

    def _get_approval_policy(self) -> str:
        return """# Approval Policy
# Human approval requirements by risk level

risk_levels:
  L0:
    human_approval_required: false
    approvers: []
  
  L1:
    human_approval_required: false
    approvers: []
  
  L2:
    human_approval_required: true
    approvers:
      - type: "reviewer"
        count: 1
        description: "Any team member can review L2 changes"
  
  L3:
    human_approval_required: true
    approvers:
      - type: "domain_owner"
        count: 1
        description: "Requires approval from domain owner or tech lead"
    additional_requirements:
      - "rollback_path_documented"
      - "verifier_report_passed"
  
  L4:
    human_approval_required: true
    approvers:
      - type: "independent_verifier"
        count: 1
        description: "Independent verification required"
      - type: "formal_approval"
        count: 1
        description: "Formal approval from designated authority"
    additional_requirements:
      - "rollback_path_documented"
      - "simulation_or_hil_evidence"
      - "traceability_matrix"
      - "verifier_report_passed"

# GitHub integration
github:
  use_codeowners: true
  required_reviews_by_risk:
    L0: 0
    L1: 0
    L2: 1
    L3: 2
    L4: 3
  
  dismiss_stale_reviews: false
  require_code_owner_reviews:
    L3: true
    L4: true
"""

    def _get_evidence_policy(self) -> str:
        return """# Evidence Policy
# Evidence requirements by risk level

risk_levels:
  L0:
    required_evidence:
      - "changed_files"
    optional_evidence:
      - "tests"
    
  L1:
    required_evidence:
      - "task_brief"
      - "changed_files"
      - "tests_or_rationale"
    optional_evidence:
      - "checks"
  
  L2:
    required_evidence:
      - "task_brief"
      - "changed_files"
      - "tests_added_or_modified"
      - "tests_passed"
      - "checks_passed"
      - "verifier_report"
    optional_evidence:
      - "performance_benchmarks"
  
  L3:
    required_evidence:
      - "task_brief"
      - "risk_assessment"
      - "changed_files"
      - "tests_added_or_modified"
      - "tests_passed"
      - "checks_passed"
      - "rollback_path"
      - "verifier_report"
      - "domain_owner_approval"
    optional_evidence:
      - "performance_benchmarks"
      - "load_testing"
  
  L4:
    required_evidence:
      - "task_brief"
      - "formal_risk_assessment"
      - "changed_files"
      - "tests_added_or_modified"
      - "tests_passed"
      - "checks_passed"
      - "rollback_path"
      - "simulation_or_hil"
      - "traceability_matrix"
      - "verifier_report"
      - "independent_verification"
      - "formal_approval"
    optional_evidence:
      - "formal_methods_proof"
      - "certification_evidence"

# Validation rules
validation:
  fail_on_missing_required: true
  warn_on_missing_optional: true
  allow_override_for_risk_levels: []  # No overrides
"""

    def _get_risk_level_policy(self) -> str:
        return """# Risk Level Policy
# Guidance for risk classification (L0-L4)

risk_levels:
  L0:
    name: "Trivial"
    description: "No code execution changes"
    examples:
      - "Documentation updates"
      - "Comment changes"
      - "README updates"
      - "Markdown formatting"
    
  L1:
    name: "Low Risk"
    description: "Small, isolated changes with limited blast radius"
    examples:
      - "Small bug fixes (internal)"
      - "Internal refactors (no API change)"
      - "New unit tests"
      - "Logging additions"
      - "Error message improvements"
    
  L2:
    name: "Moderate Risk"
    description: "Moderate changes with potential customer impact"
    examples:
      - "New features (internal)"
      - "API changes (non-breaking, additive)"
      - "Database schema changes (additive columns)"
      - "New vetted dependencies"
      - "Performance optimizations"
    
  L3:
    name: "High Risk"
    description: "Significant changes with high impact potential"
    examples:
      - "Breaking API changes"
      - "Authentication/authorization changes"
      - "Cryptography changes"
      - "Data migration"
      - "Security-sensitive changes"
      - "Infrastructure changes (production)"
      - "Database schema changes (destructive)"
    
  L4:
    name: "Critical Risk"
    description: "Safety-critical or mission-critical changes"
    examples:
      - "Safety-critical systems (hardware, firmware)"
      - "Medical devices"
      - "Aviation systems"
      - "Automotive systems"
      - "Financial transaction integrity"
      - "Customer data deletion/migration"
      - "Disaster recovery procedures"

# Auto-classification hints
auto_classification:
  patterns:
    L0:
      - "**/*.md"
      - "**/README*"
      - "**/docs/**"
    
    L3_or_higher:
      - "**/auth/**"
      - "**/crypto/**"
      - "**/secrets/**"
      - "**/migration/**"
      - "infra/**"
      - "terraform/**"
  
  dependency_changes:
    default_risk: "L2"
    security_dependency: "L3"
  
  api_changes:
    additive: "L2"
    breaking: "L3"

# Escalation rules
escalation:
  when_uncertain: "escalate_to_higher_risk"
  default_risk_if_unknown: "L2"
"""
