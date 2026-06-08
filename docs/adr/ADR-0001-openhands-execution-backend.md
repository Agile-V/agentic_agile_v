# ADR-0001: OpenHands as Execution Backend

**Status:** Accepted  
**Date:** 2026-06-08  
**Decision makers:** Agentic Agile-V Core Team  

---

## Context

Agentic Agile-V provides a risk-based evidence framework for autonomous engineering changes. However, it does not provide its own code execution engine. Teams need a capable agentic execution backend that can inspect repositories, implement changes, run tests, and prepare pull requests—while remaining subordinate to Agile-V's control and verification layer.

OpenHands is an open-source autonomous coding agent that can perform complex engineering tasks. It has tool use, planning capabilities, and GitHub integration. However, it lacks built-in risk classification, evidence gates, scope control, and independent verification.

## Decision

**OpenHands is adopted as an optional execution backend for Agentic Agile-V.**

The integration follows a strict separation of responsibilities:

### Agile-V owns (control plane):
- Task briefs and risk classification
- Acceptance criteria definition
- Evidence policy and validation gates
- Approval policy (human review requirements)
- Independent verification rules
- Scope control (allowed/blocked paths)
- Final acceptance decision

### OpenHands owns (execution plane):
- Repository inspection and analysis
- Code edits and implementation
- Test execution
- Agent sessions and tool use
- Pull request creation
- Implementation summaries

### GitHub/CI owns (objective verification plane):
- Automated test execution
- Lint, type check, and build verification
- Security scanning
- Integration test results

### Human review owns (accountability plane):
- Risk-appropriate approval
- Domain expert validation for L3/L4 changes
- Release decisions
- Override authority

---

## Architecture

