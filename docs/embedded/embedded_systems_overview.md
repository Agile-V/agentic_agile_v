# Embedded Systems Integration Overview

## Purpose

Agentic Agile-V provides a unified verification and evidence framework for **full embedded product development** that connects:

- **PCB/Hardware design** → Physical component selection, schematic, layout
- **Firmware** → Makes hardware executable, implements behavior
- **Software** → Controls and consumes firmware functionality  

This integration ensures that all three domains agree through machine-checkable contracts, evidence collection, and independent verification.

## Core Principle

> PCB describes what exists physically. Firmware makes that hardware executable. Software consumes and controls the firmware behavior. Agentic Agile-V proves that all three agree.

## Architecture Layers

```
Layer 8 - Human approval and release decision
  Product owner, electrical engineer, firmware engineer, software owner, QA, release owner

Layer 7 - Agile-V assurance layer
  Requirements, risk level, traceability, validation gates, evidence bundles, approval records

Layer 6 - System integration layer
  Hardware-firmware contract, firmware-software contract, end-to-end acceptance criteria

Layer 5 - Domain backends
  PCB backend, firmware backend, software/OpenHands backend

Layer 4 - Execution engines
  KiCad CLI, OpenHands, PlatformIO, Zephyr/west, Renode, OpenOCD, CI runners

Layer 3 - Deterministic checks
  Schema validation, ERC, DRC, BOM checks, builds, unit tests, static analysis, protocol tests

Layer 2 - Physical and simulated execution
  Emulators, simulators, connected boards, serial logs, flash logs, hardware-in-the-loop

Layer 1 - Repository and artifact store
  Git, pull requests, CI artifacts, signed evidence, release packages
```

## Responsibilities

### Agile-V Control Plane
- Owns process, risk classification, evidence requirements, traceability, gates, and approval
- Does NOT generate PCB/firmware/software (delegates to backends)
- Does NOT approve its own work (requires independent verification)

### PCB Backend
- Owns schematic/circuit artifacts, KiCad export, PCB validation evidence
- Exports hardware-firmware contract data (pinmap, netlist, interfaces)

### Firmware Backend
- Owns hardware-firmware contract, board config, firmware generation, firmware validation evidence
- Bridges PCB physical design to software-visible behavior

### OpenHands Backend
- Executes repository work, code edits, tests, documentation updates, pull requests
- Works under Agile-V supervision with hook-enforced gates

### CI
- Produces objective repeatable evidence
- Enforces gates automatically

### Humans
- Approve residual risk and release decisions
- Required for L3+ changes

## Key Design Decisions

### 1. Contracts are Machine-Checkable

All cross-domain interfaces use YAML contracts with JSON schemas:
- `system_contract.yaml` - Links product requirements to PCB/firmware/software tasks
- `hardware_firmware_contract.yaml` - PCB exports hardware capabilities to firmware
- `firmware_software_contract.yaml` - Firmware exposes API/protocol to software

### 2. Evidence Must Flow Across Domains

A requirement must trace through:
```
REQ-TEMP-001
  → PCB component (TMP117 sensor)
  → PCB nets (I2C1_SDA, I2C1_SCL, TEMP_INT)
  → Hardware-firmware contract (temp_sensor at 0x48 on I2C1)
  → Firmware implementation (temp_sensor.cpp)
  → Firmware test (test_temp_sensor_reading)
  → Firmware-software contract (get_temperature command)
  → Software implementation (temperature_client.ts)
  → Software test (test_get_temperature_success)
  → HIL evidence (serial_log_temp_sensor_read.txt)
```

### 3. Stale Evidence Detection

If PCB pinout changes after firmware implementation:
- Firmware evidence is marked STALE
- Software evidence is marked STALE  
- Release gate blocks merge until re-validation

### 4. Validation Ladder

```
1. Schema validation
2. Static checks
3. Host unit tests
4. Target cross-build
5. Simulation or emulation
6. Flash to target
7. Hardware-in-the-loop diagnostics
8. End-to-end software integration test
9. Independent verification
10. Human approval
```

Each risk level (L0-L4) requires different evidence coverage.

### 5. Manufacturing Red Line (Hardware)

**No AI-generated PCB may go to fabrication without explicit human EE approval.**

This is a BLOCKING GATE enforced in PCB evidence bundles.

### 6. Firmware Must Not Invent Hardware

Firmware cannot assume:
- Pins, buses, components, addresses, voltage levels, interrupts, clocks, or power states

...unless they exist in the hardware-firmware contract (which is derived from accepted PCB candidate).

### 7. Software Must Not Invent Firmware Capabilities

Software cannot assume:
- Commands, payloads, error codes, timing, protocol versions

...unless they exist in the firmware-software contract.

## Non-Goals

This integration does NOT:
- Replace electrical engineering judgment
- Auto-approve high-risk changes
- Generate production-ready firmware from prompt alone  
- Bypass testing or evidence requirements
- Weaken existing software/PCB workflows

## Integration with Existing Features

- **OpenHands integration** (PR #5) provides the execution backend for firmware and software tasks
- **PCB integration** (PR #6) provides circuit IR, KiCad CLI, component index, and validators
- **Embedded systems integration** (this PR) connects both through contracts and cross-domain verification

All three work together but can function independently where appropriate.

## Next Steps

See individual documents:
- [Unified System Contract](./unified_system_contract.md)
- [Hardware-Firmware Contract](./hardware_firmware_contract.md)
- [Firmware-Software Contract](./firmware_software_contract.md)
- [Firmware Backend](./firmware_backend.md)
- [Hardware-Firmware Verification](./hardware_firmware_verification.md)
- [Simulation and HIL](./simulation_and_hil.md)
- [Embedded Release Gates](./embedded_release_gates.md)
- [Embedded Human Review Guide](./embedded_human_review_guide.md)
