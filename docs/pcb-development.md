# PCB Development with Agile-V

## Overview

This document describes the PCB-specific workflow for Agentic Agile-V, extending the evidence-based gates framework to hardware design.

**Key Principle:**
> AI generates grounded, inspectable PCB candidates. Agile-V turns every candidate into structured evidence. KiCad and deterministic validators check what can be checked. A separate verifier and a human electrical engineer approve what remains risk-bearing.

The target is NOT "AI designs a PCB and we trust it."

The target IS: Fast, traceable, evidence-based PCB development where every design move is inspectable from requirement to component, net, schematic, validation report, and review decision.

---

## PCB Development Lifecycle

The PCB workflow extends Agile-V with hardware-specific stages:

### 1. Discover
**Goal:** Clarify product intent, electrical interfaces, power budget, environment, constraints.

**Activities:**
- Define what the board must do
- Identify functional blocks (MCU, sensors, power, interfaces)
- Establish voltage domains and power budget
- Determine environmental constraints (temperature, EMI, size)
- List mechanical and manufacturing constraints

**Output:** Initial requirements conversation

---

### 2. Specify
**Goal:** Convert conversation into a reviewed PCB task brief.

**Activities:**
- Create structured task brief from requirements
- Define electrical specifications (voltage, current, interfaces)
- List component constraints (approved parts, packages, vendors)
- Specify required interfaces with acceptance criteria
- Document manufacturing constraints (layer count, trace/space)

**Output:** PCB task brief (see `templates/pcb_brief.md`)

---

### 3. Constrain
**Goal:** Define approved components, voltage domains, interfaces, footprints, manufacturing rules.

**Activities:**
- Select approved component list
- Define voltage domain rules
- Specify interface standards (I2C, SPI, USB, etc.)
- Set manufacturing design rules
- List forbidden components or practices

**Output:** Component manifest, design constraints

---

### 4. Orchestrate
**Goal:** Select agents and validation depth based on PCB risk class.

**Activities:**
- Classify task risk level (L0-L4)
- Select appropriate validation gates
- Determine required evidence
- Choose agent workflow (builder, verifier, reviewer)

**Output:** Validation plan, evidence requirements

---

### 5. Generate
**Goal:** Produce multiple circuit IR candidates.

**Activities:**
- AI agent generates circuit intermediate representation (IR)
- Create component manifest with datasheet references
- Define netlist structure
- Produce multiple candidates for comparison

**Output:** Circuit IR (JSON), component manifest

---

### 6. Execute
**Goal:** Compile/export candidate into KiCad-compatible artifacts.

**Activities:**
- Convert circuit IR to KiCad schematic format
- Generate symbol libraries if needed
- Create footprint assignments
- Export KiCad project files

**Output:** KiCad `.kicad_sch`, `.kicad_pro` files

---

### 7. Prove
**Goal:** Run deterministic validation.

**Checks:**
- **Schema validation** - Circuit IR matches schema
- **Pin validation** - All pins correctly assigned
- **Net validation** - Nets properly connected
- **Symbol validation** - Symbols match components
- **Footprint validation** - Footprints assigned and correct
- **ERC (Electrical Rule Check)** - KiCad ERC passes
- **BOM generation** - Bill of materials complete
- **Netlist export** - Netlist is valid

**Output:** Validation reports, ERC results, BOM, netlist

---

### 8. Review
**Goal:** Run semantic checks and independent verifier.

**Checks:**
- **Datasheet compliance** - Pins, voltages, connections match datasheets
- **Voltage domain check** - All domains properly regulated and connected
- **Power budget check** - Current draw within limits
- **Interface check** - I2C pullups, SPI termination, USB compliance, etc.
- **Protection check** - ESD, reverse polarity, overcurrent protection
- **Semantic review** - Independent AI verifier checks design intent

**Output:** Semantic review report, verification report

---

### 9. Evolve
**Goal:** Repair candidate using validation feedback.

