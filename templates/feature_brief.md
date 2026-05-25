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

### API Compatibility

**IMPORTANT:** Run interface validation before testing:

```bash
python scripts/validate_interface_contracts.py --task tasks/AAV-XXX/task_description.md --implementation src/module.py
```

This validation MUST PASS. It checks that your implementation API matches task examples exactly.

Common issue: Making parameters required that aren't in task examples breaks compatibility.

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

**IMPORTANT:** Run test quality validation:

```bash
python scripts/validate_test_quality.py --tests test_module.py
```

This validation ensures tests check EXTERNAL BEHAVIOR (what users/consumers see), not internal implementation.

✅ Good: `mock_connection.send.assert_called_with(message)`  
❌ Bad: `assert len(router._internal_queue) == 1`

## Risk level

`L0 | L1 | L2 | L3 | L4`

## Required evidence

- Evidence bundle path:
- Test logs:
- Reviewer checklist:

## Rollback path

How can this change be reverted safely?
