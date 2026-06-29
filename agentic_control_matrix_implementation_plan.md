# Agentic Repo Implementation Plan: Kontrollmatrix / Control Matrix

Repo: `Agile-V/agentic_agile_v`

Purpose: add an enforceable control matrix to the Agentic Agile-V runtime so every agentic task, skill invocation, model call, tool call, log write, approval gate, cost boundary, rollback path, and owner assignment is machine-checkable.

Important dependency: this repo uses the Agile-V skills. The skills repo should define the normative skill guidance and templates. This agentic repo should enforce the policy at runtime through schemas, CLI validators, OpenHands hooks, evidence bundles, and CI gates.

---

## 1. Existing repo facts to preserve

The current agentic repo already contains these concepts and should not be bypassed:

- `AGENTS.md` is the repository-level instruction file for AI coding agents.
- The workflow requires a structured task brief before implementation.
- Risk levels are already defined from `L0` to `L4`.
- `L3` and `L4` require stronger approval and evidence.
- OpenHands integration exists as an execution backend.
- OpenHands uses skills, hooks, policies, tool logging, and evidence validation.
- The Python package is named `agilev` and exposes the `agilev` CLI.
- Evidence bundles are already schema-driven.
- Existing policy files live under `config/policies/`.
- Existing OpenHands logs live under `.openhands/logs/`.

Do not replace this system. Extend it.

---

## 2. Ten implementation refinement iterations

These are the ten review iterations used to converge on the final design.

| Iteration | Question | Decision |
|---|---|---|
| 1 | Should the matrix be documentation or enforcement? | It must be both: YAML spec plus runtime enforcement. |
| 2 | Where is the source of truth? | Runtime instance uses `.agile-v/CONTROL_MATRIX.yaml`; repo default lives in `config/control_matrix.yaml`. |
| 3 | How does this relate to skills? | Skills define the rules and templates; agentic runtime enforces them. |
| 4 | How should it align with existing risk levels? | Each control entry includes `minimum_risk_level`, and gate logic maps to `L0` to `L4`. |
| 5 | How should tool calls be controlled? | Tool calls are checked against allowed and forbidden tool classes before execution. |
| 6 | How should model/vendor use be controlled? | Model calls are allowed only when vendor, model, residency, and data-class constraints match. |
| 7 | How should logs be handled? | Logs are required, typed, retention-bound, and redacted according to the entry. |
| 8 | How should Human Gates work? | Human Gates are durable approvals with role, artifact, expiry, resume token, and evidence reference. |
| 9 | How should rollback and cost limits work? | Every entry has a rollback method, owner, maximum rollback time, run limit, and daily limit. |
| 10 | How should testing prove it works? | Use schema tests, policy unit tests, CLI tests, hook tests, evidence-bundle tests, and CI tests. |

---

## 3. Target architecture

The control matrix becomes a new governance layer between task context, skill routing, agent execution, tool use, logging, evidence validation, and approval.

```text
User intent
  |
  v
Task brief + risk classification
  |
  v
Skill guidance from Agile-V skills
  |
  v
CONTROL_MATRIX.yaml lookup
  |
  +-- data class check
  +-- tool allowlist / denylist check
  +-- model / vendor check
  +-- max permission check
  +-- human gate check
  +-- cost limit check
  +-- log routing check
  +-- rollback owner check
  |
  v
OpenHands / agent execution
  |
  v
Evidence bundle + trace log + reviewer gate
  |
  v
Merge only after required gates pass
```

---

## 4. Files to add or modify

```text
agentic_agile_v/
├── config/
│   ├── control_matrix.yaml                         # default runtime policy
│   └── policies/
│       ├── control_matrix_policy.yaml              # mapping into existing risk/evidence policies
│       └── approval_policy.yaml                    # extend with control matrix gates
├── schemas/
│   ├── control_matrix.schema.json                  # validates config/control_matrix.yaml
│   └── evidence_bundle.schema.json                 # extend with control_matrix section
├── src/agilev/
│   ├── control_matrix.py                           # dataclasses, loader, validator
│   ├── control_enforcer.py                         # runtime checks
│   ├── cli.py                                      # add `agilev controls ...`
│   └── openhands/
│       ├── control_hooks.py                        # helper for shell hooks
│       └── scaffold.py                             # scaffold CONTROL_MATRIX + hook registration
├── .openhands/
│   ├── hooks.json                                  # register control hooks
│   └── hooks/
│       ├── enforce_control_matrix.sh               # pre_tool_use / user_prompt_submit
│       └── validate_control_evidence_on_stop.sh    # stop hook
├── tests/
│   ├── test_control_matrix_schema.py
│   ├── test_control_matrix_loader.py
│   ├── test_control_enforcer.py
│   ├── test_control_cli.py
│   ├── test_openhands_control_hooks.py
│   └── fixtures/
│       ├── control_matrix.valid.yaml
│       ├── control_matrix.invalid_missing_owner.yaml
│       ├── control_matrix.invalid_forbidden_tool.yaml
│       └── evidence_bundle.with_controls.json
└── docs/
    ├── control-matrix.md
    └── adr/
        └── ADR-0002-control-matrix.md
```