**Activities:**
- Analyze validation failures
- Update circuit IR to fix issues
- Re-export to KiCad
- Re-run validation
- Iterate until all checks pass

**Output:** Updated circuit IR, updated KiCad files

---

### 10. Accept
**Goal:** Create evidence bundle and require human EE approval for risk-bearing tasks.

**Activities:**
- Collect all validation reports
- Generate evidence bundle
- Create handoff report
- Require human electrical engineer review
- Document approval decision

**Output:** Evidence bundle, human approval, release decision

---

## Task Types

PCB tasks are classified differently from software tasks due to physical/electrical risks:

### Software Task (Existing)
```bash
agilev new --title "Add API endpoint" --risk L1
agilev validate
```

### PCB Task (NEW)
```bash
agilev new --type pcb --title "IMU sensor board" --risk L3
agilev pcb generate --task AAV-PCB-001
agilev pcb validate --task AAV-PCB-001
```

---

## Risk Classification for PCB

See `config/pcb_risk_levels.yaml` for detailed definitions.

**L0 - Documentation Only**
- Update design notes
- Add schematic review checklist
- Rename internal documentation

**L1 - Non-Electrical Artifact**
- Add BOM metadata
- Add reference schematic link
- Add library index entry (not used in design)

**L2 - Early Concept Schematic**
- Generated draft for exploration
- Low-power sensor breakout concept
- Reference-only design (not for fabrication)

**L3 - Prototype Candidate**
- Board for bench prototype
- Powered circuit with connectors
- Battery, USB, motor, RF, sensor integration

**L4 - Manufacturing/Safety Relevant**
- Design intended for fabrication
- Medical, regulated, safety-critical
- Mains power, lithium battery, high-current/voltage
- RF compliance, customer-facing hardware

---

## Manufacturing Red Line

**CRITICAL RULE:**

> No AI-generated PCB design may be sent to fabrication, customers, test subjects, or production without explicit human electrical engineering approval and risk-appropriate evidence.

This is a **BLOCKING GATE** enforced by:
- Evidence validation (required artifacts must exist)
- Risk-level gates (L3+ requires human EE approval)
- Release checks (`agilev pcb release-check`)

**Consequences of violation:**
- CI/CD will fail
- Release blocked
- Audit trail flags unapproved manufacturing

---

## Integration with Existing Agile-V

PCB development **extends** the existing framework:

### Existing Capabilities (Unchanged)
✅ Software task management  
✅ Evidence bundles  
✅ Risk classification (L0-L4)  
✅ Event logging  
✅ OpenHands integration  
✅ GitHub Actions workflows  

### New PCB Capabilities (Added)
➕ Circuit IR (intermediate representation)  
➕ KiCad integration (ERC, DRC, BOM, netlist)  
➕ Component and datasheet indexing  
➕ Hardware-specific validators  
➕ PCB-specific agents (builder, verifier)  
➕ Hardware evidence collection  
➕ PCB CLI commands (`agilev pcb ...`)  

### Shared Infrastructure
- Task briefs (extended with PCB fields)
- Evidence bundles (extended with hardware artifacts)
- Event ledger (logs PCB events)
- Risk gates (extended with PCB-specific rules)
- Human review gates (extended with EE approval)

---

## Example Workflow

### Creating a Simple Sensor Board (L3)

```bash
# 1. Create PCB task
agilev new --type pcb --id AAV-PCB-001 --title "Wearable IMU sensor node" --risk L3

# 2. Edit task brief
vim .agentic-agile-v/tasks/AAV-PCB-001/task_brief.md
# Add electrical specs, component constraints, interfaces

# 3. Clarify requirements
agilev pcb clarify --task AAV-PCB-001
# AI agent asks clarifying questions

# 4. Generate design candidates
agilev pcb generate --task AAV-PCB-001 --candidates 5
# Produces 5 circuit IR candidates

# 5. Validate all candidates
agilev pcb validate --task AAV-PCB-001 --all-candidates
# Runs ERC, netlist, BOM, semantic checks

# 6. Rank candidates
agilev pcb rank --task AAV-PCB-001
# Shows which candidate passes most checks

# 7. Export best candidate to KiCad
agilev pcb export --task AAV-PCB-001 --candidate 3 --format kicad

# 8. Collect evidence
agilev pcb evidence collect --task AAV-PCB-001

# 9. Independent verification
agilev pcb verify --task AAV-PCB-001 --fresh-context

# 10. Generate handoff report
agilev pcb report --task AAV-PCB-001

# 11. Human EE review (REQUIRED for L3+)
# Engineer reviews schematic, evidence bundle, validation reports
# Records approval decision

# 12. Release check (before fabrication)
agilev pcb release-check --task AAV-PCB-001
# BLOCKS if human approval missing or evidence incomplete
```

