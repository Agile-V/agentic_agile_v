# Agentic Agile-V Infrastructure Manifest

This scaffold turns the Agentic Agile-V paper into operational repository infrastructure.

## Core files

- `AGENTS.md`: rules for coding agents.
- `README.md`: quick start and workflow.
- `.github/PULL_REQUEST_TEMPLATE.md`: evidence-first PR gate.
- `.github/workflows/agentic-agile-v-gates.yml`: CI validation for evidence bundles.

## Process docs

- `docs/agentic-agile-v.md`: macro Agile-V plus micro SCOPE-V process.
- `docs/risk-levels.md`: L0-L4 acceptance levels.
- `docs/evidence-bundles.md`: acceptance evidence model.
- `docs/feature-workflow.md`: feature workflow.
- `docs/bug-workflow.md`: bug workflow.
- `docs/hardware-firmware-workflow.md`: hardware and firmware workflow.
- `docs/testing-strategy.md`: testing gates.
- `docs/tooling-architecture.md`: agent/tooling architecture.
- `docs/adoption-checklist.md`: rollout plan.

## Templates

- `templates/feature_brief.md`
- `templates/bug_brief.md`
- `templates/hardware_firmware_brief.md`
- `templates/agent_plan.md`
- `templates/test_plan.md`
- `templates/review_checklist.md`
- `templates/evidence_bundle.json`

## Scripts

- `scripts/new_task.py`: create a structured task package.
- `scripts/validate_evidence.py`: validate evidence bundles using only Python stdlib.
- `scripts/risk_assessment.py`: simple local risk-level helper.

## Examples

- `tasks/examples/feature` and `evidence/examples/feature`
- `tasks/examples/bug` and `evidence/examples/bug`
- `tasks/examples/hardware` and `evidence/examples/hardware`

Validation command:

```bash
python scripts/validate_evidence.py --root evidence
```