---

## 5. Control matrix data contract

Each matrix entry controls one agent, skill, task type, or execution mode. Start with task/agent-level entries. Add skill-level entries later.

Required columns from the user request:

- `data_class`
- `allowed_tools`
- `model_vendor`
- `model_name`
- `log_storage`
- `max_permissions`
- `human_gates`
- `tests`
- `cost_limit`
- `rollback`
- `owner`

Add these derived fields for implementation safety:

- `id`
- `scope`
- `applies_to`
- `minimum_risk_level`
- `forbidden_tools`
- `model_constraints`
- `evidence_requirements`
- `retention_days`
- `status`
- `review_cycle_days`
- `last_reviewed`

---

## 6. Default YAML to add

File: `config/control_matrix.yaml`

```yaml
version: "1.0.0"
effective_from: "2026-06-28T00:00:00Z"
default_fail_mode: "closed"
default_log_storage: ".agile-v/logs/control-events.jsonl"
default_retention_days: 90

controls:
  - id: "cm-default-agentic-task"
    status: "active"
    description: "Default policy for Agentic Agile-V task execution."
    scope: "task"
    applies_to:
      task_types: ["feature", "bug", "hardware", "firmware", "test", "refactor", "docs", "security", "other"]
      agent_modes: ["builder", "verifier", "risk_classifier", "manual"]
      skills: ["*"]
    minimum_risk_level: "L1"

    data_class:
      allowed: ["public", "internal", "confidential"]
      forbidden: ["secret", "regulated_health", "payment_card", "production_secret"]
      default_if_unknown: "confidential"
      unknown_action: "require_human_gate"
      redaction_required: true

    tools:
      allowed:
        - "read_file"
        - "write_file"
        - "list_files"
        - "run_tests"
        - "git_diff"
        - "git_status"
        - "static_analysis"
        - "schema_validation"
      forbidden:
        - "deploy_production"
        - "send_email_external"
        - "delete_data"
        - "rotate_secrets"
        - "change_iam"
        - "manufacture_hardware"
      requires_gate:
        - "shell_exec"
        - "network_egress"
        - "dependency_install"
        - "database_migration"
        - "public_api_change"

    model:
      vendor: "approved_vendor"
      model_name: "approved_model"
      fallback_model: null
      allow_external_vendor: false
      require_vendor_review_for_data_classes: ["confidential", "secret", "regulated_health"]
      record_model_in_evidence: true

    logs:
      storage_location: ".agile-v/logs/control-events.jsonl"
      tool_log_location: ".openhands/logs/tool-usage.jsonl"
      include_prompt: false
      include_response: false
      include_tool_calls: true
      include_decision_rationale: true
      redact_personal_data: true
      retention_days: 90

    max_permissions:
      file_access: "repo_scoped"
      write_access: "task_allowed_paths_only"
      network_access: "blocked_unless_approved"
      database_access: "none"
      email_access: "none"
      credential_access: "none"
      code_execution: "tests_and_local_tools_only"
      git_access: "diff_status_only"

    human_gates:
      required_before:
        - action: "external_effect"
          gate: "G2"
          approver_role: "domain_owner"
        - action: "production_change"
          gate: "G2"
          approver_role: "technical_owner"
        - action: "l3_or_higher"
          gate: "G2"
          approver_role: "domain_owner"
        - action: "forbidden_data_class_exception"
          gate: "G1"
          approver_role: "security_owner"
        - action: "cost_limit_exception"
          gate: "G2"
          approver_role: "business_owner"
      checkpoint_file: ".agile-v/CHECKPOINTS.md"
      approvals_file: ".agile-v/APPROVALS.md"
      require_resume_token: true

    tests:
      required:
        - "schema_validation"
        - "unit_tests"
        - "risk_policy_test"
        - "evidence_bundle_validation"
        - "control_matrix_validation"
      required_for_l3_plus:
        - "security_privacy_check"
        - "rollback_test"
        - "independent_verifier_report"
      required_for_l4:
        - "simulation_or_hil_evidence"
        - "traceability_matrix"
        - "formal_approval"
      minimum_coverage_percent: 80

    cost_limit:
      currency: "EUR"
      max_run_cost: 2.00
      max_daily_cost: 25.00
      max_monthly_cost: 500.00
      action_on_limit: "stop_and_request_approval"
      cost_log: ".agile-v/logs/costs.jsonl"

    rollback:
      required: true
      strategy: "revert_commit_or_disable_feature_flag"
      rollback_path_required_for: ["L2", "L3", "L4"]
      feature_flag_required_for: ["L3", "L4"]
      max_rollback_time_minutes: 30
      rollback_owner_role: "technical_owner"

    owner:
      business_owner: "TBD"
      technical_owner: "TBD"
      security_owner: "TBD"
      reviewer: "TBD"
      backup_owner: "TBD"

    review:
      last_reviewed: "2026-06-28"
      review_cycle_days: 90
      reviewer_role: "security_owner"
```

