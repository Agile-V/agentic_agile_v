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
# 1. Copy the default matrix and customise it
mkdir -p .agile-v
cp config/control_matrix.yaml .agile-v/CONTROL_MATRIX.yaml
# Edit: replace all TBD owner fields, vendor, model_name; set status: active when ready

# 2. Validate
agilev controls validate

# 3. Explain which control applies to a task
agilev controls explain --task-type feature --risk L2 --mode builder --skill agile-v-builder

# 4. Check specific enforcement dimensions
agilev controls check-tool       --task AAV-0001 --tool shell_exec --json
agilev controls check-data-class --task AAV-0001 --data-class confidential --json
agilev controls check-model      --task AAV-0001 --vendor my-vendor --model my-model --data-class internal
agilev controls check-cost       --task AAV-0001 --run-cost 1.20 --daily-cost 4.50 --monthly-cost 120.00
agilev controls check-rollback   --task AAV-0001 --risk L2 --rollback-path "git revert HEAD"

# 5. Check evidence bundle (stop hook equivalent)
agilev controls evidence --task AAV-0001 --risk L2 --check-only

# 6. Export evidence template for a task
agilev controls evidence --task AAV-0001 --json
```

> **Environment variables required by the OpenHands hooks:**
>
> - `AGILEV_TASK_ID` — set to the current task ID (e.g. `AAV-0001`) before running agentic sessions.
> - `AGILEV_RISK_LEVEL` — set to the task risk level (`L0`–`L4`). Required for the stop hook to enforce L2+ evidence.
> - `AGILEV_TOOL_CLASS` — set by the execution environment to the tool class being invoked (e.g. `shell_exec`).
> - `AGILEV_STRICT_MODE` — set to `1` to block all tool calls when the `agilev` CLI is not installed (default: `0`, fail-open).
>
> Example:
> ```bash
> export AGILEV_TASK_ID=AAV-0001
> export AGILEV_RISK_LEVEL=L2
> ```

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

| Phase | Behavior | How to advance |
|---|---|---|
| 1 (current) | Matrix in `draft` mode. CI validates syntax only. No blocking hooks. | Fill in all TBD fields, set `status: active`. |
| 2 | Enable warnings. Hooks log decisions. Deny decisions warn for low-risk. | Set `AGILEV_STRICT_MODE=0`, deploy hooks, verify log output for a few tasks. |
| 3 | Fail closed for L3+. Gated/forbidden actions block high-risk tasks. | Set `minimum_risk_level: L3` controls to active; verify L3 tasks are blocked on policy violations. |
| 4 | Fail closed for all L2+. Evidence bundle must include `control_matrix` section. | Require evidence bundles; set `AGILEV_RISK_LEVEL` in all sessions. |
| 5 | Fail closed globally. All non-trivial work requires matrix resolution. | Set `AGILEV_STRICT_MODE=1`; ensure all tasks export `AGILEV_TASK_ID`. |

> **Note:** The two tool-classification registries (`_TOOL_CLASS_MAP` in `src/agilev/openhands/control_hooks.py` and `config/policies/control_matrix_policy.yaml`) must be kept in sync. When adding a new tool mapping, update both files.

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

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `No control matrix found` | No YAML in `.agile-v/` or `config/` | Run `cp config/control_matrix.yaml .agile-v/CONTROL_MATRIX.yaml` |
| `unresolved owner field` | `status: active` with TBD owner | Replace all TBD values in `owner` section before activating |
| `unresolved model field` | `status: active` with TBD vendor/model | Replace `vendor` and `model_name` with real values |
| `PASS (schema validation skipped…)` | `jsonschema` not installed | `pip install jsonschema` |
| Stop hook does nothing for L2 tasks | `AGILEV_RISK_LEVEL` not set | `export AGILEV_RISK_LEVEL=L2` before starting the session |
| All tool calls pass without checking | `agilev` CLI not in PATH, `AGILEV_STRICT_MODE` not set | Install agilev or set `AGILEV_STRICT_MODE=1` to fail-closed |
| `No matching active control` | Task type or agent mode not in `applies_to` | Add `"*"` to `task_types` or `agent_modes`, or add the specific value |
| Currency pattern error | `currency` is not a 3-letter uppercase code | Use ISO 4217 codes: `EUR`, `USD`, `GBP`, etc. |

## Related docs

- `docs/adr/ADR-0002-control-matrix.md` — architectural decision record
- `config/control_matrix.yaml` — default matrix
- `schemas/control_matrix.schema.json` — JSON Schema (hardened with `additionalProperties: false`)
- `config/policies/control_matrix_policy.yaml` — tool classification (keep in sync with `control_hooks.py`)
- `src/agilev/control_matrix.py` — loader and resolver
- `src/agilev/control_enforcer.py` — runtime checks (check_data_class, check_tool, check_model, check_cost, check_rollback, check_tests, check_max_permissions)
- `src/agilev/openhands/control_hooks.py` — classify_tool, has_approval, append_control_event
