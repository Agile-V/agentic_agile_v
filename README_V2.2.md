# Agentic Agile-V v2.2 - Active Quality Gates

**Version:** 2.2  
**Status:** Ready for validation testing  
**Previous Version:** 2.1 (regressed from 68.2% to 54.5%)  
**Target:** 80-90% quality on validation tests

---

## What's New in v2.2

### Active Enforcement Scripts

v2.2 introduces **active quality gates** inspired by the Agile-V Skills quality-gates skill that achieved 100% on validation testing.

**The key insight:** Passive checklists don't work. You need active enforcement.

### New Validation Scripts

1. **`validate_interface_contracts.py`** - Interface Validation Gate
   - Checks implementation API matches task examples
   - Catches incompatibilities BEFORE tests run
   - Prevents TypeErrors and missing argument errors

2. **`validate_test_quality.py`** - Test Quality Gate
   - Ensures tests check external behavior, not internal state
   - Prevents self-assessment gaps (tests pass but quality fails)
   - Promotes observable, user-facing testing

3. **`validate_time_allocation.py`** - Time Allocation Gate (from v2.1)
   - Prevents rushing complex tasks
   - Evidence-based time requirements

4. **`run_quality_gates.py`** - Master Script
   - Runs all quality gates
   - Must pass before submission
   - Provides clear feedback and fix guidance

---

## Why v2.2 Exists

### The v2.1 Regression

v2.1 added enhanced templates with passive checklists. Result:

- **68.2% → 54.5%** (-13.7% regression)
- Agent checked boxes without actually validating
- Made `Message.sender_id` required (breaking change)
- 8 tests ERROR with API incompatibility
- Enhanced templates provided false confidence

### The Root Cause

> **Passive checklists ≠ Active quality gates**

Templates said "Check API compatibility ✓" but agent:
1. Read checklist
2. Implemented code  
3. Checked the box
4. Never actually tested compatibility
5. Broke 8 tests

### The Solution

**Active enforcement** like Agile-V Skills quality-gates:
- Scripts that ACTUALLY RUN
- FAIL if quality issues detected
- Provide fix guidance
- Force agent to fix before proceeding

---

## How to Use

### Before Implementation

1. Read task description
2. Create feature_brief.md and agent_plan.md
3. Calculate time allocation

### During Implementation

4. Write code
5. Write tests

### Before Submission (REQUIRED)

6. **Run quality gates:**

```bash
# Auto-discover mode (recommended)
python scripts/run_quality_gates.py --task-id AAV-001

# Manual mode
python scripts/run_quality_gates.py \
  --task tasks/AAV-001/task_description.md \
  --plan tasks/AAV-001/agent_plan.md \
  --impl src/module.py \
  --tests test_module.py
```

7. **Fix any failures** - cannot submit until all gates PASS

8. Run actual tests and submit

---

## Quality Gates Explained

### 1. Interface Contract Gate

**What it checks:**
- Implementation API matches task examples
- Message(topic, payload) works if task shows Message(topic, payload)
- No required parameters missing from examples

**Why it matters:**
- #1 failure mode in v2.1
- 8 tests ERROR due to API incompatibility
- TypeErrors break everything

**Example failure:**
```
❌ FAIL: Interface incompatibility detected

Example call missing required parameter(s): sender_id

Resolution:
  Make sender_id optional with default value
```

**How to fix:**
```python
# Before (breaks)
@dataclass
class Message:
    topic: str
    payload: dict
    sender_id: str  # Required!

# After (works)
@dataclass
class Message:
    topic: str
    payload: dict
    sender_id: Optional[str] = None  # Optional!
```

---

### 2. Test Quality Gate

**What it checks:**
- Tests verify external behavior (connection.send(), etc.)
- Tests don't only check internal state (queues, buffers)
- At least 70% of tests check external interface

**Why it matters:**
- Self-assessment gap: v2.0 tests passed (100%) but quality was 68%
- Tests checking internal queues miss actual delivery bugs
- External behavior is what users/hidden tests see

**Example failure:**
```
❌ FAIL: Test quality is inadequate (40% check external behavior)

Problematic Tests:
  - test_publish_message (line 45)
    Issue: Checking internal state (queues)
    Fix: Verify connection.send() called
```

**How to fix:**
```python
# Before (bad)
def test_publish():
    router.publish(msg)
    assert len(router._message_queues[client_id]) == 1  # ❌ internal

# After (good)
def test_publish():
    router.publish(msg)
    mock_connection.send.assert_called_once_with(message)  # ✅ external
```

---

### 3. Time Allocation Gate

**What it checks:**
- Adequate time allocated based on risk level
- Complexity multipliers applied (concurrency +60min, etc.)
- Not rushing complex tasks

**Why it matters:**
- Evidence: Rushed tasks (5 min on L3) = 36% quality
- Adequate time (180+ min on L3) = 80-100% quality
- Strong correlation (r=0.89) between time and quality

**Example failure:**
```
❌ FAIL: Insufficient time allocated
   Shortfall: -135 min (only 25% of minimum)

Resolution:
  Allocate 135 more minutes
```

---

## Comparison: v2.1 vs v2.2