For production, replace every `TBD`, `approved_vendor`, and `approved_model` before enabling fail-closed enforcement in CI.

---

## 7. JSON schema

File: `schemas/control_matrix.schema.json`

Key constraints:

- `version`, `default_fail_mode`, and `controls` are required.
- Every control entry must have owners.
- Every control entry must define data classes, tools, model, logs, permissions, gates, tests, cost limit, rollback.
- Unknown data class behavior must be explicit.
- Forbidden tools and allowed tools may not overlap.
- Human gates must identify an approver role.

Skeleton:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Agile-V Control Matrix",
  "type": "object",
  "required": ["version", "default_fail_mode", "controls"],
  "properties": {
    "version": {"type": "string"},
    "effective_from": {"type": "string"},
    "default_fail_mode": {"type": "string", "enum": ["closed", "open"]},
    "default_log_storage": {"type": "string"},
    "default_retention_days": {"type": "integer", "minimum": 1},
    "controls": {
      "type": "array",
      "minItems": 1,
      "items": {"$ref": "#/$defs/control"}
    }
  },
  "$defs": {
    "control": {
      "type": "object",
      "required": [
        "id", "status", "scope", "applies_to", "minimum_risk_level",
        "data_class", "tools", "model", "logs", "max_permissions",
        "human_gates", "tests", "cost_limit", "rollback", "owner", "review"
      ],
      "properties": {
        "id": {"type": "string", "pattern": "^cm-[a-z0-9][a-z0-9-]*$"},
        "status": {"type": "string", "enum": ["draft", "active", "deprecated", "disabled"]},
        "description": {"type": "string"},
        "scope": {"type": "string", "enum": ["global", "task", "agent", "skill", "tool", "repo"]},
        "minimum_risk_level": {"type": "string", "enum": ["L0", "L1", "L2", "L3", "L4"]},
        "applies_to": {"type": "object"},
        "data_class": {"$ref": "#/$defs/dataClass"},
        "tools": {"$ref": "#/$defs/tools"},
        "model": {"$ref": "#/$defs/model"},
        "logs": {"$ref": "#/$defs/logs"},
        "max_permissions": {"type": "object"},
        "human_gates": {"$ref": "#/$defs/humanGates"},
        "tests": {"type": "object"},
        "cost_limit": {"$ref": "#/$defs/costLimit"},
        "rollback": {"type": "object"},
        "owner": {"$ref": "#/$defs/owner"},
        "review": {"type": "object"}
      }
    },
    "dataClass": {
      "type": "object",
      "required": ["allowed", "forbidden", "default_if_unknown", "unknown_action", "redaction_required"],
      "properties": {
        "allowed": {"type": "array", "items": {"type": "string"}},
        "forbidden": {"type": "array", "items": {"type": "string"}},
        "default_if_unknown": {"type": "string"},
        "unknown_action": {"type": "string", "enum": ["deny", "allow", "require_human_gate"]},
        "redaction_required": {"type": "boolean"}
      }
    },
    "tools": {
      "type": "object",
      "required": ["allowed", "forbidden", "requires_gate"],
      "properties": {
        "allowed": {"type": "array", "items": {"type": "string"}},
        "forbidden": {"type": "array", "items": {"type": "string"}},
        "requires_gate": {"type": "array", "items": {"type": "string"}}
      }
    },
    "model": {
      "type": "object",
      "required": ["vendor", "model_name", "allow_external_vendor", "record_model_in_evidence"],
      "properties": {
        "vendor": {"type": "string"},
        "model_name": {"type": "string"},
        "fallback_model": {"type": ["string", "null"]},
        "allow_external_vendor": {"type": "boolean"},
        "require_vendor_review_for_data_classes": {"type": "array", "items": {"type": "string"}},
        "record_model_in_evidence": {"type": "boolean"}
      }
    },
    "logs": {
      "type": "object",
      "required": ["storage_location", "include_tool_calls", "redact_personal_data", "retention_days"],
      "properties": {
        "storage_location": {"type": "string"},
        "tool_log_location": {"type": "string"},
        "include_prompt": {"type": "boolean"},
        "include_response": {"type": "boolean"},
        "include_tool_calls": {"type": "boolean"},
        "include_decision_rationale": {"type": "boolean"},
        "redact_personal_data": {"type": "boolean"},
        "retention_days": {"type": "integer", "minimum": 1}
      }
    },
    "humanGates": {
      "type": "object",
      "required": ["required_before", "checkpoint_file", "approvals_file", "require_resume_token"],
      "properties": {
        "required_before": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["action", "gate", "approver_role"],
            "properties": {
              "action": {"type": "string"},
              "gate": {"type": "string"},
              "approver_role": {"type": "string"}
            }
          }
        },
        "checkpoint_file": {"type": "string"},
        "approvals_file": {"type": "string"},
        "require_resume_token": {"type": "boolean"}
      }
    },
    "costLimit": {
      "type": "object",
      "required": ["currency", "max_run_cost", "max_daily_cost", "action_on_limit", "cost_log"],
      "properties": {
        "currency": {"type": "string"},
        "max_run_cost": {"type": "number", "minimum": 0},
        "max_daily_cost": {"type": "number", "minimum": 0},
        "max_monthly_cost": {"type": "number", "minimum": 0},
        "action_on_limit": {"type": "string", "enum": ["stop", "warn", "stop_and_request_approval"]},
        "cost_log": {"type": "string"}
      }
    },
    "owner": {
      "type": "object",
      "required": ["business_owner", "technical_owner", "security_owner", "reviewer"],
      "properties": {
        "business_owner": {"type": "string", "minLength": 1},
        "technical_owner": {"type": "string", "minLength": 1},
        "security_owner": {"type": "string", "minLength": 1},
        "reviewer": {"type": "string", "minLength": 1},
        "backup_owner": {"type": "string"}
      }
    }
  }
}
```

Add semantic validation in Python for overlaps and owner placeholders because JSON Schema alone is not enough.

---

## 8. Python module design

File: `src/agilev/control_matrix.py`

Responsibilities:

- Load matrix from `.agile-v/CONTROL_MATRIX.yaml` if present.
- Fall back to `config/control_matrix.yaml`.
- Validate schema.
- Run semantic checks.
- Resolve the applicable control entry for a task, agent mode, skill, or tool.
- Return a structured decision object.

Core API:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml

RiskLevel = Literal["L0", "L1", "L2", "L3", "L4"]
Decision = Literal["allow", "deny", "require_human_gate", "warn"]

RISK_ORDER = {"L0": 0, "L1": 1, "L2": 2, "L3": 3, "L4": 4}


@dataclass(frozen=True)
class ControlDecision:
    decision: Decision
    control_id: str
    reason: str
    required_gate: str | None = None
    approver_role: str | None = None
    evidence_ref: str | None = None


class ControlMatrixError(RuntimeError):
    pass


class ControlMatrix:
    def __init__(self, data: dict[str, Any], source_path: Path) -> None:
        self.data = data
        self.source_path = source_path

    @classmethod
    def load(cls, root: Path) -> "ControlMatrix":
        candidates = [
            root / ".agile-v" / "CONTROL_MATRIX.yaml",
            root / "config" / "control_matrix.yaml",
        ]
        for path in candidates:
            if path.exists():
                with path.open("r", encoding="utf-8") as handle:
                    data = yaml.safe_load(handle) or {}
                matrix = cls(data=data, source_path=path)
                matrix.validate_semantics()
                return matrix
        raise ControlMatrixError("No control matrix found")

    def validate_semantics(self) -> None:
        controls = self.data.get("controls", [])
        if not controls:
            raise ControlMatrixError("control matrix has no controls")
        ids = set()
        for control in controls:
            cid = control["id"]
            if cid in ids:
                raise ControlMatrixError(f"duplicate control id: {cid}")
            ids.add(cid)
            allowed = set(control["tools"].get("allowed", []))
            forbidden = set(control["tools"].get("forbidden", []))
            overlap = allowed & forbidden
            if overlap:
                raise ControlMatrixError(f"control {cid} has overlapping tools: {sorted(overlap)}")
            owner = control["owner"]
            for key in ["business_owner", "technical_owner", "security_owner", "reviewer"]:
                if owner.get(key) in (None, "", "TBD"):
                    raise ControlMatrixError(f"control {cid} has unresolved owner: {key}")

    def resolve(self, task_type: str, risk_level: RiskLevel, agent_mode: str, skill: str | None) -> dict[str, Any]:
        active = [c for c in self.data["controls"] if c.get("status") == "active"]
        for control in active:
            applies = control.get("applies_to", {})
            task_ok = "*" in applies.get("task_types", []) or task_type in applies.get("task_types", [])
            mode_ok = "*" in applies.get("agent_modes", []) or agent_mode in applies.get("agent_modes", [])
            skill_ok = skill is None or "*" in applies.get("skills", []) or skill in applies.get("skills", [])
            min_ok = RISK_ORDER[risk_level] >= RISK_ORDER[control["minimum_risk_level"]]
            if task_ok and mode_ok and skill_ok and min_ok:
                return control
        raise ControlMatrixError(f"No matching control for task_type={task_type}, risk={risk_level}, mode={agent_mode}, skill={skill}")
```

