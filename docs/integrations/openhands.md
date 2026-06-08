# OpenHands Integration

**Status:** Active  
**Integration Type:** Execution Backend  
**Agile-V Version:** ≥0.1.0  
**OpenHands Version:** Compatible with OpenHands v0.9+  

---

## Overview

This integration makes OpenHands a first-class execution backend for Agentic Agile-V while preserving Agile-V as the control, evidence, and verification layer.

**Key Principle:** OpenHands executes; Agile-V decides acceptance.

---

## Architecture

```text
Agentic Agile-V = control plane (task briefs, risk, evidence, gates)
OpenHands       = execution plane (inspect, plan, implement, test, PR)
GitHub/CI       = objective verification (tests, checks, builds)
Human review    = accountability (approval, release decision)
```

---

## Integration Components

### 1. Skills (`.agents/skills/`)

Repository-level progressive disclosure that teaches OpenHands about Agile-V rules.

| Skill | Purpose | When Loaded |
|-------|---------|-------------|
| `agile-v-core` | Core workflow rules (task brief first, evidence gates) | Always |
| `agile-v-builder` | Implementation behavior (scope, tests, evidence) | Builder sessions |
| `agile-v-verifier` | Independent review behavior (fresh context, gaps) | Verifier sessions |
| `agile-v-evidence` | Evidence collection and update | Both modes |
| `agile-v-risk-classifier` | Risk level L0-L4 guidance | Task planning |

**Example skill excerpt** (`.agents/skills/agile-v-core/SKILL.md`):
```markdown
# Agile-V Core Rules

Before editing code:
1. Locate the task brief
2. Confirm risk level
3. Confirm allowed and blocked paths
4. Confirm acceptance criteria
5. Produce a short plan

Never:
- remove tests to make a build pass
- weaken security controls
- self-approve high-risk work
```

### 2. Hooks (`.openhands/hooks/`)

Mechanical enforcement during OpenHands execution. Hooks receive JSON input via stdin and return JSON decisions.

| Hook Lifecycle | Script | Blocking | Purpose |
|----------------|--------|----------|---------|
| `user_prompt_submit` | `enforce_task_brief.sh` | Yes | Require task ID/brief before implementation |
| `pre_tool_use` (terminal) | `block_unsafe_commands.sh` | Yes | Block destructive commands |
| `pre_tool_use` (all) | `validate_scope.sh` | Yes | Warn/block out-of-scope changes |
| `post_tool_use` | `log_tool_usage.sh` | No | Append tool events to session log |
| `session_start` | `collect_session_metadata.sh` | No | Record session metadata |
| `stop` | `validate_evidence_on_stop.sh` | Yes | Block completion until evidence passes |
| `session_end` | `generate_handoff_on_session_end.sh` | No | Generate handoff summary |

**Hook decision format:**
```json
{
  "decision": "allow|deny",
  "reason": "Human-readable explanation"
}
```

Blocking hooks return exit code `2` when denying an operation.

### 3. CLI Commands (`agilev openhands ...`)

| Command | Purpose | Example |
|---------|---------|---------|
| `init` | Generate OpenHands integration files | `agilev openhands init` |
| `doctor` | Validate integration setup | `agilev openhands doctor` |
| `scaffold` | Regenerate skills and hooks | `agilev openhands scaffold` |
| `hooks test` | Test hooks with sample payloads | `agilev openhands hooks test` |
| `evidence collect` | Adapt OpenHands logs to evidence bundle | `agilev openhands evidence collect --task AAV-001` |
| `validate` | Validate scope and evidence | `agilev openhands validate --task AAV-001` |
| `handoff` | Generate handoff report | `agilev openhands handoff --task AAV-001` |

### 4. Evidence Extensions

Evidence bundle schema extended with optional OpenHands metadata:

```json
{
  "agent_execution": {
    "engine": "openhands",
    "mode": "builder",
    "session_id": "openhands-20260608-123456",
    "agent_model": "claude-3.5-sonnet",
    "started_at": "2026-06-08T10:00:00Z",
    "ended_at": "2026-06-08T10:45:00Z",
    "tool_log_path": "evidence/AAV-001/logs/openhands_tool_log.jsonl",
    "handoff_path": "evidence/AAV-001/openhands_handoff.md"
  },
  "scope_control": {
    "allowed_paths": ["src/upload/**", "tests/upload/**"],
    "blocked_paths": ["src/auth/**", "infra/**"],
    "changed_files_within_scope": true,
    "out_of_scope_changes": []
  },
  "verification": {
    "builder_summary_path": "evidence/AAV-001/implementation_summary.md",
    "verifier_report_path": "evidence/AAV-001/verifier_report.md",
    "fresh_context_verification": true,
    "verifier_result": "pass"
  }
}
```

