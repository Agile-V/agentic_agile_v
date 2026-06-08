# PCB Task Brief: {{TASK_ID}}

**Task ID:** {{TASK_ID}}  
**Title:** {{TITLE}}  
**Risk Level:** {{RISK_LEVEL}}  
**Created:** {{DATE}}  
**Owner:** {{OWNER}}

---

## Title

Brief, descriptive title for this PCB task.

---

## Intent

Describe what the board or schematic must do. Include:
- Purpose of the board
- Key functionality
- Integration context (where will this be used?)

---

## Intended Use

Check all that apply:

- [ ] Exploration only (concept, not for fabrication)
- [ ] Bench prototype (internal testing only)
- [ ] Manufacturing candidate (intended for production)
- [ ] Safety or regulated context (medical, automotive, mains power, etc.)

---

## Functional Blocks

List all functional blocks required:

### MCU
- Part number or family:
- Clock frequency:
- Flash/RAM:
- Special requirements:

### Sensors
| Type | Part Number | Interface | Special Requirements |
|------|-------------|-----------|---------------------|
| | | | |

### Power Input
- Input voltage range:
- Connector type:
- Protection required:

### Power Regulation
- Output rails required:
- Regulators (LDO vs switching):
- Sequencing requirements:

### Battery or Charging
- Battery type:
- Capacity:
- Charging IC:
- Protection:

### Communication Interfaces
| Interface | Pins/Signals | Voltage Level | Notes |
|-----------|-------------|---------------|-------|
| | | | |

### Debug/Programming
- Interface (SWD, JTAG, UART, USB):
- Connector:
- Requirements:

### Connectors
| Connector | Type | Pins | Purpose |
|-----------|------|------|---------|
| | | | |

### Protection
- ESD protection:
- Reverse polarity:
- Overcurrent:
- Overvoltage:

---

## Electrical Requirements

### Voltage
- Input voltage range: ___V to ___V
- Output voltage rails:
  - ___V @ ___mA (typical) / ___mA (max)
  - ___V @ ___mA (typical) / ___mA (max)
  - ___V @ ___mA (typical) / ___mA (max)

### Power Budget
- Total power consumption (typical): ___mW
- Total power consumption (max): ___mW
- Battery life target (if applicable): ___

### Logic Levels
- MCU I/O voltage: ___V
- Sensor I/O voltages: ___V
- Level shifters required: Yes / No

### Interfaces

#### I2C
- SCL/SDA voltage: ___V
- Pullup resistors: ___Ω to ___V
- Clock speed: ___kHz
- Devices on bus:

#### SPI
- MOSI/MISO/SCK voltage: ___V
- Clock speed: ___MHz
- CS lines required: ___
- Devices on bus:

#### UART
- TX/RX voltage: ___V
- Baud rate: ___
- Flow control: Yes / No

#### USB
- USB version: 2.0 / 3.0 / USB-C
- Power delivery: No / USB-PD / BC1.2
- Data lines: D+/D- only / USB 3.0 + HS

#### CAN
- CAN version: 2.0A / 2.0B / CAN-FD
- Termination: 120Ω
- Voltage: ___V

#### Other
- Describe any other interfaces:

### Clocking
- Main clock source: crystal / oscillator / internal RC
- Frequency: ___MHz
- Accuracy required: ±___ppm
- 32kHz RTC: Yes / No

### Reset/Boot
- Reset circuit: external / internal / supervisor IC
- Boot mode selection: required / not required
- Watchdog: required / not required

---

## Mechanical and Manufacturing Constraints

### Board Dimensions
- Maximum size: ___mm x ___mm
- Thickness: ___mm (standard is 1.6mm)
- Shape: rectangular / custom (attach outline)

### Connector Orientation
- Connectors on: top / bottom / edge
- Orientation requirements:

### Mounting
- Mounting holes: Yes / No
- Hole diameter: ___mm
- Hole locations:

### Layer Count
- Layers: 2 / 4 / 6 / other
- Justification for layer count:

### Trace and Spacing
- Minimum trace width: ___mm (6mil/0.15mm is common)
- Minimum spacing: ___mm (6mil/0.15mm is common)
- Impedance controlled traces: Yes / No
  - If yes, impedance: ___Ω differential / ___Ω single-ended

### Assembly Constraints
- SMT only / THT only / Mixed
- Smallest component: 0402 / 0603 / 0805 / larger
- BGA allowed: Yes / No
- Preferred assembly house:

### Manufacturer Rules
- Preferred PCB fab:
- IPC class: 1 / 2 / 3
- Special requirements (e.g., controlled impedance, flex, HDI):

---

## Component Constraints

### Approved Component List
- Use components from: [link to approved list or specify below]
- Specific components required:

