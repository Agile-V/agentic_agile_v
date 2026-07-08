# ADR-0002: Control Matrix for Agentic Task Governance

**Status:** Accepted  
**Date:** 2026-06-28  
**Author:** Agile-V Engineering

---

## Context

Agentic task execution in the `agentic_agile_v` runtime lacked a single, machine-readable governance record that tied together:

- Which data classes an agent may process
- Which tools an agent may call
- Which model/vendor is approved
- Where logs must be written
- Maximum permissions per access dimension
- Which Human Gates are required and who must approve
- Which tests are required per risk level
- Cost limits and overflow behavior
- Rollback strategy and requirements
- Owner accountability

The existing system had separate policy files (`config/policies/`), scope validation hooks, and evidence bundle schemas, but no unified control record that agents, hooks, CLI validators, and CI gates could all consult.

---

## Decision

Add a **Control Matrix** (`config/control_matrix.yaml`) as the operating control record for all agentic task execution. The matrix is:

1. **Machine-readable YAML** validated by a JSON Schema (`schemas/control_matrix.schema.json`).
2. **Enforced at runtime** via:
   - `agilev controls validate` (CLI, run locally and in CI)
   - `agilev controls check-tool` (pre-execution check)
   - `.openhands/hooks/enforce_control_matrix.sh` (pre_tool_use OpenHands hook)
   - `.openhands/hooks/validate_control_evidence_on_stop.sh` (stop hook)
   - Evidence bundle validator (evidence must include control_matrix section for L2+)
3. **Loaded with precedence**: `.agile-v/CONTROL_MATRIX.yaml` overrides `config/control_matrix.yaml`.
4. **Consumed by skills**: The `agile-v-control-matrix` skill in `Agile-V/agile_v_skills` provides normative agent instructions and the canonical template.

### Load order

```
.agile-v/CONTROL_MATRIX.yaml   ← project runtime instance (highest precedence)
config/control_matrix.yaml     ← repository default (shipped as draft)
```

### Semantic checks enforced beyond JSON Schema

- No allowed/forbidden tool overlap per control entry.
- Active controls must not have `TBD`, empty, or `null` owner fields.
- At least one control entry must exist.
- No duplicate control IDs.

### Migration phases

Fail-closed enforcement is phased to avoid disrupting current workflows:

| Phase | Trigger |
|---|---|
| 1 | Shipped. Draft matrix. CI validates syntax. No blocking. |
| 2 | Enable hook warnings. |
| 3 | Fail closed for L3+ after owners and model/vendor are resolved. |
| 4 | Fail closed for L2+. Evidence bundle requires control_matrix section. |
| 5 | Fail closed globally. |

---

## Consequences

**Positive:**
- Every agentic task can be audited against a single, versioned control record.
- Forbidden tool calls and gated actions are blockable before execution.
- CI gates enforce the matrix on every PR.
- Evidence bundles gain structured control_matrix proof for regulators.

**Negative / trade-offs:**
- The matrix must be maintained. Unresolved `TBD` values (owner, vendor, model) prevent activation.
- Hooks require `AGILEV_TOOL_CLASS`, `AGILEV_TASK_ID`, and `AGILEV_RISK_LEVEL` environment variables to be set by the execution environment. Missing vars degrade gracefully (warn and pass) — see the fail-open vs. fail-closed trade-off note below.
- `jsonschema` is an optional dependency; schema validation is skipped when not installed (CLI prints a notice).
- **Graceful degradation is fail-open by default:** when the `agilev` CLI is not installed, the pre-tool-use hook warns but does not block. This permits teams to adopt incrementally. Set `AGILEV_STRICT_MODE=1` to make the hook fail-closed. This decision is intentional and documented; see *Alternatives considered — strict-by-default enforcement* below.
- **Not yet enforced at runtime** (deferred to a follow-up iteration):
  - `tests.required_for_l3_plus` and `tests.minimum_coverage_percent` checks exist in `check_tests()` but are not wired into the pre-tool-use hook (only the stop hook via evidence check).
  - `max_permissions` is loaded and validated by `check_max_permissions()` but not automatically called from the hooks (requires calling code to pass `requested_permissions`).
  - Gate and approver roles can be configured per-action in `human_gates.required_before`; the enforcer reads this config but not all callers pass an explicit action name.

---

## Alternatives considered

1. **Extend existing POLICY.yaml**: Rejected. `POLICY.yaml` operates at the rule level (tool-class patterns). The control matrix needs task-level, skill-level, and role-level scope bindings, plus owner, model, cost, and rollback fields that go beyond what `POLICY.yaml` models.

2. **Per-task briefs only**: Rejected. Briefs are task-specific. The control matrix defines organization-wide defaults that apply across all tasks and can be overridden per project via `.agile-v/CONTROL_MATRIX.yaml`.

3. **No runtime enforcement, skills only**: Rejected. Skills instruct agents but cannot block execution. A fail-closed hook or CI gate cannot be bypassed without leaving evidence.

4. **Strict-by-default enforcement (fail-closed on missing CLI)**: Deferred. Fail-closed enforcement requires the `agilev` binary to be installed in every agent session. Many teams do not yet have this; requiring it would block adoption. The current default (fail-open, warn only) allows teams to onboard the matrix at their own pace while gradually tightening. `AGILEV_STRICT_MODE=1` is the migration path to fail-closed.

---

## Related

- `docs/control-matrix.md` — user guide
- `config/control_matrix.yaml` — default matrix
- `schemas/control_matrix.schema.json` — JSON Schema
- `src/agilev/control_matrix.py` — loader and resolver
- `src/agilev/control_enforcer.py` — runtime checks
- `agile_v_skills/agile-v-control-matrix/SKILL.md` — normative skill
- `docs/adr/ADR-0001-openhands-execution-backend.md` — OpenHands execution backend (referenced decision)
