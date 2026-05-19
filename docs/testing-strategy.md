# Testing Strategy for Agentic Development

Testing is not a final step. It is part of the agent loop.

## Before implementation

Ask the agent to propose:

- relevant existing tests
- missing tests
- edge cases
- failure modes
- regression risk

## During implementation

Require the agent to:

- keep changes small
- run targeted tests first
- update tests with implementation
- avoid weakening existing tests

## Before merge

Run risk-appropriate gates:

- unit tests
- integration tests
- regression tests
- lint/type/static analysis
- security checks
- HIL or simulation for hardware/firmware

## After merge

Monitor:

- production logs
- hardware telemetry
- error rates
- performance regressions
- user feedback
- field defects

## Rule

If a change cannot be tested, require a written verification rationale and human approval.
