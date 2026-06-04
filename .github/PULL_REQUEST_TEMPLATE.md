# Pull Request: Agentic Agile-V Evidence Gate

## Task Information

- **Task ID:** AAV-XXX
- **Risk Level:** L0 | L1 | L2 | L3 | L4
- **Task Type:** Feature | Bug | Hardware/Firmware | Documentation

## Required Evidence

### All Risk Levels (L0+)
- [ ] Task brief completed and reviewed: `tasks/AAV-XXX/brief.md`
- [ ] Agent plan created: `tasks/AAV-XXX/plan.md`
- [ ] Evidence bundle generated: `evidence/AAV-XXX/evidence_bundle.json`
- [ ] Evidence bundle validates: `python scripts/validate_evidence.py --bundle evidence/AAV-XXX/evidence_bundle.json`

### L1+ Requirements
- [ ] Tests added or test rationale provided
- [ ] At least one static check passed (lint, type, build, or static analysis)

### L2+ Requirements
- [ ] Unit and/or integration tests passing
- [ ] CI checks passing
- [ ] Human reviewer assigned and approved

### L3+ Requirements
- [ ] Security/privacy/regression evidence provided
- [ ] Rollback path documented (not "N/A")
- [ ] Impact analysis completed
- [ ] Approval from authorized reviewer

### L4+ Requirements
- [ ] Independent verification completed
- [ ] Simulation/HIL/formal evidence or approved waiver
- [ ] Traceability matrix complete
- [ ] Safety/regulatory approval obtained

## Evidence Bundle Validation

```bash
python scripts/validate_evidence.py --bundle evidence/AAV-XXX/evidence_bundle.json
```

**Validation result:** PASS | FAIL

## Reviewer Checklist

- [ ] Evidence bundle exists and validates
- [ ] Changed files match what's documented in evidence
- [ ] Tests cover the requirements
- [ ] No stubs or anti-patterns without rationale
- [ ] Risk level matches scope of change
- [ ] Rollback path is realistic (L3+)
- [ ] Compliance requirements met (if applicable)

## Residual Risks

<!-- Document any known risks or limitations -->

## Additional Notes

<!-- Any additional context or information -->

---

**By approving this PR, I confirm that:**
- The evidence bundle is complete and accurate
- The risk level is appropriate for this change
- All required gates have been satisfied or explicitly waived
- This change is ready for merge

Reviewer: ________________  
Date: ___________  
Signature/Approval: ________________