```text
┌─────────────────────────────────────────┐
│      Agentic Agile-V Control Plane      │
│  ┌───────────────────────────────────┐  │
│  │   Task Brief + Risk Level         │  │
│  │   Acceptance Criteria             │  │
│  │   Scope Policy (allowed/blocked)  │  │
│  │   Evidence Requirements           │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
                   │
                   ↓ hooks + skills
┌─────────────────────────────────────────┐
│       OpenHands Execution Plane         │
│  ┌───────────────────────────────────┐  │
│  │   Repository Inspection           │  │
│  │   Code Implementation             │  │
│  │   Test Execution                  │  │
│  │   PR Creation                     │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
                   │
                   ↓ generates evidence
┌─────────────────────────────────────────┐
│     Evidence Bundle + Verification      │
│  ┌───────────────────────────────────┐  │
│  │   Changed Files                   │  │
│  │   Test Results                    │  │
│  │   Tool Usage Log                  │  │
│  │   Verifier Report (L2+)           │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
                   │
                   ↓ CI + gates
┌─────────────────────────────────────────┐
│         GitHub CI + Human Review        │
│  ┌───────────────────────────────────┐  │
│  │   Automated Tests                 │  │
│  │   Evidence Validation             │  │
│  │   Human Approval (L2+)            │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

---

## Integration Mechanisms

### 1. Skills (`.agents/skills/`)
Repository-level instructions that teach OpenHands about Agile-V rules:
- `agile-v-core`: Core workflow rules (task brief first, evidence controls acceptance)
- `agile-v-builder`: Implementation behavior (minimal scope, add tests)
- `agile-v-verifier`: Independent review behavior (fresh context, challenge assumptions)
- `agile-v-evidence`: Evidence collection behavior
- `agile-v-risk-classifier`: Risk level guidance (L0-L4)

### 2. Hooks (`.openhands/hooks/`)
Mechanical enforcement during OpenHands execution:
- `enforce_task_brief.sh`: Block implementation without task brief
- `block_unsafe_commands.sh`: Block destructive terminal commands
- `validate_scope.sh`: Warn/block out-of-scope changes
- `log_tool_usage.sh`: Record all tool events
- `validate_evidence_on_stop.sh`: Block completion until evidence passes
- `generate_handoff_on_session_end.sh`: Generate handoff summary

### 3. CLI Integration (`agilev openhands ...`)
First-class command group:
- `agilev openhands init` - Generate OpenHands integration files
- `agilev openhands doctor` - Validate integration setup
- `agilev openhands scaffold` - Create skills and hooks
- `agilev openhands evidence collect` - Adapt OpenHands logs to evidence bundle
- `agilev openhands validate` - Validate scope and evidence
- `agilev openhands handoff` - Generate handoff report

### 4. Evidence Extension
Evidence bundle schema extended with OpenHands metadata:
```json
{
  "agent_execution": {
    "engine": "openhands",
    "mode": "builder|verifier",
    "session_id": "...",
    "tool_log_path": "...",
    "handoff_path": "..."
  },
  "scope_control": {
    "allowed_paths": [...],
    "blocked_paths": [...],
    "changed_files_within_scope": true,
    "out_of_scope_changes": [...]
  }
}
```

---

## Non-Goals

**What this integration explicitly does NOT do:**

1. **OpenHands must not self-approve high-risk changes**
   - L3/L4 changes always require human approval
   - Evidence gates cannot be bypassed by agent success claims

2. **OpenHands must not bypass task briefs**
   - Implementation from raw chat history is blocked
   - Hook enforces task brief existence before code edits

3. **OpenHands must not weaken Agile-V evidence gates**
   - Removing tests to pass builds is forbidden
   - Evidence requirements are policy-driven, not agent-negotiable

4. **OpenHands must not have final authority**
   - Agile-V validates evidence, not OpenHands
   - Independent verifier (separate session) required for L2+

5. **OpenHands must not silently expand scope**
   - Scope validation hook checks changed files against allowed paths
   - Out-of-scope changes block completion

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Agent bypasses task brief | `enforce_task_brief.sh` hook blocks implementation without task ID |
| Agent removes tests | Skill forbids test removal; evidence bundle tracks test count delta |
| Agent expands scope | `validate_scope.sh` compares changed files to allowed_paths |
| Agent self-approves L3/L4 | Policy enforces human approval; CI blocks merge without it |
| Agent fabricates evidence | Evidence adapter uses Git/CI truth, not agent claims |
| Agent weakens security | Skill explicitly forbids weakening auth/crypto/validation |
| Hook or skill ignored | Stop hook blocks completion; required evidence missing fails CI gate |

---

## Consequences

### Positive
- Teams get autonomous execution without losing engineering control
- Evidence and verification remain independent of implementation agent
- Scope drift and high-risk changes are mechanically blocked
- Integration is additive—works alongside existing manual workflows
- Human oversight remains authoritative for critical changes

### Negative
- Additional setup complexity (skills, hooks, policies)
- Hook validation adds latency to OpenHands operations
- Requires discipline to maintain hook/skill alignment with policy
- Learning curve for teams adopting both Agile-V and OpenHands

### Neutral
- Evidence bundle size increases (includes session logs, tool events)
- Verification pattern (builder + verifier) requires two agent sessions for L2+
- OpenHands becomes preferred but not required execution backend

---

## Alternatives Considered

### 1. Tight coupling (OpenHands as built-in authority)
**Rejected:** Would make OpenHands the source of truth for acceptance, violating independent verification principle.

### 2. No integration (manual only)
**Rejected:** Leaves substantial value on the table; teams want autonomous execution with safety.

### 3. Custom agent runtime
**Rejected:** Building from scratch duplicates existing capability and delays value delivery.

### 4. Multiple agent backends
**Deferred:** Could support Cursor, Continue, Windsurf, etc. in future. OpenHands first as reference implementation.

---

## References

- [Agile-V README](../../README.md) - Core methodology
- [OpenHands Integration Guide](../integrations/openhands.md) - Implementation details
- [Evidence Bundle Schema](../../schemas/evidence_bundle.schema.json)
- [Task Brief Template](../../templates/task_brief.md)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-06-08 | Agentic Agile-V Core Team | Initial decision |
