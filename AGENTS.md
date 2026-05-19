# AGENTS.md - Repository Instructions for AI Coding Agents

These rules apply to all agentic changes in this repository.

## Operating principle

Conversation is allowed for discovery. Implementation requires a structured task brief.

Do not implement from an ambiguous chat history. Before editing files, find or create a task brief and a task plan.

## Required sequence

1. Read this `AGENTS.md` file.
2. Read the task brief in `tasks/` or `evidence/`.
3. Inspect the relevant code before proposing changes.
4. Produce a short plan before editing.
5. Keep the patch minimal and scoped.
6. Add or update tests before claiming completion.
7. Update the evidence bundle.
8. Summarize residual risks.

## Change boundaries

- Do not change public APIs unless the brief explicitly requests it.
- Do not add dependencies without approval.
- Do not refactor unrelated code.
- Do not remove tests to make a build pass.
- Do not weaken security checks, authentication, authorization, logging, or validation.
- Do not change hardware pin mappings, timing assumptions, clock trees, or safety states without explicit evidence and review.
- Do not embed secrets, tokens, credentials, personal data, or proprietary customer data in code, tests, logs, prompts, or evidence bundles.

## Expected artifacts

For every non-trivial change, produce or update:

- task brief
- agent plan
- implementation diff
- tests or test rationale
- evidence bundle
- reviewer checklist
- residual-risk note

## Testing expectations

Run the narrowest relevant tests first, then broader tests as risk increases.

For software:

- unit tests
- integration tests where interfaces or persistence change
- lint/type/static analysis where available
- security checks for auth, input validation, secrets, or data handling

For firmware/hardware:

- build check
- simulation or emulator run where available
- HIL test where applicable
- timing, memory, protocol, and rollback evidence for high-risk changes

## Acceptance rule

A change is not complete because code was generated. It is complete only when the evidence bundle satisfies the required risk level.
