# Feature Workflow

## Required inputs

- objective
- user-visible behavior
- non-goals
- affected modules
- interface contracts
- compatibility constraints
- data migration needs
- security considerations
- acceptance criteria
- test plan
- rollback path

## Agent workflow

1. Inspect existing implementation.
2. Summarize relevant design.
3. Propose file-level plan.
4. Wait for approval for L2+ changes.
5. Implement smallest useful slice.
6. Add or update tests.
7. Run checks.
8. Update evidence bundle.
9. Summarize residual risks.

## Acceptance rule

A feature is not done when code exists. It is done when acceptance criteria pass and evidence is attached.
