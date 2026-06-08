# PCB Semantic Review: {{TASK_ID}}

**Task:** {{TASK_ID}} - {{TITLE}}  
**Reviewer:** {{VERIFIER_AGENT_OR_HUMAN}}  
**Review Date:** {{DATE}}  
**Candidate:** {{CANDIDATE_ID}}

---

## Review Summary

**Overall Assessment:** PASS / CONDITIONAL PASS / FAIL

**Critical Issues:** {{COUNT}}  
**Warnings:** {{COUNT}}  
**Recommendations:** {{COUNT}}

---

## Datasheet Compliance

### Component Pin Assignments

| Component | Datasheet Pins | Actual Connections | Status | Notes |
|-----------|----------------|-------------------|--------|-------|
| | | | ✓ / ⚠ / ✗ | |

### Voltage Ratings

| Component | Rated Voltage | Applied Voltage | Margin | Status |
|-----------|---------------|-----------------|--------|--------|
| | | | | ✓ / ⚠ / ✗ |

### Current Ratings

| Component | Rated Current | Expected Current | Margin | Status |
|-----------|---------------|------------------|--------|--------|
| | | | | ✓ / ⚠ / ✗ |

### Typical Application Circuits

| Component | Typical Application Followed | Deviations | Justification |
|-----------|------------------------------|------------|---------------|
| | Yes / No / Partial | | |

---

## Power Architecture Review

### Voltage Domains

| Domain | Voltage | Source | Load | Status | Issues |
|--------|---------|--------|------|--------|--------|
| | | | | ✓ / ⚠ / ✗ | |

**Issues:**
- [ ] Mixed voltage on same net
- [ ] Missing level shifter
- [ ] Insufficient decoupling
- [ ] Improper power sequencing

### Power Budget

| Rail | Capacity | Load (Typical) | Load (Max) | Margin | Status |
|------|----------|----------------|------------|--------|--------|
| | | | | | ✓ / ⚠ / ✗ |

**Issues:**
- [ ] Insufficient margin
- [ ] Regulator overloaded
- [ ] Missing current limiting

---

## Interface Compliance

### I2C
- [ ] Pullup resistors present: ___Ω to ___V
- [ ] Pullup values correct for bus capacitance
- [ ] Voltage levels compatible with all devices
- [ ] No conflicts on 7-bit addresses

**Issues:**

### SPI
- [ ] Termination appropriate for frequency
- [ ] Voltage levels compatible
- [ ] CS lines correctly assigned
- [ ] Clock polarity/phase compatible

**Issues:**

### USB
- [ ] Termination resistors correct (D+/D- 90Ω, pullup 1.5kΩ)
- [ ] ESD protection on D+/D-
- [ ] Enumeration circuit correct
- [ ] Power management correct

**Issues:**

### UART
- [ ] Voltage levels compatible
- [ ] Baud rate generators compatible
- [ ] Flow control correct (if used)

**Issues:**

---

## Protection Circuits

### Input Protection
- [ ] Reverse polarity protection present
- [ ] Overcurrent protection present and correct
- [ ] Overvoltage protection present and correct
- [ ] ESD protection on all external connectors

**Issues:**

### Output Protection
- [ ] Short circuit protection adequate
- [ ] Thermal shutdown present (if high power)

**Issues:**

---

## Grounding and Decoupling

### Decoupling Capacitors
- [ ] Every power pin has local decoupling
- [ ] Bulk capacitance adequate
- [ ] Values appropriate for switching frequency

**Issues:**

### Ground Connections
- [ ] Ground strategy appropriate (star vs distributed)
- [ ] Analog/digital grounds handled correctly
- [ ] No ground loops

**Issues:**

---

## Clock and Reset

### Clocking
- [ ] Crystal/oscillator load capacitors correct
- [ ] Clock routing appropriate
- [ ] Clock accuracy sufficient for peripherals (UART, USB, etc.)

**Issues:**

### Reset
- [ ] Reset circuit appropriate
- [ ] Reset timing adequate
- [ ] Watchdog configured correctly (if used)

**Issues:**

---

## Critical Issues (MUST FIX)

1. 
2. 
3. 

---

## Warnings (SHOULD FIX)

1. 
2. 
3. 

---

## Recommendations (CONSIDER)

1. 
2. 
3. 

---

## Verification Checklist

- [ ] All component datasheets reviewed
- [ ] Pin assignments verified against datasheets
- [ ] Voltage/current ratings verified
- [ ] Typical application circuits compared
- [ ] Power budget verified
- [ ] Voltage domains validated
- [ ] Interfaces validated (I2C, SPI, USB, UART, etc.)
- [ ] Protection circuits validated
- [ ] Decoupling adequate
- [ ] Grounding strategy appropriate
- [ ] Clocking correct
- [ ] Reset circuit correct

---

## Decision

**PASS:** Design meets all requirements, no critical issues  
**CONDITIONAL PASS:** Design acceptable with warnings addressed  
**FAIL:** Critical issues must be fixed before proceeding

**Reviewer Decision:** PASS / CONDITIONAL PASS / FAIL

**Conditions (if conditional):**

**Next Steps:**

---

**Reviewer:** {{NAME}}  
**Date:** {{DATE}}  
**Signature:** {{SIGNATURE_IF_HUMAN}}
