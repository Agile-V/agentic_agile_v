# PCB Design Plan: {{TASK_ID}}

**Task ID:** {{TASK_ID}}  
**Title:** {{TITLE}}  
**Plan Version:** 1.0  
**Created:** {{DATE}}  
**Planner:** {{AGENT_OR_ENGINEER}}

---

## Design Approach

### Overall Strategy

Describe the high-level approach to this PCB design:

---

## Architecture Decisions

### Block Diagram

```
[ASCII block diagram or reference to attached diagram]
```

### Component Selection Rationale

| Function | Selected Component | Rationale |
|----------|-------------------|-----------|
| MCU | | |
| Voltage Regulator | | |
| Sensor | | |
| Interface IC | | |
| Protection | | |

---

## Power Architecture

### Power Tree

```
Input (___V) 
  └─> Reverse Polarity Protection
      └─> Overcurrent Protection
          └─> Regulator 1 (___V)
              ├─> MCU (___mA)
              ├─> Sensor 1 (___mA)
              └─> Interface IC (___mA)
          └─> Regulator 2 (___V)
              └─> Sensor 2 (___mA)
```

### Power Budget

| Rail | Voltage | Load | Typical | Max | Regulator | Margin |
|------|---------|------|---------|-----|-----------|--------|
| | | | | | | |

**Total power consumption:**
- Typical: ___mW
- Maximum: ___mW
- Margin: ___%

---

## Signal Integrity

### Critical Signals

| Signal | Type | Frequency | Length Constraint | Notes |
|--------|------|-----------|-------------------|-------|
| | | | | |

### Impedance Requirements

| Signal | Target Impedance | Tolerance | Stackup |
|--------|------------------|-----------|---------|
| | | | |

---

## Thermal Considerations

### Heat Sources

| Component | Power Dissipation | Thermal Management |
|-----------|-------------------|-------------------|
| | | |

### Thermal Requirements
- Ambient temperature range: ___°C to ___°C
- Maximum junction temperature: ___°C
- Cooling method: passive / active / heatsink

---

## Interface Design

### I2C Bus
- Voltage: ___V
- Clock frequency: ___kHz
- Pullup resistors: ___Ω to ___V
- Devices: [list]
- Bus capacitance budget: ___pF

### SPI Bus
- Voltage: ___V
- Clock frequency: ___MHz
- Topology: single master / multi-master
- Devices: [list]

### USB
- Type: USB 2.0 / 3.0 / USB-C
- Termination resistors:
  - D+: ___Ω
  - D-: ___Ω
  - Pullup: ___kΩ on D+ to ___V
- ESD protection: [part number]

### Other Interfaces
[Describe any other interfaces]

---

## Protection Circuits

### Input Protection
- Reverse polarity: method / component
- Overcurrent: method / component / trip point
- Overvoltage: method / component / clamp voltage
- ESD: TVS diodes on all connectors

### Output Protection
- Short circuit protection: method
- Thermal shutdown: method

---

## Layout Constraints

### Critical Placement
- Components that must be close together:
- Components that must be separated:
- Keep-out zones:

### Routing Constraints
- Differential pairs: impedance, length matching
- Clock signals: routing guidelines
- Power distribution: plane vs trace

### Grounding Strategy
- Ground planes: continuous / split
- Ground connections: star / distributed
- Analog/digital ground: separate / common

---

## Test Points and Debug

### Required Test Points
| Signal | Purpose | Location |
|--------|---------|----------|
| | | |

### Debug Interface
- Programming: connector / pads / header
- UART debug: connector / pads / header
- Status LEDs: [list]

---

## Variants and Options

### Build Options
- Option 1: [description]
- Option 2: [description]
- DNP (Do Not Populate) components:

### Future Expansion
- Unpopulated footprints for future features:
- Reserved pins:

---

## Manufacturing Considerations

### Assembly Notes
- Assembly sequence:
- Special handling:
- Conformal coating: Yes / No / Selective

### Testing Strategy
- Continuity test: Yes / No
- Power-on test: Yes / No
- Functional test: Yes / No
- In-circuit test: Yes / No

---

## Design Milestones

- [ ] Component selection complete
- [ ] Circuit IR generated
- [ ] Schematic capture complete
- [ ] ERC clean
- [ ] Design review #1
- [ ] Layout started
- [ ] Layout complete
- [ ] DRC clean
- [ ] Design review #2
- [ ] Manufacturing files generated
- [ ] Prototype order
- [ ] Prototype bring-up
- [ ] Design validation complete

---

## Risk Mitigation

### Identified Risks

| Risk | Impact | Mitigation | Status |
|------|--------|------------|--------|
| | | | |

---

## Validation Plan

### Schematic Validation
- [ ] ERC passes with zero errors
- [ ] All nets connected
- [ ] All components have footprints
- [ ] Power pins connected
- [ ] Decoupling capacitors present
- [ ] Pullup/pulldown resistors where needed

### Semantic Validation
- [ ] Datasheets reviewed
- [ ] Pin assignments verified
- [ ] Voltage ratings verified
- [ ] Current ratings verified
- [ ] Interface compliance verified
- [ ] Protection circuits verified

### Layout Validation (if applicable)
- [ ] DRC passes with zero errors
- [ ] Schematic-layout parity verified
- [ ] Critical clearances met
- [ ] Signal integrity requirements met
- [ ] Thermal requirements met
- [ ] Manufacturing requirements met

---

## Dependencies

### Blocking Items
- [ ] Awaiting component datasheet for: [component]
- [ ] Awaiting interface spec for: [interface]
- [ ] Awaiting mechanical constraints from: [source]

### External Reviews Required
- [ ] Mechanical review (enclosure fit)
- [ ] Software review (pin assignments)
- [ ] Safety review (protection circuits)
- [ ] Regulatory review (compliance)

---

## Approval

### Design Plan Review
- Reviewed by: 
- Date: 
- Status: Approved / Conditional / Needs Revision
- Comments:

---

**Template Version:** 1.0  
**Last Updated:** 2026-06-08
