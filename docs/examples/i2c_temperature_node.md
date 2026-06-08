# I2C Temperature Node - Reference Example

This reference example demonstrates the complete embedded systems integration workflow for an I2C temperature sensor node.

## Overview

**Hardware:** STM32F401 MCU with TMP102 I2C temperature sensor
**Firmware:** Temperature reading with diagnostics
**Software:** Python API for temperature monitoring

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      PCB Layer (L3 Risk)                     │
│  - STM32F401 MCU                                             │
│  - TMP102 I2C Temperature Sensor @ 0x48                      │
│  - USB-C for power and communication                         │
│  - I2C bus: SDA=PB7, SCL=PB6                                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ hardware_firmware_contract.yaml
                       │ (MCU, pins, interfaces)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   Firmware Layer (L2 Risk)                   │
│  - Initialize I2C1 on PB6/PB7                                │
│  - Read temperature from TMP102                              │
│  - USB CDC serial protocol                                   │
│  - Commands: get_temperature, run_diagnostics                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ firmware_software_contract.yaml
                       │ (Commands, transport, protocol)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   Software Layer (L1 Risk)                   │
│  - Python API client                                         │
│  - Temperature monitoring                                    │
│  - Data logging and alerting                                 │
└─────────────────────────────────────────────────────────────┘
```

## Workflow Steps

### 1. PCB Design (Hardware Layer)

```bash
# Create PCB project
agilev pcb init

# Export circuit IR
agilev pcb export-circuit-ir \
  --project pcb/temp_sensor \
  --output pcb/temp_sensor/circuit_ir.json
```

**Circuit IR includes:**
- MCU: STM32F401
- I2C1 interface: SDA=PB7, SCL=PB6
- TMP102 sensor: address 0x48
- USB interface for CDC serial

### 2. Generate Hardware-Firmware Contract

```bash
# Generate contract from PCB
agilev firmware contract generate \
  --from-pcb pcb/temp_sensor/circuit_ir.json \
  --output .agentic-agile-v/contracts/hardware_firmware_contract.yaml

# Validate contract
agilev firmware contract validate \
  .agentic-agile-v/contracts/hardware_firmware_contract.yaml
```

### 3. Generate Firmware Project

```bash
# Generate PlatformIO firmware project
agilev firmware generate \
  --contract .agentic-agile-v/contracts/hardware_firmware_contract.yaml \
  --output firmware/temp_sensor

# Generated files:
#  - platformio.ini (build config)
#  - src/board_contract.h (pin definitions)
#  - src/main.cpp (skeleton)
#  - src/diagnostics.cpp (diagnostics)
```

### 4. Develop Firmware (with OpenHands)

```bash
# Start OpenHands firmware session
python -c "
from agilev.openhands.firmware_builder import FirmwareBuilderConfig
from pathlib import Path

config = FirmwareBuilderConfig(
    contract_path=Path('.agentic-agile-v/contracts/hardware_firmware_contract.yaml'),
    firmware_project_dir=Path('firmware/temp_sensor'),
    task_id='TASK-123-firmware',
)

session_id = config.create_session()
print(f'Session ID: {session_id}')
"

# OpenHands implements:
#  - I2C initialization
#  - TMP102 driver
#  - USB CDC protocol handler
#  - Temperature reading command
#  - Diagnostics command

# Hooks automatically enforce:
#  - No contract modifications
#  - No PCB modifications
#  - Scope limited to firmware/
#  - Tests required (L2 risk)
```

### 5. Build and Test Firmware

```bash
# Build firmware
agilev firmware build --project firmware/temp_sensor

# Run simulation (Renode)
agilev firmware simulate \
  --project firmware/temp_sensor \
  --mcu STM32F401

# Run host tests
agilev firmware test --project firmware/temp_sensor --host

# Run HIL tests (requires hardware)
agilev firmware hil-test \
  --project firmware/temp_sensor \
  --port /dev/ttyUSB0 \
  --flash
```

### 6. Generate Firmware-Software Contract

```bash
# Generate contract from firmware
agilev firmware contract generate-software \
  --project firmware/temp_sensor \
  --contract-id FSC-001 \
  --task-id TASK-123-firmware \
  --output .agentic-agile-v/contracts/firmware_software_contract.yaml

# Contract includes:
#  - Commands: get_temperature, run_diagnostics
#  - Transport: usb_cdc_serial
#  - Protocol: JSON over serial
#  - Error codes
```

### 7. Generate Software API

```bash
# Generate Python API from contract
agilev software generate-api \
  --contract .agentic-agile-v/contracts/firmware_software_contract.yaml \
  --output software/temp_sensor_api.py

# Generated API includes:
#  - FSC_001_API class
#  - get_temperature() method
#  - run_diagnostics() method
#  - Serial communication
#  - Error handling
```

### 8. Use Software API

```python
from software.temp_sensor_api import FSC_001_API