### 5. Policy Files (`config/policies/`)

| Policy File | Purpose |
|-------------|---------|
| `openhands_dangerous_commands.yaml` | Commands to block (rm -rf, dd, etc.) |
| `scope_policy.yaml` | Default scope behavior, security-sensitive paths |
| `approval_policy.yaml` | Human approval requirements by risk level |
| `evidence_policy.yaml` | Evidence requirements by risk level |
| `risk_level_policy.yaml` | Risk classification guidance |

---

## Quick Start

### 1. Install Agile-V CLI

```bash
pip install -e .
```

### 2. Initialize OpenHands Integration

```bash
cd your-repo
agilev openhands init
```

This creates:
```text
.agents/skills/agile-v-core/SKILL.md
.agents/skills/agile-v-builder/SKILL.md
.agents/skills/agile-v-verifier/SKILL.md
.agents/skills/agile-v-evidence/SKILL.md
.agents/skills/agile-v-risk-classifier/SKILL.md
.openhands/setup.sh
.openhands/hooks.json
.openhands/hooks/*.sh
config/openhands.yaml
```

### 3. Validate Setup

```bash
agilev openhands doctor
```

Expected output:
```text
✅ AGENTS.md exists
✅ .agents/skills/agile-v-core/SKILL.md exists
✅ .openhands/setup.sh exists and is executable
✅ .openhands/hooks.json exists
✅ All required hook scripts exist and are executable
✅ Schemas exist
✅ config/openhands.yaml exists
✅ OpenHands integration ready
```

### 4. Create a Task Brief

```bash
agilev task new --title "Add retry handling" --risk L2
```

This generates:
```text
.agentic-agile-v/tasks/AAV-0001/
  task_brief.md
  evidence_bundle.json
  plan.md
```

Edit the task brief to include:
- Acceptance criteria
- Allowed paths: `src/upload/**`, `tests/upload/**`
- Blocked paths: `src/auth/**`, `infra/**`

### 5. Run OpenHands with Agile-V Integration

Currently, launch OpenHands manually and point it to the repository. The skills and hooks will activate automatically.

Future: `agilev openhands run --task AAV-0001 --mode builder`

### 6. Collect Evidence

After OpenHands completes:

```bash
agilev openhands evidence collect --task AAV-0001
```

This:
- Maps OpenHands session data into evidence bundle
- Records changed files from Git (not agent self-report)
- Maps test outputs to evidence
- Flags missing or failed tests

### 7. Validate Evidence

```bash
agilev validate --task AAV-0001
```

Checks:
- Task brief exists
- Evidence bundle validates against schema
- Scope control (changed files within allowed paths)
- Risk-appropriate evidence (tests, checks, verifier report)

### 8. Independent Verification (L2+)

For L2+ changes, run a separate verifier session:

```bash
agilev openhands verify --task AAV-0001 --fresh-context
```

Verifier:
- Starts from clean context (no builder session memory)
- Reads task brief, diff, and evidence
- Verifies each acceptance criterion
- Looks for edge cases and scope creep
- Produces verification report

### 9. Open Pull Request

OpenHands (or manual):
```bash
git checkout -b aav-0001-retry-handling
git add .
git commit -m "AAV-0001: Add retry handling"
git push origin aav-0001-retry-handling
gh pr create --title "AAV-0001: Add retry handling" --body-file evidence/AAV-0001/pr_description.md
```

PR must include:
- Link to task brief
- Risk level label
- Evidence bundle path
- Verifier report (if L2+)

### 10. GitHub CI Gates

CI workflow validates:
```bash
make test
make lint
make typecheck
agilev validate --task AAV-0001
agilev openhands validate --task AAV-0001 --scope
```

Merge is blocked if:
- Tests fail
- Evidence bundle incomplete for risk level
- Scope violations detected
- Verifier report missing (L2+)
- Human approval missing (L2+)

---

## Builder vs. Verifier Pattern

### Builder Session

**Purpose:** Implement the change

**Responsibilities:**
- Inspect repository
- Implement scoped change
- Run narrow tests first
- Run required checks
- Update evidence bundle
- Produce implementation summary

**Skill loaded:** `agile-v-builder`

**Mode:** Read-write

### Verifier Session

**Purpose:** Independent verification

**Responsibilities:**
- Start from clean context (fresh session)
- Read task brief, diff, evidence bundle, test results
- Verify each acceptance criterion
- Look for edge cases and scope creep
- Run or request relevant tests
- Produce verification report
- Recommend: pass/fail/needs-human-review

