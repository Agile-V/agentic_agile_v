# OpenHands Integration Quick Start

Get started with the Agentic Agile-V OpenHands integration in under 10 minutes.

---

## Prerequisites

- Agentic Agile-V repository initialized (`agilev init`)
- Python 3.11+ installed
- Git repository

---

## Step 1: Initialize OpenHands Integration

```bash
agilev openhands init
```

This creates:
- 5 skills in `.agents/skills/`
- 7 hooks in `.openhands/hooks/`
- 5 policy files in `config/policies/`
- 1 setup script in `.openhands/setup.sh`
- 1 hook config in `.openhands/hooks.json`
- 1 integration config in `config/openhands.yaml`

**Total:** 19 files, ~4,200 lines of code

---

## Step 2: Validate Setup

```bash
agilev openhands doctor
```

Expected output:
```
✅ All 21 checks passed
✅ OpenHands integration ready
```

If any checks fail:
```bash
agilev openhands init --force  # Regenerate files
```

---

## Step 3: Create a Task

```bash
agilev new --title "Add retry handling" --risk L2
```

This creates:
- `.agentic-agile-v/tasks/AAV-0001/task_brief.md`
- `.agentic-agile-v/tasks/AAV-0001/evidence_bundle.json`
- `.agentic-agile-v/tasks/AAV-0001/plan.md`

**Edit the task brief** to add:
- Acceptance criteria
- Allowed paths: `src/upload/**`, `tests/upload/**`
- Blocked paths: `src/auth/**`, `infra/**`

---

## Step 4: Run OpenHands

### Manual (Current MVP)

1. Launch OpenHands
2. Point to your repository
3. Skills and hooks activate automatically
4. OpenHands will:
   - ✅ Load Agile-V skills
   - ✅ Enforce task brief requirement
   - ✅ Block unsafe commands
   - ✅ Log tool usage
   - ✅ Validate evidence before completion

### Future (Phase 8)

```bash
agilev openhands run --task AAV-0001 --mode builder
```

---

## Step 5: Validate Session

```bash
agilev openhands validate --task AAV-0001
```

Output:
```
🔍 Validating OpenHands session for task AAV-0001...
  ✅ OpenHands session metadata found
  ✅ OpenHands tool log found (42 events)
✅ Validation complete
```

---

## Step 6: View Handoff Report

```bash
agilev openhands handoff --task AAV-0001
```

Output:
```
# OpenHands Session Handoff: AAV-0001

**Session ID:** openhands-20260608-123456

## Changed Files
- src/upload/retry.py (new)
- tests/upload/test_retry.py (new)
- src/upload/client.py (modified)

## Next Steps
1. Review changed files
2. Run: agilev validate --task AAV-0001
3. Create pull request
```

---

## Step 7: Validate Evidence

```bash
agilev validate --task AAV-0001
```

This checks:
- ✅ Task brief exists
- ✅ Evidence bundle complete for risk level L2
- ✅ Tests added/modified
- ✅ Tests passed (from CI)
- ✅ Checks passed (lint, typecheck)
- ⏳ Verifier report (Phase 8)

---

## Step 8: Create Pull Request

```bash
git checkout -b aav-0001-retry-handling
git add .
git commit -m "AAV-0001: Add retry handling"
git push origin aav-0001-retry-handling
gh pr create --title "AAV-0001: Add retry handling"
```

PR should include:
- Link to task brief
- Risk level label (`agilev-risk-l2`)
- Evidence bundle path
- Verifier report (for L2+, Phase 8)

---

## Risk Levels Quick Reference

| Level | Name | Tests | Verifier | Approval | Example |
|-------|------|-------|----------|----------|---------|
| L0 | Trivial | Optional | No | No | README updates |
| L1 | Low | Required | No | No | Bug fixes |
| L2 | Moderate | Passing | Yes* | Reviewer | New features |
| L3 | High | Passing | Yes* | Domain owner | Auth changes |
| L4 | Critical | Passing | Yes* | Formal | Safety-critical |

\* Verifier available in Phase 8

---

## Commands Reference

| Command | Purpose |
|---------|---------|
| `agilev openhands init` | Initialize integration |
| `agilev openhands doctor` | Validate setup |
| `agilev openhands validate --task AAV-XXXX` | Validate session |
| `agilev openhands handoff --task AAV-XXXX` | View handoff report |
| `agilev openhands scaffold --force` | Regenerate files |

---

## Skills Loaded

1. **agile-v-core**: Core workflow rules (always loaded)
2. **agile-v-builder**: Implementation behavior (builder mode)
3. **agile-v-verifier**: Verification behavior (verifier mode, Phase 8)
4. **agile-v-evidence**: Evidence collection
5. **agile-v-risk-classifier**: Risk classification guidance

---

## Hooks Active

| Hook | When | Purpose |
|------|------|---------|
| `enforce_task_brief` | Before implementation | Require task ID/brief |
| `block_unsafe_commands` | Before terminal commands | Block destructive commands |
| `validate_scope` | Before file edits | Check scope (MVP: warn) |
| `log_tool_usage` | After tool use | Record events |
| `collect_session_metadata` | Session start | Record metadata |
| `validate_evidence_on_stop` | Before stop | Require passing evidence |
| `generate_handoff` | Session end | Create handoff report |

---

## Troubleshooting

### Hook not firing

```bash
# Check hook is executable
ls -la .openhands/hooks/*.sh

# Make executable if needed
chmod +x .openhands/hooks/*.sh

# Test manually
echo '{"tool_name":"terminal","tool_args":{"command":"rm -rf /"}}' | \
  .openhands/hooks/block_unsafe_commands.sh
```

### Task ID not found

```bash
# Set explicitly
export AGILEV_TASK_ID=AAV-0001

# Or use branch name
git checkout -b aav-0001-feature-name

# Or pass to command
agilev openhands validate --task AAV-0001
```

### Evidence validation fails

```bash
# Check evidence bundle
cat .agentic-agile-v/tasks/AAV-0001/evidence_bundle.json

# Validate
agilev validate --task AAV-0001

# Regenerate (Phase 6)
# agilev openhands evidence collect --task AAV-0001
```

---

## What's Next?

### Implemented (Phases 0-4)
- ✅ Skills and hooks
- ✅ CLI commands
- ✅ Task context resolution
- ✅ Policy files

### Coming Soon (Phases 5-12)
- ⏳ Evidence schema extension
- ⏳ Evidence adapter (collect from logs)
- ⏳ Scope enforcement (full implementation)
- ⏳ Builder/verifier pattern
- ⏳ GitHub Actions integration
- ⏳ Event ledger with hash chain
- ⏳ Reports and handoffs
- ⏳ Examples and tutorials

---

## Support

- Implementation Summary: `OPENHANDS_INTEGRATION_SUMMARY.md`
- Integration Guide: `docs/integrations/openhands.md`
- ADR: `docs/adr/ADR-0001-openhands-execution-backend.md`
- Issues: https://github.com/Agile-V/agentic_agile_v/issues

---

**Status:** MVP Ready (Phases 0-4 Complete)  
**Last Updated:** 2026-06-08
