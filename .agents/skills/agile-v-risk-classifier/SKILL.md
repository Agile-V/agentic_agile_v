---
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