---

## 9. Enforcement module

File: `src/agilev/control_enforcer.py`

Core checks:

```python
from __future__ import annotations

from typing import Any

from agilev.control_matrix import ControlDecision


def check_data_class(control: dict[str, Any], data_class: str) -> ControlDecision:
    cfg = control["data_class"]
    if data_class in cfg["forbidden"]:
        return ControlDecision("deny", control["id"], f"Forbidden data class: {data_class}")
    if data_class not in cfg["allowed"]:
        action = cfg["unknown_action"]
        if action == "require_human_gate":
            return ControlDecision("require_human_gate", control["id"], f"Unknown data class: {data_class}", required_gate="G1", approver_role="security_owner")
        if action == "deny":
            return ControlDecision("deny", control["id"], f"Unknown data class denied: {data_class}")
    return ControlDecision("allow", control["id"], "Data class allowed")


def check_tool(control: dict[str, Any], tool_class: str) -> ControlDecision:
    tools = control["tools"]
    if tool_class in tools.get("forbidden", []):
        return ControlDecision("deny", control["id"], f"Forbidden tool: {tool_class}")
    if tool_class in tools.get("requires_gate", []):
        return ControlDecision("require_human_gate", control["id"], f"Tool requires gate: {tool_class}", required_gate="G2", approver_role="technical_owner")
    if tool_class not in tools.get("allowed", []):
        return ControlDecision("deny", control["id"], f"Tool not allowlisted: {tool_class}")
    return ControlDecision("allow", control["id"], "Tool allowed")


def check_model(control: dict[str, Any], vendor: str, model_name: str, data_class: str) -> ControlDecision:
    model = control["model"]
    if vendor != model["vendor"] and not model["allow_external_vendor"]:
        return ControlDecision("deny", control["id"], f"Vendor not allowed: {vendor}")
    if model_name != model["model_name"] and model.get("fallback_model") != model_name:
        return ControlDecision("deny", control["id"], f"Model not allowed: {model_name}")
    if data_class in model.get("require_vendor_review_for_data_classes", []):
        return ControlDecision("require_human_gate", control["id"], f"Vendor review required for data class: {data_class}", required_gate="G1", approver_role="security_owner")
    return ControlDecision("allow", control["id"], "Model allowed")


def check_cost(control: dict[str, Any], run_cost: float, daily_cost: float) -> ControlDecision:
    cost = control["cost_limit"]
    if run_cost > cost["max_run_cost"]:
        return ControlDecision("require_human_gate", control["id"], "Run cost limit exceeded", required_gate="G2", approver_role="business_owner")
    if daily_cost > cost["max_daily_cost"]:
        return ControlDecision("require_human_gate", control["id"], "Daily cost limit exceeded", required_gate="G2", approver_role="business_owner")
    return ControlDecision("allow", control["id"], "Cost allowed")
```

