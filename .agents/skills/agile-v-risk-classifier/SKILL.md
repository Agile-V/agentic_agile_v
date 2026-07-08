---
name: agile-v-risk-classifier
description: Risk level classification guidance (L0-L4) for Agile-V tasks.
---

# Agile-V Risk Classification

## Risk Levels

### L0: Trivial
- Documentation changes, comments, README updates
- No change to code execution, no change to any test
- Examples: fix a typo, update a diagram, add a comment

### L1: Low Risk
- Small bug fixes in non-critical paths
- Internal refactors with no API or interface change
- New unit tests added to existing coverage
- Logging additions with no business logic change
- Examples: rename a variable, fix an off-by-one error, add a log statement

### L2: Moderate Risk
- New features (internal, non-security-sensitive)
- Non-breaking API or interface changes
- Additive database schema changes (new column, new table)
- New validated dependencies
- Changes to shared utilities or common modules
- Examples: add a new REST endpoint, add a search filter, add a new DB column

### L3: High Risk
- Breaking API or interface changes (existing callers affected)
- Authentication, authorization, or permission changes
- Cryptography or secret-handling changes
- Destructive or migrating database schema changes
- Infrastructure or deployment changes in production environments
- Security-sensitive configuration changes
- Examples: change auth token format, drop a database column, change CORS policy

### L4: Critical Risk
- Safety-critical system changes (hardware, firmware, medical, aviation, automotive)
- Financial transaction integrity (payment processing, ledger changes)
- Bulk customer data deletion or migration
- Cryptographic key rotation or algorithm change in regulated systems
- Changes requiring formal verification, HIL testing, or regulatory sign-off

## Evidence Requirements

| Level | Tests | Verifier | Approval | Special |
|-------|-------|----------|----------|---------|
| L0 | Optional | No | No | - |
| L1 | Required or rationale | No | No | - |
| L2 | Passing | Yes | Reviewer | - |
| L3 | Passing | Yes | Domain owner | Rollback path documented |
| L4 | Passing | Yes | Formal | Simulation/HIL/formal verification + traceability matrix |

## Classification Rules

**When unsure, default to the higher risk level.**

If a change touches multiple categories, use the highest level that applies.

L3/L4 classification requires an explicit risk assessment written into the evidence bundle before work begins.

A change initially classified as L1 must be re-classified if it unexpectedly touches an auth path, security control, or shared interface.