**Skill loaded:** `agile-v-verifier`

**Mode:** Read-only (by default)

**Required for:** L2+ changes

**Cannot self-approve:** L3/L4 changes (human approval always required)

---

## Scope Control

### Task Brief Scope Declaration

Every task brief includes:
```yaml
allowed_paths:
  - src/upload/**
  - tests/upload/**
blocked_paths:
  - src/auth/**
  - infra/**
public_api_changes_allowed: false
dependency_changes_allowed: false
```

### Validation

```bash
agilev openhands validate --task AAV-0001 --scope
```

Compares `git diff --name-only` against allowed/blocked paths.

**Result:**
- Changes within allowed paths: ✅ Pass
- Changes outside allowed paths: ❌ Block (unless explicit override)
- Dependency file changes: ❌ Block (unless allowed in brief)
- Public API changes: ❌ Block (unless allowed in brief)

### Hook Enforcement

`validate_scope.sh` runs on `pre_tool_use` and checks tool arguments against scope policy.

**Example block:**
```json
{
  "decision": "deny",
  "reason": "File 'src/auth/login.py' is in blocked_paths. Task brief only allows changes to src/upload/** and tests/upload/**"
}
```

---

## Risk-Level Evidence Requirements

| Risk Level | Evidence Required | Verifier | Human Approval |
|------------|-------------------|----------|----------------|
| L0 (trivial) | Minimal (README, comments, docs) | No | No |
| L1 (low) | Tests or test rationale | No | No |
| L2 (moderate) | Passing tests + checks | Yes | Reviewer gate |
| L3 (high) | L2 + rollback path + domain expert | Yes | Domain owner |
| L4 (critical) | L3 + simulation/HIL/formal + traceability | Yes | Independent verification + formal approval |

### Example Evidence Gate (L2)

```bash
agilev validate --task AAV-0001
```

Checks:
- ✅ Task brief exists
- ✅ Risk level = L2
- ✅ Changed files documented
- ✅ Tests added or updated
- ✅ Tests passed (CI result)
- ✅ Lint/typecheck passed
- ✅ Verifier report exists
- ✅ Verifier result = pass or needs-human-review
- ❌ **FAIL:** Reviewer approval missing

Action: Add reviewer approval, then merge.

---

## Hook Details

### `enforce_task_brief.sh`

**Trigger:** `user_prompt_submit`

**Purpose:** Block implementation requests without a task ID or task brief

**Input (stdin):**
```json
{
  "event_type": "user_prompt_submit",
  "prompt": "Add retry handling to upload service"
}
```

**Logic:**
1. Parse prompt for task ID (e.g., "AAV-0001")
2. Check environment variable `AGILEV_TASK_ID`
3. Check branch name pattern (`aav-*`)
4. If no task ID found: deny
5. If task ID found, check task brief exists
6. If brief missing: deny

**Output (stdout):**
```json
{
  "decision": "deny",
  "reason": "No task ID found. Create task brief first: agilev task new --title '...' --risk L1"
}
```

### `block_unsafe_commands.sh`

**Trigger:** `pre_tool_use` (tool_name = "terminal")

**Purpose:** Block destructive or policy-forbidden terminal commands

**Input (stdin):**
```json
{
  "event_type": "pre_tool_use",
  "tool_name": "terminal",
  "tool_args": {
    "command": "rm -rf /"
  }
}
```

**Blocked patterns:**
- `rm -rf /`
- `dd if=...`
- `mkfs.*`
- `:(){ :|:& };:`
- `curl ... | sudo bash`
- `chmod 777`
- Commands from `config/policies/openhands_dangerous_commands.yaml`

**Output (stdout):**
```json
{
  "decision": "deny",
  "reason": "Command 'rm -rf /' is forbidden by policy (destructive filesystem operation)"
}
```

### `validate_scope.sh`

**Trigger:** `pre_tool_use`

**Purpose:** Warn or block when an action appears outside allowed scope

**Input (stdin):**
```json
{
  "event_type": "pre_tool_use",
  "tool_name": "edit",
  "tool_args": {
    "file_path": "src/auth/login.py",
    "old_string": "...",
    "new_string": "..."
  }
}
```

**Logic:**
1. Resolve task ID
2. Load task brief
3. Extract allowed_paths and blocked_paths
4. Check if file_path matches patterns
5. If in blocked_paths: deny
6. If not in allowed_paths: deny (or warn, depending on policy)

**Output (stdout):**
```json
{
  "decision": "deny",
  "reason": "File 'src/auth/login.py' is in blocked_paths. Task AAV-0001 only allows changes to src/upload/** and tests/upload/**"
}
```

### `log_tool_usage.sh`

