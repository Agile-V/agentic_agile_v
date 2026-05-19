# Risk Levels and Acceptance Gates

## L0 - Informational or trivial

Examples:

- documentation edits
- comments
- typo fixes
- local non-functional cleanup

Evidence:

- brief or issue reference
- agent plan
- reviewer note

## L1 - Low-risk internal change

Examples:

- internal helper function
- non-public UI text
- isolated script

Evidence:

- brief
- plan
- tests or test rationale
- lint/static check if available

## L2 - Normal production change

Examples:

- standard feature
- normal bug fix
- API-neutral refactor

Evidence:

- brief
- plan
- unit tests
- integration or regression tests where relevant
- CI pass
- human review

## L3 - High-risk software change

Examples:

- authentication or authorization
- customer data
- persistent state
- public API
- payment, audit, export, or compliance-sensitive workflow
- CI/CD or infrastructure change

Evidence:

- all L2 evidence
- security/privacy review
- rollback path
- migration plan if data changes
- explicit human approval

## L4 - Critical, hardware, safety, regulated, or irreversible

Examples:

- firmware update path
- hardware timing or pinout
- medical, safety, lab, production, or regulated device behavior
- money movement
- cryptographic boundary
- critical infrastructure

Evidence:

- all L3 evidence
- independent verification
- HIL, simulation, formal checks, or equivalent
- traceability matrix
- release approval
- rollback or recovery evidence
