# ADR-0002: Embedded Systems Layer

## Status

Proposed

## Context

Agentic Agile-V currently supports:
1. Software development with OpenHands integration (traceability, evidence, gates)
2. PCB development with Circuit IR, KiCad CLI, component index, validators

However, real embedded products require THREE tightly-coupled domains:
- **PCB**: Physical hardware (pins, components, nets, power, interfaces)
- **Firmware**: Makes hardware executable (drivers, protocols, diagnostics)
- **Software**: Application logic that controls/consumes firmware

Without a bridge connecting all three, we risk:
- Firmware assuming pins/buses/components that don't exist in hardware
- Software assuming commands/protocols that firmware doesn't implement
- PCB changes silently invalidating firmware/software evidence
- Missing end-to-end traceability from requirements → PCB → firmware → software
- High-risk embedded changes without appropriate evidence

## Decision

We will add a **first-class embedded systems layer** that:

###  1. Owns cross-domain contracts
- `system_contract.yaml` - Links product requirements to PCB/firmware/software tasks
- `hardware_firmware_contract.yaml` - Exports PCB capabilities to firmware
- `firmware_software_contract.yaml` - Exports firmware API to software

### 2. Implements firmware backends
- PlatformIO backend (initial priority)
- Zephyr backend (for devicetree/RTOS workflows)
- CMake/bare-metal backend (for minimal MCU projects)

### 3. Exports PCB artifacts to firmware
- Pinmap (MCU pins → nets → components)
- Interface map (I2C/SPI/UART topology, addresses, chip-selects)
- Power rail model (voltage domains, nominal/tolerance)
- ADC scaling (resistor dividers)

### 4. Connects firmware to software via contracts
- Protocol commands and payloads
- Error codes and retry expectations
- Timing and data freshness requirements

### 5. Adds simulation and HIL evidence
- Renode simulation (optional, recommended for L2+)
- Hardware-in-the-loop runner (required for L3+)
- Flash logs, serial logs, diagnostic outputs

### 6. Implements cross-domain verification
- PCB netlist ↔ hardware-firmware contract validation
- Firmware config ↔ hardware-firmware contract validation
- Software implementation ↔ firmware-software contract validation
- Stale evidence detection across domains

### 7. Adds embedded release gate
- Aggregates PCB + firmware + software evidence
- Enforces L0-L4 approval policies
- Blocks merge if contracts are inconsistent or evidence is stale

## Consequences

### Positive

- **End-to-end traceability**: Requirements trace through PCB → firmware → software → HIL evidence
- **Contract enforcement**: Firmware can't invent hardware, software can't invent firmware capabilities
- **Stale evidence detection**: PCB changes automatically invalidate downstream evidence
- **Validation ladder**: Clear path from schema → build → test → simulation → HIL → approval
- **Backend flexibility**: PlatformIO, Zephyr, bare-metal all supported through common interface
- **OpenHands integration**: Existing software backend extends naturally to firmware tasks

### Negative

- **Increased complexity**: Three domains (PCB, firmware, software) must stay synchronized
- **Setup overhead**: Requires hardware-firmware contracts before firmware work can start
- **Toolchain dependencies**: PlatformIO, KiCad, potentially Renode/OpenOCD for full workflow
- **Learning curve**: Developers must understand contracts, evidence requirements, risk levels

### Neutral

- **Agile-V remains control plane**: Firmware backends are execution engines, not autonomous decision-makers
- **No auto-approval**: L3/L4 changes still require human electrical/firmware/software approval
- **Backward compatibility**: Existing software and PCB workflows continue to work independently

## Responsibilities

### What Agile-V Owns
- Process, risk classification, evidence requirements, traceability
- Contract schemas and validation
- Cross-domain verification and stale evidence detection
- Release gates and approval enforcement

### What Agile-V Does NOT Own
- PCB design decisions (delegates to electrical engineers)
- Firmware implementation (delegates to firmware backends + OpenHands)
- Software implementation (delegates to software backends + OpenHands)
- Toolchain configuration (PlatformIO, Zephyr, KiCad)

### What Requires Human Approval
- L3/L4 PCB changes (before fabrication - BLOCKING GATE)
- L3/L4 firmware changes (boot, power, watchdog, safety, security)
- L3/L4 software changes (protocol, API, release)
- All system releases

## Alternatives Considered

### Alternative 1: No firmware layer (manual integration)
- **Rejected**: Creates gap between PCB and software, no evidence flow, high risk of mismatch

### Alternative 2: Firmware as separate project (not integrated)
- **Rejected**: Loses cross-domain traceability, no stale evidence detection, duplicates gates

### Alternative 3: All-in-one autonomous firmware generator
- **Rejected**: Too risky without contracts, human oversight, and independent verification

### Alternative 4: Hardware-firmware contract only (no firmware-software contract)
- **Rejected**: Software would still invent firmware capabilities, no protocol versioning

## Implementation Phases

1. **Phase 0**: Architecture decision and boundaries (this document)
2. **Phase 1**: Schemas and templates
3. **Phase 2**: Embedded and firmware CLI
4. **Phase 3**: PCB-to-firmware export
5. **Phase 4**: PlatformIO backend
6. **Phase 5**: OpenHands firmware integration
7. **Phase 6**: Firmware-software contract
8. **Phase 7**: Simulation support
9. **Phase 8**: HIL runner
10. **Phase 9**: Cross-domain verifier
11. **Phase 10**: Embedded release gate
12. **Phase 11**: Reference example (I2C temperature node)

## Success Criteria

- A new contributor can run the I2C temperature node example end-to-end
- All contracts validate
- Full requirement traceability from REQ → PCB → firmware → software → HIL
- Release gate blocks merge when evidence is stale or insufficient
- Human approval enforced for L3/L4 embedded changes
- Existing software and PCB workflows remain unaffected

## References

- [Embedded Systems Overview](../embedded/embedded_systems_overview.md)
- [OpenHands Integration Plan](../../agentic_agile_v_openhands_integration_plan.md)
- [PCB Development Integration Plan](../../agentic_agile_v_pcb_development_integration_plan.md)
- [Embedded Systems Integration Plan](../../agentic_agile_v_embedded_systems_integration_plan.md)
