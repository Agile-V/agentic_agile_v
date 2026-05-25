# Feature Brief

## Task ID

`AAV-000`

## Title

Short feature title.

## Objective

What should be achieved?

## User-visible behavior

What should users observe after the change?

## Non-goals

What is explicitly out of scope?

## Affected modules

- `path/to/module`

## Interface contracts

Describe APIs, message formats, hardware interfaces, or public behavior that must remain stable or change explicitly.

### API Compatibility Checklist

If task provides examples or test framework:

- [ ] Reviewed task description for interface examples
- [ ] Identified all delivery methods that must be called (send(), write(), publish(), etc.)
- [ ] Verified method signatures match expected API
- [ ] Ensured parameters match task examples (if example shows `Foo(a, b)`, accept exactly `Foo(a, b)`)
- [ ] Made extra parameters optional with sensible defaults
- [ ] Tested object creation with minimal arguments from examples

## Constraints

- Compatibility:
- Security:
- Performance:
- Data migration:
- Dependencies:

## Acceptance criteria

- [ ] Criterion 1
- [ ] Criterion 2

## Test plan

- [ ] Unit tests:
- [ ] Integration tests:
- [ ] Regression tests:
- [ ] Manual or HIL tests:

### Test Quality Requirements

- [ ] Tests verify external interface (what consumers see), not internal implementation
- [ ] Tests use realistic data types (CSV = strings, not clean numbers)
- [ ] Tests verify actual delivery mechanisms (connection.send(), etc.)
- [ ] Tests include end-to-end workflows
- [ ] Tests include negative cases (what should NOT happen)

## Risk level

`L0 | L1 | L2 | L3 | L4`

## Required evidence

- Evidence bundle path:
- Test logs:
- Reviewer checklist:

## Rollback path

How can this change be reverted safely?