# Connect to device
with FSC_001_API('/dev/ttyUSB0') as api:
    # Run diagnostics
    diag = api.run_diagnostics()
    print(f"I2C Scan: {diag['i2c_scan']}")
    print(f"Self Test: {diag['self_test']}")
    
    # Read temperature
    temp = api.get_temperature()
    print(f"Temperature: {temp['temperature_c']}°C")
    print(f"Status: {temp['status']}")
```

### 9. Verify Cross-Domain Consistency

```bash
# Verify all contracts match
agilev embedded verify

# Checks:
#  - PCB circuit IR ↔ hardware-firmware contract
#  - hardware-firmware contract ↔ firmware-software contract
#  - Pin assignments match
#  - Interfaces match
#  - No invented hardware
```

### 10. Release Gate

```bash
# Check release gate
agilev embedded gate \
  --task-id TASK-123 \
  --risk-level L2 \
  --firmware-task TASK-123-firmware

# Gate checks:
#  - Evidence freshness (not stale)
#  - Tests passed
#  - Build artifacts present
#  - Simulation passed (L2+)
#  - HIL passed (L3+)
#  - EE approval (L4)
```

## Evidence Trail

Each phase generates evidence:

1. **PCB Evidence** (`TASK-123_evidence.json`):
   - Circuit IR
   - ERC results
   - Component manifest
   - Approval status

2. **Firmware Evidence** (`TASK-123-firmware_evidence.json`):
   - Build artifacts (SHA-256 hashes)
   - Test results
   - Simulation results
   - HIL results
   - Contract compliance

3. **Software Evidence** (`TASK-123-software_evidence.json`):
   - API tests
   - Integration tests
   - Contract compliance

## Risk Levels

- **PCB:** L3 (requires ERC, simulation, human EE approval)
- **Firmware:** L2 (requires tests, build, simulation)
- **Software:** L1 (requires tests)

## Contract Enforcement

### Firmware Cannot Invent Hardware

```bash
# BLOCKED: Firmware tries to use SPI (not in contract)
# Hook: enforce_hardware_firmware_contract.sh
# Result: ✗ Contract violation - SPI not in hardware-firmware contract
```

### Software Cannot Invent Firmware APIs

```bash
# BLOCKED: Software calls invalid command
# Result: FirmwareError: UNKNOWN_COMMAND
```

### Stale Evidence Detection

```bash
# PCB changed → firmware evidence marked stale
# Result: ✗ Release gate BLOCKED - evidence is stale
```

## File Structure

```
.
├── pcb/
│   └── temp_sensor/
│       ├── circuit_ir.json          # PCB export
│       └── kicad_project/
├── firmware/
│   └── temp_sensor/
│       ├── platformio.ini            # Build config
│       ├── src/
│       │   ├── board_contract.h      # Pin definitions
│       │   ├── main.cpp              # Main firmware
│       │   └── diagnostics.cpp       # Diagnostics
│       ├── test/
│       │   └── test_temperature.cpp  # Tests
│       ├── renode/
│       │   ├── platform.resc         # Simulation config
│       │   └── results.json          # Simulation results
│       └── hil/
│           ├── test_config.json      # HIL config
│           └── results.json          # HIL results
├── software/
│   ├── temp_sensor_api.py            # Generated API
│   └── monitor.py                    # Application
├── .agentic-agile-v/
│   ├── contracts/
│   │   ├── system_contract.yaml      # System-level
│   │   ├── hardware_firmware_contract.yaml  # PCB→FW
│   │   └── firmware_software_contract.yaml  # FW→SW
│   ├── evidence/
│   │   ├── TASK-123_evidence.json    # PCB evidence
│   │   ├── TASK-123-firmware_evidence.json  # FW evidence
│   │   └── TASK-123-software_evidence.json  # SW evidence
│   ├── verification/
│   │   └── cross_domain.json         # Verification results
│   └── gates/
│       └── TASK-123_gate.json        # Gate results
└── config/
    └── embedded/
        └── embedded_risk_levels.yaml  # Risk config
```

## Success Criteria

✅ PCB design exported to Circuit IR
✅ Hardware-firmware contract generated from PCB
✅ Firmware project generated from contract
✅ Firmware implements contract (validated by hooks)
✅ Firmware builds successfully
✅ Firmware passes tests (host + simulation + HIL)
✅ Firmware-software contract generated
✅ Software API generated from contract
✅ Software successfully communicates with firmware
✅ Cross-domain verification passes
✅ Release gate passes for all risk levels
✅ Evidence trail complete and machine-verifiable

## Next Steps

1. **Clone and customize** this example for your use case
2. **Modify risk levels** in `config/embedded/embedded_risk_levels.yaml`
3. **Add more sensors** to the PCB and contracts
4. **Extend firmware commands** for new functionality
5. **Build applications** using the generated API

## References

- [Embedded Systems Overview](../embedded/embedded_systems_overview.md)
- [ADR-0002: Embedded Systems Layer](../adr/ADR-0002-embedded-systems-layer.md)
- [Risk Levels](../../config/embedded/embedded_risk_levels.yaml)
- [Phase Plan](../../agentic_agile_v_embedded_systems_integration_plan.md)