---

## 10. CLI commands

Extend `src/agilev/cli.py`.

Commands:

```bash
agilev controls validate
agilev controls explain --task-type feature --risk L2 --mode builder --skill agile-v-builder
agilev controls check-tool --task AAV-0001 --tool shell_exec
agilev controls check-model --task AAV-0001 --vendor approved_vendor --model approved_model --data-class internal
agilev controls check-cost --task AAV-0001 --run-cost 1.20 --daily-cost 4.50
agilev controls evidence --task AAV-0001
```

Expected behavior:

- `validate`: validates schema and semantics.
- `explain`: prints selected control entry and why it matches.
- `check-tool`: returns non-zero if deny or gate required without approval.
- `check-model`: returns non-zero if vendor/model/data-class mismatch.
- `check-cost`: returns non-zero if limits exceeded.
- `evidence`: writes or updates control evidence in the evidence bundle.

Output format should support both human-readable and JSON:

```bash
agilev controls check-tool --tool shell_exec --json
```

Example JSON response:

```json
{
  "decision": "require_human_gate",
  "control_id": "cm-default-agentic-task",
  "reason": "Tool requires gate: shell_exec",
  "required_gate": "G2",
  "approver_role": "technical_owner"
}
```

---

## 11. OpenHands hook integration

Add hook files:

