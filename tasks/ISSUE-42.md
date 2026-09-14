# ISSUE-42 — reference conformance adapter

Source: https://github.com/Agile-V/agile_v_skills/issues/42, section 5.
Baseline: `54eaa5451fcbfe9fa1c59355584deddbf7cef342`.

## Task brief

Implement a runtime-owned, read-only admission evaluation command and versioned
capability manifest. Consume the same candidate records and synthetic trusted
provider records as the skills reference conformance tests; compare normalized
decisions and reason codes. Scope is a cooperative local conformance path,
not production authorization, signed approvals, or changes to existing hooks.

## Plan

1. Add a separately callable `python -m agilev.assurance` command using trusted
   context and schemas supplied independently of candidate stdin.
2. Implement runtime-native checks without importing `contracts.semantics`.
3. Export a packaged compatibility manifest documenting implemented scope.
4. Execute positive/adversarial cases through subprocesses in the skills suite.
5. Retain results/limitations; do not claim live human authentication or
   integration into existing OpenHands completion routes.

## Acceptance and residual risks

Required cases: positive, wrong subject, wrong policy, unsupported property,
changed adapter, missing property requirement, wrong approval, incomplete waiver,
insufficient independence, partial reuse. Malformed input must reject with a
structured error. No candidate field can supply the trusted context path.

This command does not mutate task state, perform external actions, or consume
single-use approvals. Trusted files must be protected by the caller; same-user
filesystem access is not a security boundary. Publication and production-route
integration remain separate release work.