---

## Validation Gates by Risk Level

### L0 (Documentation)
- Task brief exists
- Reviewer note present

### L1 (Non-Electrical)
- Task brief exists
- Schema validation passes
- Reviewer note present

### L2 (Concept Schematic)
- All L1 evidence
- Circuit IR valid
- Component manifest complete
- Netlist exports
- ERC passes
- Schematic PDF generated
- Semantic review passes
- Human review note present

### L3 (Prototype)
- All L2 evidence
- Datasheet extracts linked
- Voltage domain check passes
- Power budget check passes
- Interface check passes (I2C, SPI, USB, etc.)
- Independent verification passes
- Rollback/rework plan documented
- **Named human EE approval required**

### L4 (Manufacturing/Safety)
- All L3 evidence
- Layout DRC passes (if PCB layout exists)
- Schematic-layout parity verified
- Manufacturing output review (Gerbers)
- Formal design review minutes
- Second independent review
- Release signoff
- **Explicit statement that AI output was reviewed by qualified humans**

---

## Tools and Dependencies

### Required
- **KiCad 8.0+** - PCB design tool
- **kicad-cli** - Command-line interface for automation
- **Python 3.11+** - Agile-V runtime
- **Git** - Version control

### Optional
- **Understand Anything** - Datasheet parsing and indexing
- **OpenHands** - AI agent execution
- **pcbGPT reference** - Circuit IR inspiration

---

## File Structure

PCB tasks use this structure:

```
.agentic-agile-v/
  tasks/
    AAV-PCB-001/
      task_brief.md              # PCB requirements
      pcb_design_plan.md         # Design approach
      candidates/
        candidate_001/
          circuit_ir.json        # Intermediate representation
          component_manifest.json
          kicad/                 # Exported KiCad files
            project.kicad_sch
            project.kicad_pro
          validation/
            erc_report.txt
            bom.csv
            netlist.net
            semantic_review.md
        candidate_002/
          ...
      evidence/
        evidence_bundle.json     # Complete evidence
        validation_reports/
        verification_report.md
        human_approval.md
      reports/
        handoff_report.md
```

---

## Next Steps

1. **Read the PCB risk model:** `docs/pcb-risk-model.md`
2. **Review validation gates:** `docs/pcb-validation-gates.md`
3. **Understand agent workflow:** `docs/pcb-agent-workflow.md`
4. **See human review guide:** `docs/pcb-human-review-guide.md`
5. **Try an example:** `examples/pcb/imu_sensor_node/`

---

## Safety and Liability

**WARNING:**

PCB design involves electrical, thermal, and mechanical risks. AI-generated designs are NOT safe for production use without thorough human review by qualified electrical engineers.

**Agile-V provides:**
- Evidence collection and validation
- Deterministic checks (ERC, DRC, netlist)
- Audit trails
- Review workflows

**Agile-V does NOT provide:**
- Electrical engineering expertise
- Safety certification
- Liability protection
- Guarantee of correctness

**Your responsibilities:**
- Ensure qualified EE review for all manufactured designs
- Follow applicable regulations and standards
- Test prototypes before production
- Document all safety-critical decisions
- Maintain liability insurance for hardware products

---

**Version:** 1.0  
**Last Updated:** 2026-06-08  
**Status:** Initial implementation