```text
.openhands/hooks/enforce_control_matrix.sh
.openhands/hooks/validate_control_evidence_on_stop.sh
```

Register in `.openhands/hooks.json`:

```json
{
  "hooks": [
    {
      "name": "enforce_control_matrix",
      "lifecycle": "pre_tool_use",
      "path": ".openhands/hooks/enforce_control_matrix.sh",
      "blocking": true,
      "timeout_seconds": 10
    },
    {
      "name": "validate_control_evidence_on_stop",
      "lifecycle": "stop",
      "path": ".openhands/hooks/validate_control_evidence_on_stop.sh",
      "blocking": true,
      "timeout_seconds": 20
    }
  ]
}
```

Hook behavior:

- Identify current task through existing `TaskContextResolver`.
- Resolve task type, risk, mode, skill if available.
- Classify requested tool into a matrix tool class.
- Call `agilev controls check-tool`.
- Append decision to `.agile-v/logs/control-events.jsonl`.
- Deny with exit code 2 when decision is `deny`.
- Deny with exit code 2 when decision is `require_human_gate` and no approval exists.

Example hook body:

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

TOOL_CLASS="${AGILEV_TOOL_CLASS:-unknown}"
TASK_ID="${AGILEV_TASK_ID:-}"

if [ -z "$TASK_ID" ]; then
  echo '{"decision":"deny","reason":"AGILEV_TASK_ID missing"}'
  exit 2
fi

agilev controls check-tool --task "$TASK_ID" --tool "$TOOL_CLASS" --json
```

Keep shell hooks thin. The Python CLI must own policy logic.

---

## 12. Tool classification

Create a deterministic mapping from concrete tool names to matrix tool classes.

File: `config/policies/control_matrix_policy.yaml`

```yaml
version: "1.0.0"
tool_classification:
  shell:
    class: "shell_exec"
    patterns: ["bash", "sh", "terminal", "exec", "run"]
  filesystem_read:
    class: "read_file"
    patterns: ["read", "cat", "list", "find", "grep"]
  filesystem_write:
    class: "write_file"
    patterns: ["write", "edit", "patch", "create_file"]
  git:
    class: "git_diff"
    patterns: ["git diff", "git status", "git show"]
  network:
    class: "network_egress"
    patterns: ["curl", "wget", "fetch", "http"]
  dependency:
    class: "dependency_install"
    patterns: ["pip install", "npm install", "pnpm add", "cargo add"]
  database:
    class: "database_migration"
    patterns: ["alembic", "prisma migrate", "knex migrate"]
```

Enforcement should fail closed for unknown tool classes unless the control entry explicitly allows `unknown`.

---

## 13. Evidence bundle extension

Extend `schemas/evidence_bundle.schema.json` with a `control_matrix` object.

```json
"control_matrix": {
  "type": "object",
  "required": ["control_id", "matrix_path", "policy_version", "decisions", "owner", "rollback", "cost"],
  "properties": {
    "control_id": {"type": "string"},
    "matrix_path": {"type": "string"},
    "policy_version": {"type": "string"},
    "decisions": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["timestamp", "check", "decision", "reason"],
        "properties": {
          "timestamp": {"type": "string"},
          "check": {"type": "string"},
          "decision": {"type": "string", "enum": ["allow", "deny", "require_human_gate", "warn"]},
          "reason": {"type": "string"},
          "approval_ref": {"type": "string"}
        }
      }
    },
    "owner": {"type": "object"},
    "rollback": {"type": "object"},
    "cost": {"type": "object"},
    "log_refs": {"type": "array", "items": {"type": "string"}}
  }
}
```

Validation rule:

- For `L0` and `L1`, warn if missing initially, then require after migration date.
- For `L2+`, require `control_matrix` immediately.
- For `L3+`, require at least one approval reference when gates are triggered.

---

## 14. Human Gate integration

Map matrix gates to existing gate system:

| Matrix trigger | Existing gate | Required artifact |
|---|---|---|
| requirements approval | G1 | task brief, requirement IDs, approval row |
| high-risk tool call | G2 or custom gate | checkpoint row, approval row |
| production effect | G2 | evidence bundle, rollback path, approver |
| L3/L4 task | G2 | domain/security approval, verifier report |
| cost exception | G2 | cost log, business owner approval |
| data-class exception | G1 | data classification note, security owner approval |

Add durable checkpoint rows to `.agile-v/CHECKPOINTS.md` before blocking.

Format:

```text
INT-0007|C1|CONTROL_MATRIX_TOOL_GATE|PENDING|2026-06-28T10:00:00Z|2026-06-29T10:00:00Z|technical_owner|rt-abc123|config/control_matrix.yaml|none|-|-
```

Approval row in `.agile-v/APPROVALS.md`:

```text
GATE-0042|2026-06-28T10:15:00Z|technical_owner|approved|rt-abc123|shell_exec approved for AAV-0001 test execution|INT-0007
```

---

## 15. Cost enforcement

Initial implementation can be conservative:

- Read estimated costs from task metadata or environment.
- Allow manual `--run-cost` and `--daily-cost` checks.
- Append cost entries to `.agile-v/logs/costs.jsonl`.
- If no cost can be determined, use unknown cost behavior:
  - `L0-L1`: warn.
  - `L2`: warn unless configured fail-closed.
  - `L3-L4`: require gate.

Future improvement:

- Adapter for model provider usage metadata.
- Token counting per model call.
- CI summary for cost per task.

Cost log line:

```json
{"timestamp":"2026-06-28T12:00:00Z","task_id":"AAV-0001","control_id":"cm-default-agentic-task","vendor":"approved_vendor","model":"approved_model","run_cost":0.42,"daily_cost":3.80,"currency":"EUR"}
```

---

## 16. Rollback enforcement

For every `L2+` task, the evidence bundle must contain a non-empty `rollback_path`.

For every `L3+` task, require either:

- a feature flag, or
- a reversible migration plan, or
- a documented revert commit strategy, or
- a manual operational fallback.

Add validator:

```python
def validate_rollback(control: dict, risk_level: str, evidence: dict) -> ControlDecision:
    required_levels = set(control["rollback"].get("rollback_path_required_for", []))
    if risk_level in required_levels and not evidence.get("rollback_path"):
        return ControlDecision("deny", control["id"], "rollback_path missing")
    if risk_level in control["rollback"].get("feature_flag_required_for", []) and "feature_flag" not in evidence.get("rollback_path", ""):
        return ControlDecision("require_human_gate", control["id"], "feature flag or equivalent rollback not documented", required_gate="G2", approver_role="technical_owner")
    return ControlDecision("allow", control["id"], "Rollback evidence acceptable")
