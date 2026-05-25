# Agent Plan

## Task ID

`AAV-000`

## Repository inspection summary

What files, modules, tests, and dependencies are relevant?

## Proposed changes

- `path/to/file`: planned change

## Files intentionally not touched

- `path/to/file`: reason

## Test strategy

- targeted tests:
- broader tests:
- manual/HIL tests:

### Data Type Considerations

For file-based data sources:

- [ ] CSV data is always strings (even numbers) - need type conversion for comparisons
- [ ] JSON data types verified against schema
- [ ] Numeric operations on file data require explicit conversion (float(), int())
- [ ] Tests use realistic data types (string "35", not number 35)
- [ ] Comparison operators (>, <, >=, <=) handle type conversion correctly

## Risk classification

`L0 | L1 | L2 | L3 | L4`

### Risk Factors Assessment

Check all that apply (**if ANY checked → consider escalating to higher level**):

- [ ] Concurrency/thread safety required
- [ ] Security/authentication involved
- [ ] Customer-visible behavior changes
- [ ] Data storage/migration needed
- [ ] Public API changes
- [ ] Complex state management
- [ ] External integrations (APIs, services, connections)
- [ ] Safety-critical/hardware/regulated
- [ ] Hard to test/verify

### Classification Rule

⚠️ **Escalate to L3 if ANY concurrency, security, complex state, or external integration**

**Justification:**

Why this level? What factors determined it?

## Time Allocation

### Minimum Time Calculation

Based on complexity and risk factors:

- Base time (from risk level):
  - L0: 15-20 min
  - L1: 30-60 min
  - L2: 90-180 min
  - L3: 180-360 min
  - L4: 360+ min

- Multipliers (add if applicable):
  - Concurrency/thread safety: +60 min
  - External integration: +30 min
  - Complex state: +30 min
  - Security: +30 min
  - Testing infrastructure: +20 min

**Total Minimum Required:** ___ minutes

**Actual Time Available:** ___ minutes

### Time Check Gate

**IMPORTANT:** Run time validation:

```bash
python scripts/validate_time_allocation.py --plan tasks/AAV-XXX/agent_plan.md
```

This validation MUST PASS. It ensures you're not rushing a complex task.

Evidence: Tasks with adequate time achieve 80-100% quality. Rushed tasks average 36% quality.

## Approval needed before edit?

`yes | no`

Reason:

## Residual concerns before implementation

- concern 1