### Preferred Vendors
- Preferred suppliers: Digi-Key / Mouser / LCSC / other
- Avoid suppliers:

### Forbidden Components
- Do NOT use:
- Reasons:

### Package Constraints
- Allowed packages: 0603 and larger / 0402 and larger / specific packages
- Forbidden packages: BGA / QFN / other

### Availability Constraints
- All components must be: in stock / available within ___ weeks
- Lifecycle status: active / NRND acceptable / obsolete not acceptable
- Minimum stock level: ___ units

### Temperature Range
- Operating temperature: ___°C to ___°C
- Storage temperature: ___°C to ___°C
- Industrial / automotive / military grade required: Yes / No

---

## Required Interfaces

| Interface | Pins | Voltage | Pullups/Termination | Acceptance Criteria |
|-----------|------|---------|---------------------|---------------------|
| I2C | SCL, SDA | 3.3V | 4.7kΩ to 3.3V | Must communicate with sensor at 400kHz |
| SPI | MOSI, MISO, SCK, CS | 3.3V | None | Must read/write flash at 20MHz |
| USB | D+, D- | USB spec | 1.5kΩ pullup | Must enumerate as USB device |
| UART | TX, RX | 3.3V | None | Must communicate at 115200 baud |
| | | | | |

---

## Required Evidence

### For this risk level ({{RISK_LEVEL}}), the following evidence is required:

**Always required:**
- [ ] Task brief (this document)
- [ ] Circuit IR (intermediate representation)
- [ ] Component manifest with datasheets
- [ ] KiCad schematic export
- [ ] ERC (Electrical Rule Check) report
- [ ] Netlist export
- [ ] BOM (Bill of Materials)
- [ ] Schematic PDF for review

**L2+ (Concept) additional:**
- [ ] Semantic review by AI verifier
- [ ] Human review note

**L3+ (Prototype) additional:**
- [ ] Datasheet extracts for key components
- [ ] Voltage domain validation
- [ ] Power budget analysis
- [ ] Interface compliance check (I2C, SPI, USB, etc.)
- [ ] Protection circuit validation
- [ ] Independent verification report
- [ ] Rollback/rework plan
- [ ] Named human EE approval

**L4 (Manufacturing) additional:**
- [ ] Layout DRC (if layout exists)
- [ ] Schematic-layout parity check
- [ ] Manufacturing output review (Gerbers)
- [ ] Formal design review minutes
- [ ] Second independent review
- [ ] Release signoff
- [ ] AI review statement

---

## Acceptance Criteria

Define specific, testable criteria for accepting this design:

1. [ ] 
2. [ ] 
3. [ ] 
4. [ ] 
5. [ ] 

---

## Constraints and Exclusions

### What this task DOES include:


### What this task DOES NOT include:


### Known limitations:


---

## Dependencies

### Component Availability
- List any components with long lead times:

### External Interfaces
- List any external boards or systems this must interface with:

### Design Assets
- List any required design files, references, or libraries:

---

## Success Metrics

How will we know this design is successful?

- [ ] All acceptance criteria met
- [ ] All validation gates pass
- [ ] ERC clean (zero errors)
- [ ] Human EE approves design
- [ ] (For L3+) Prototype builds and boots
- [ ] (For L3+) All interfaces functional
- [ ] (For L4) Passes manufacturing review

---

## Risk Assessment

### Known Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| | | | |

### Escalation Triggers

This task should escalate to higher risk level if:

- [ ] Input voltage exceeds 50V (escalate to L4)
- [ ] Current exceeds 1A (escalate to L4)
- [ ] Lithium battery charging required (escalate to L4)
- [ ] Mains power connection (escalate to L4)
- [ ] RF transmitter (escalate to L4)
- [ ] Medical/safety-critical use (escalate to L4)
- [ ] Customer-facing hardware (escalate to L4)

---

## Timeline

- Task created: {{DATE}}
- Target for first candidate: 
- Target for prototype build: 
- Target for manufacturing release: 

---

## References

### Datasheets
- Component 1: [link]
- Component 2: [link]

### Design References
- Similar designs:
- Application notes:

### Standards and Regulations
- Applicable standards (e.g., USB spec, I2C spec):
- Regulatory requirements (e.g., FCC, CE, UL):

---

## Notes

Additional context, clarifications, or considerations:

---

## Approval

### Task Brief Review
- Reviewed by: 
- Date: 
- Approved: Yes / No / Needs revision

### Engineering Approval (L3+ only)
- Electrical Engineer: 
- Date: 
- Approval decision: Approved / Conditional / Rejected
- Conditions or concerns:

---

**Template Version:** 1.0  
**Last Updated:** 2026-06-08