```

---

## 17. Owner enforcement

Owner fields must not be placeholders once the matrix is active.

Minimum owner set:

```yaml
owner:
  business_owner: "Name or team"
  technical_owner: "Name or team"
  security_owner: "Name or team"
  reviewer: "Name or team"
  backup_owner: "Name or team"
```

Semantic validator must fail if any required owner equals:

- `TBD`
- `unknown`
- empty string
- missing value

CI should block `main` when active controls have unresolved owners.

---

## 18. Test plan

### 18.1 Unit tests

File: `tests/test_control_matrix_loader.py`

Tests:

- loads `.agile-v/CONTROL_MATRIX.yaml` over `config/control_matrix.yaml`
- fails when no matrix exists
- fails on duplicate IDs
- fails when owner is `TBD`
- fails when allowed and forbidden tools overlap
- resolves default task policy
- resolves skill-specific policy when present

### 18.2 Enforcer tests

File: `tests/test_control_enforcer.py`

Tests:

- allowed data class returns `allow`
- forbidden data class returns `deny`
- unknown data class returns `require_human_gate`
- allowed tool returns `allow`
- forbidden tool returns `deny`
- gated tool returns `require_human_gate`
- unlisted tool returns `deny`
- unauthorized vendor returns `deny`
- unauthorized model returns `deny`
- run cost over limit requires gate
- daily cost over limit requires gate

### 18.3 CLI tests

File: `tests/test_control_cli.py`

Use `pytest` with `tmp_path` and monkeypatch current working directory.

Commands to test:

```bash
agilev controls validate
agilev controls explain --task-type feature --risk L2 --mode builder --skill agile-v-builder
agilev controls check-tool --task AAV-0001 --tool read_file
agilev controls check-tool --task AAV-0001 --tool deploy_production
```

Expected:

- allow exits `0`
- deny exits non-zero
- JSON mode emits parseable JSON
- output includes `control_id`

### 18.4 Hook tests

File: `tests/test_openhands_control_hooks.py`

Tests:

- hook denies missing `AGILEV_TASK_ID`
- hook denies forbidden tool
- hook allows allowlisted read
- hook writes control event log
- hook requires approval for gated tool
- approved gated tool proceeds

Use temporary repo fixture with `.git`, `.agile-v`, config, task, approvals.

### 18.5 Evidence bundle tests

File: `tests/test_evidence_bundle_controls.py`

Tests:

- `L2+` evidence without `control_matrix` fails
- evidence with control matrix passes
- evidence with deny decision fails
- evidence with gate decision and no approval fails
- evidence with gate decision and approval passes
- rollback path required for `L2+`

### 18.6 CI checks

Add or extend GitHub Actions:

```yaml
name: Control Matrix Gates
on:
  pull_request:
  push:
    branches: [main]

