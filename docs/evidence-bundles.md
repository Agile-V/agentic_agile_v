# Evidence Bundles

An evidence bundle is the acceptance artifact for agent-generated work.

It answers five questions:

1. What was the agent asked to do?
2. What constraints applied?
3. What changed?
4. How was it verified?
5. What risk remains?

## Minimum fields

- task id
- task type
- risk level
- requirement ids
- brief path
- plan path
- changed files
- tests
- checks
- evidence artifacts
- reviewer gate
- residual risks

## Strong evidence examples

- failing test before bug fix
- passing test after fix
- integration test logs
- static analysis output
- security scan output
- HIL logs
- simulator output
- traceability matrix
- rollback validation
- reviewer approval

## Weak evidence examples

- "The agent says it works"
- screenshots without test commands
- generated explanation without executable proof
- unrelated passing tests
- no reproduction for a bug
- no rollback plan for persistent data changes