**Trigger:** `post_tool_use`

**Purpose:** Append tool events to task/session log

**Input (stdin):**
```json
{
  "event_type": "post_tool_use",
  "tool_name": "terminal",
  "tool_args": {
    "command": "pytest tests/upload"
  },
  "result": {
    "exit_code": 0,
    "stdout": "===== 10 passed in 2.3s ====="
  }
}
```

**Output:** Appends to `evidence/AAV-0001/logs/openhands_tool_log.jsonl`:
```json
{"timestamp":"2026-06-08T10:15:00Z","tool":"terminal","command":"pytest tests/upload","exit_code":0,"summary":"10 passed"}
```

### `validate_evidence_on_stop.sh`

**Trigger:** `stop`

**Purpose:** Block completion until evidence and checks pass

**Logic:**
1. Resolve task ID
2. Run `agilev validate --task $TASK_ID`
3. Check evidence bundle completeness for risk level
4. If validation fails: deny

**Output (stdout):**
```json
{
  "decision": "deny",
  "reason": "Evidence bundle incomplete for risk level L2. Missing: verifier_report. Run: agilev openhands verify --task AAV-0001"
}
```

### `generate_handoff_on_session_end.sh`

**Trigger:** `session_end`

**Purpose:** Generate handoff summary

**Output:** Writes `evidence/AAV-0001/openhands_handoff.md`:
```markdown
# OpenHands Session Handoff: AAV-0001

**Session ID:** openhands-20260608-123456
**Started:** 2026-06-08T10:00:00Z
**Ended:** 2026-06-08T10:45:00Z

## Objective
Add retry handling to upload service

## Changed Files
- src/upload/retry.py (new)
- tests/upload/test_retry.py (new)
- src/upload/client.py (modified)

## Tests Run
- pytest tests/upload (10 passed)

## Open Risks
- Exponential backoff may delay uploads under heavy failure
- No integration test with real S3 backend

## Next Action
Run verifier: agilev openhands verify --task AAV-0001 --fresh-context
```

---

## Troubleshooting

### Hook Not Firing

**Symptom:** `validate_scope.sh` should block, but doesn't

**Check:**
1. Hook script is executable: `chmod +x .openhands/hooks/validate_scope.sh`
2. Hook is registered in `.openhands/hooks.json`
3. OpenHands hooks feature is enabled
4. Script has no syntax errors: `bash -n .openhands/hooks/validate_scope.sh`

**Test manually:**
```bash
echo '{"tool_name":"edit","tool_args":{"file_path":"src/auth/login.py"}}' | .openhands/hooks/validate_scope.sh
```

### Evidence Validation Fails

**Symptom:** `agilev validate --task AAV-0001` fails

**Common causes:**
- Evidence bundle schema mismatch
- Missing required fields for risk level
- Test results not recorded
- Verifier report missing (L2+)

**Fix:**
```bash
agilev openhands evidence collect --task AAV-0001
agilev validate --task AAV-0001 --verbose
```

### Scope Violation False Positive

**Symptom:** Hook blocks legitimate change

**Cause:** Overly restrictive allowed_paths pattern

**Fix:** Update task brief:
```yaml
allowed_paths:
  - src/upload/**
  - src/common/retry.py  # Add specific exception
```

Re-run validation:
```bash
agilev openhands validate --task AAV-0001 --scope
```

---

## Future Enhancements

### Planned
- [ ] `agilev openhands run --task AAV-0001 --mode builder` (direct OpenHands invocation)
- [ ] `agilev openhands verify --task AAV-0001 --fresh-context` (verifier orchestration)
- [ ] GitHub Actions workflows (auto-trigger builder/verifier on labels)
- [ ] Event ledger with hash chain (append-only audit log)
- [ ] Multi-agent backend support (Cursor, Continue, Windsurf)

### Under Consideration
- Real-time scope drift detection (file watcher)
- Automated verifier report grading
- Risk classifier agent (auto-assign L0-L4)
- Rollback path generator for L3/L4

---

## References

- [ADR-0001: OpenHands Execution Backend](../adr/ADR-0001-openhands-execution-backend.md)
- [Agile-V Methodology](../../README.md)
- [Evidence Bundle Schema](../../schemas/evidence_bundle.schema.json)
- [Task Brief Template](../../templates/task_brief.md)
- [OpenHands Documentation](https://docs.all-hands.dev)

---

## Support

For issues with the integration:
1. Run `agilev openhands doctor`
2. Check hook logs in `.openhands/logs/`
3. Validate evidence: `agilev validate --task AAV-XXXX --verbose`
4. Open issue at: https://github.com/Agile-V/agentic_agile_v/issues