jobs:
  control-matrix:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e .[dev]
      - run: agilev controls validate
      - run: pytest tests/test_control_matrix_schema.py tests/test_control_enforcer.py -q
```

---

## 19. PR plan

### PR 1: Schema and default matrix

Files:

- `schemas/control_matrix.schema.json`
- `config/control_matrix.yaml`
- `docs/control-matrix.md`
- `docs/adr/ADR-0002-control-matrix.md`

Acceptance:

- `agilev controls validate` may not exist yet.
- JSON schema is syntactically valid.
- Default matrix has no unresolved owner placeholders in production branch, or branch intentionally marks it `draft`.

### PR 2: Loader and semantic validation

Files:

- `src/agilev/control_matrix.py`
- `tests/test_control_matrix_loader.py`
- update `pyproject.toml` dependencies if adding `jsonschema`

Acceptance:

- `pytest tests/test_control_matrix_loader.py` passes.
- Duplicate IDs and invalid owners fail.

### PR 3: Enforcer and CLI

Files:

- `src/agilev/control_enforcer.py`
- `src/agilev/cli.py`
- `tests/test_control_enforcer.py`
- `tests/test_control_cli.py`

Acceptance:

- `agilev controls validate` works.
- `agilev controls check-tool` blocks forbidden tools.
- JSON output is stable.

### PR 4: OpenHands hooks

Files:

- `.openhands/hooks/enforce_control_matrix.sh`
- `.openhands/hooks/validate_control_evidence_on_stop.sh`
- `.openhands/hooks.json`
- `src/agilev/openhands/control_hooks.py`
- `src/agilev/openhands/scaffold.py`
- `tests/test_openhands_control_hooks.py`

Acceptance:

- `agilev openhands doctor` checks hooks.
- forbidden tool call is blocked before execution.
- gated tool call requires approval.

### PR 5: Evidence integration and CI

Files:

- `schemas/evidence_bundle.schema.json`
- evidence adapter or validation code
- `.github/workflows/control-matrix.yml`
- `tests/test_evidence_bundle_controls.py`

Acceptance:

- `L2+` evidence requires control matrix info.
- rollback path is enforced.
- CI runs on PR.

---

## 20. Migration strategy

Phase 1: add matrix in `draft` mode.

- CI validates syntax only.
- No blocking hooks.

Phase 2: enable warnings.

- Hooks log decisions.
- Deny decisions warn but do not block except destructive commands.

Phase 3: fail closed for `L3+`.

- Gated and forbidden actions block for high-risk tasks.

Phase 4: fail closed for all `L2+`.

- Evidence bundle must include control matrix section.

Phase 5: fail closed globally.

- All non-trivial agentic work requires matrix resolution.

---

## 21. Definition of done

Implementation is done when:

- `config/control_matrix.yaml` exists.
- `.agile-v/CONTROL_MATRIX.yaml` override is supported.
- Schema validation exists.
- Semantic validation exists.
- Tool allowlist and denylist are enforced.
- Model/vendor checks are implemented.
- Data-class checks are implemented.
- Cost limit checks are implemented.
- Human Gate decisions generate checkpoints.
- Approval references can unblock gated actions.
- Control events are written to JSONL logs.
- Evidence bundle includes control matrix results.
- Rollback path is enforced for `L2+`.
- Owner fields are required and non-placeholder.
- CI validates the matrix and related tests.
- OpenHands hooks use the same enforcement path as the CLI.
- Documentation explains how this consumes the skills repo templates.

---

## 22. Commands for developers

```bash
# install
pip install -e .[dev]

# validate control matrix
agilev controls validate

# explain selected control
agilev controls explain --task-type feature --risk L2 --mode builder --skill agile-v-builder

# check tool call
agilev controls check-tool --task AAV-0001 --tool shell_exec --json

# run tests
pytest tests/test_control_matrix_loader.py tests/test_control_enforcer.py tests/test_control_cli.py -q

# full repo tests
pytest

# OpenHands setup validation
agilev openhands doctor
```

---

## 23. Compatibility with skills repo

The skills repo should publish:

- `agile-v-control-matrix/SKILL.md`
- `templates/agile-v/CONTROL_MATRIX.example.yaml`
- `templates/agile-v/CONTROL_MATRIX.schema.json`
- runtime documentation for the matrix

The agentic repo should consume this by:

- copying or pinning the skill into `.agents/skills/`
- using the template as default `config/control_matrix.yaml`
- enforcing the matrix through `agilev controls` and OpenHands hooks
- recording selected skill and control ID in the evidence bundle

Do not let skills be the only control. Skills instruct agents. Hooks and validators enforce behavior.