| Aspect | v2.1 (Passive) | v2.2 (Active) |
|--------|----------------|---------------|
| **Approach** | Enhanced templates with checklists | Validation scripts that run |
| **Enforcement** | None - agent checks boxes | Scripts FAIL if issues found |
| **Interface** | Checklist: "Verify API ✓" | Script: Parses task + tests API |
| **Test Quality** | Checklist: "Test external ✓" | Script: Analyzes test code |
| **Time** | Calculation in template | Script validates calculation |
| **Feedback** | Passive - read and hope | Active - run and fix |
| **Confidence** | False (boxes checked, bugs exist) | Real (scripts verify quality) |
| **Result** | 54.5% (regression) | 80-90% expected |

---

## Changes from v2.1

### Added

- ✅ `scripts/validate_interface_contracts.py` - NEW
- ✅ `scripts/validate_test_quality.py` - NEW  
- ✅ `scripts/run_quality_gates.py` - NEW master script
- ✅ Active enforcement in templates (reference scripts)

### Modified

- 🔧 `templates/feature_brief.md` - Removed passive checklists, added script references
- 🔧 `templates/agent_plan.md` - Simplified, added validation commands

### Removed

- ❌ Passive API compatibility checklist
- ❌ Passive test quality checklist
- ❌ False-confidence checkboxes

---

## Expected Results

### Validation Test Performance

| Version | Pass Rate | Change | Status |
|---------|-----------|--------|---------|
| v2.0 baseline | 68.2% | - | Baseline |
| v2.1 enhanced | 54.5% | -13.7% | ⚠️ REGRESSION |
| v2.2 active gates | **80-90%** | **+25-35%** | 🎯 TARGET |

### Quality Gates vs Passive Templates

**Quality-gates skill (active):** 100% ✅  
**Enhanced templates (passive):** 54.5% ❌  
**v2.2 active gates:** 80-90% expected 🎯

---

## How This Fixes the Regression

### The v2.1 Problem

1. Enhanced templates said: "Check API compatibility"
2. Agent thought: "I'll make it more robust with required sender_id"
3. Agent checked: "API compatibility ✓"
4. Reality: Broke 8 tests with TypeError
5. Templates provided false confidence

### The v2.2 Solution

1. Agent writes code
2. Runs: `python scripts/validate_interface_contracts.py`
3. Script checks: Can Message(topic, payload) work?
4. Script finds: NO - sender_id required but not in example
5. Script FAILS with clear error and fix guidance
6. Agent fixes: Makes sender_id optional
7. Script passes: API compatible ✅

**Result:** Bug caught DURING implementation, not AFTER tests fail.

---

## Testing v2.2

### Quick Test

```bash
# From framework/agentic-agile-v/v2.2/

# Test interface validation
python scripts/validate_interface_contracts.py \
  --task ../../experiments/tasks/task_13_websocket_router/TASK.md \
  --implementation ../../experiments/2026-05-validation-test/implementations/agentic-agile-v_v2.1/implementation/websocket_router.py

# Should FAIL and show sender_id incompatibility
```

### Full Validation Test

Run Task 13 with v2.2 agent instructions:
1. Copy framework to test environment
2. Run Task 13 WebSocket Router
3. Agent should use quality gates during implementation
4. Expected result: 80-90% pass rate

---

## Lessons Learned

### From Agile-V Skills v2.1 (100% success)

✅ **Active guidance during implementation**  
✅ **Real-time validation that FAILS on issues**  
✅ **Clear, actionable error messages**  
✅ **Enforcement, not suggestion**

### From Agentic v2.1 (54.5% regression)

❌ **Passive checklists get ignored**  
❌ **Agents check boxes without understanding**  
❌ **Templates can't enforce quality**  
❌ **False confidence is worse than no confidence**

### The Universal Truth

> **Checklists in templates ≠ Active validation scripts**

Quality requires active enforcement at the right moment (during implementation), not passive suggestions that can be ignored.

---

## Next Steps

### Immediate

1. ✅ v2.2 framework ready
2. ⏳ Test on Task 13 WebSocket Router
3. ⏳ Compare with v2.1 results
4. ⏳ Validate improvement achieved

### If Successful (≥80%)

1. Update PR #1 to Agentic Agile-V repo
2. Test on other tasks (Task 14, 15)
3. Document as best practice

### If Still Issues (<80%)

1. Analyze remaining failures
2. Add more quality gates if needed
3. Iterate on scripts
4. Re-test

---

## Files

```
framework/agentic-agile-v/v2.2/
├── scripts/
│   ├── validate_time_allocation.py       # Time gate (from v2.1)
│   ├── validate_interface_contracts.py   # NEW - Interface gate
│   ├── validate_test_quality.py          # NEW - Test quality gate
│   └── run_quality_gates.py              # NEW - Master script
├── templates/
│   ├── feature_brief.md                  # Updated - references scripts
│   └── agent_plan.md                     # Updated - references scripts
└── README_V2.2.md                        # This file
```

---

## Success Criteria

v2.2 is successful if:

1. ✅ Quality gates catch v2.1's API incompatibility bug
2. ✅ Validation test achieves ≥80% (vs v2.1's 54.5%)
3. ✅ No regression from active enforcement overhead
4. ✅ Scripts provide actionable fix guidance
5. ✅ Can be adopted by other frameworks

---

**Status:** Ready for validation testing  
**Confidence:** High - based on quality-gates skill 100% success  
**Expected Improvement:** +25-35% over v2.1

Let's validate! 🚀
