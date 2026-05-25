# Bug-Fix Workflow

## Required inputs

- observed behavior
- expected behavior
- reproduction steps
- input data
- logs or traces
- environment
- affected version
- suspected area, if known
- failing test, if available

## Agent workflow

1. Reproduce or explain why reproduction is not possible.
2. State hypotheses before patching.
3. Localize affected code path.
4. Add a regression test that fails before the fix.
5. Apply a minimal patch.
6. Run regression and nearby tests.
7. Explain the causal fix.
8. Update evidence bundle.

## Acceptance rule

Do not accept a bug fix that has no reproduction, no regression test, and no causal explanation unless a human explicitly approves the exception.
