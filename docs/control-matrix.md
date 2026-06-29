# Agentic Agile-V Control Matrix

The control matrix is the operating control record for all agentic task execution. It provides machine-readable policy for data class, tool use, model/vendor, log routing, max permissions, Human Gates, test requirements, cost limits, rollback plans, and owner accountability.

## File locations

| Path | Purpose |
|---|---|
| `.agile-v/CONTROL_MATRIX.yaml` | Project runtime override (highest precedence) |
| `config/control_matrix.yaml` | Repository default (shipped with this repo) |

The `config/control_matrix.yaml` ships in `draft` mode. Copy it to `.agile-v/CONTROL_MATRIX.yaml`, replace all `TBD` owner fields and `approved_vendor`/`approved_model` placeholders, then set `status: active` to enable fail-closed enforcement.

## Quick start

```bash
mkdir -p .agile-v
cp config/control_matrix.yaml .agile-v/CONTROL_MATRIX.yaml
# Edit: owners, vendor/model, data class, tool rules, cost limits, rollback
# Then: set status: active

# Validate
agilev controls validate

# Explain selected control for a task
agilev controls explain --task-type feature --risk L2 --mode builder --skill agile-v-builder

# Check a tool call
agilev controls check-tool --task AAV-0001 --tool shell_exec --json

# Check model/vendor
agilev controls check-model --task AAV-0001 --vendor my-vendor --model my-model --data-class internal

# Check cost
agilev controls check-cost --task AAV-0001 --run-cost 1.20 --daily-cost 4.50

# Check evidence bundle
agilev controls evidence --task AAV-0001 --risk L2 --check-only
```

## Schema

The JSON schema is at `schemas/control_matrix.schema.json`. Validate using `agilev controls validate`, which runs both JSON Schema and semantic checks.

## Control fields

| Field | Required | Description |
|---|---|---|
| `id` | Yes | Unique ID. Pattern: `cm-[a-z0-9-]+` |
| `status` | Yes | `draft`, `active`, `deprecated`, `disabled` |
| `minimum_risk_level` | Yes | `L0`–`L4` |
| `data_class` | Yes | Allowed, forbidden, unknown action |
| `tools` | Yes | Allowed, forbidden, requires_gate |
| `model` | Yes | vendor, model_name, allow_external_vendor |
| `logs` | Yes | storage_location, retention_days, redact |
| `max_permissions` | Yes | Per-dimension limits |
| `human_gates` | Yes | required_before, checkpoint_file, approvals_file |
| `tests` | Yes | required, required_for_l3_plus, required_for_l4 |
| `cost_limit` | Yes | max_run_cost, max_daily_cost, action_on_limit |
| `rollback` | Yes | strategy, rollback_path_required_for, feature_flag_required_for |
| `owner` | Yes | business_owner, technical_owner, security_owner, reviewer |

## Migration phases

| Phase | Behavior |
|---|---|
| 1 (current) | Matrix in `draft` mode. CI validates syntax only. No blocking hooks. |
| 2 | Enable warnings. Hooks log decisions. Deny decisions warn for low-risk. |
| 3 | Fail closed for L3+. Gated/forbidden actions block high-risk tasks. |
| 4 | Fail closed for all L2+. Evidence bundle must include control_matrix section. |
| 5 | Fail closed globally. All non-trivial work requires matrix resolution. |

## Evidence bundle

Evidence bundles for `L2+` tasks must include a `control_matrix` section. See `schemas/evidence_bundle.schema.json` for the full shape.

## OpenHands hooks

Two hooks enforce the matrix at runtime:

| Hook | Lifecycle | Purpose |
|---|---|---|
| `.openhands/hooks/enforce_control_matrix.sh` | `pre_tool_use` | Block forbidden/gated tools before execution |
| `.openhands/hooks/validate_control_evidence_on_stop.sh` | `stop` | Validate evidence bundle has control_matrix section for L2+ |

Hooks require `AGILEV_TOOL_CLASS` and `AGILEV_TASK_ID` environment variables to be set by the execution environment.

## Skills repo

The normative skill (`agile-v-control-matrix/SKILL.md`), template (`CONTROL_MATRIX.example.yaml`), and schema are published in the `Agile-V/agile_v_skills` repository. This runtime repo enforces the policy.

## Related docs

- `docs/adr/ADR-0002-control-matrix.md` — architectural decision record
- `config/control_matrix.yaml` — default matrix
- `schemas/control_matrix.schema.json` — JSON Schema
- `config/policies/control_matrix_policy.yaml` — tool classification
- `src/agilev/control_matrix.py` — loader and resolver
- `src/agilev/control_enforcer.py` — runtime checks
