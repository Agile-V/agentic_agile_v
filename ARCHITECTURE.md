# Agile-V Architecture: Software + PCB

## System Independence ✅

**Key Design Principle**: PCB features are an **OPTIONAL EXTENSION** of the core software features. The system works perfectly for software development without any PCB/hardware dependencies.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     AGILE-V CORE                            │
│                  (Software Development)                      │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ State Management                                      │  │
│  │  - EventLogger (audit trail)                         │  │
│  │  - TaskState (task tracking)                         │  │
│  │  - LockManager (concurrency)                         │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ OpenHands Integration                                 │  │
│  │  - Session Manager (builder/verifier)                │  │
│  │  - Evidence Adapter (test results, diffs)            │  │
│  │  - Event Ledger (SHA-256 hash chain)                 │  │
│  │  - GitHub Actions workflows                          │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Task Context                                          │  │
│  │  - Task resolution (AAV-XXXX)                        │  │
│  │  - Evidence bundles                                   │  │
│  │  - Risk levels (L0-L4)                               │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  Dependencies: pyyaml (core only)                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
                  ┌─────────┴─────────┐
                  │                   │
                  ↓                   ↓
        ┌──────────────────┐  ┌──────────────────┐
        │  SOFTWARE ONLY   │  │  WITH PCB/HW     │
        │                  │  │                  │
        │  ✅ Works fully  │  │  ✅ + Hardware   │
        │  ✅ No KiCad     │  │  ⚠️ KiCad opt.   │
        │  ✅ Software dev │  │  ✅ PCB dev      │
        └──────────────────┘  └──────────────────┘
                                       ↓
                        ┌──────────────────────────┐
                        │  PCB EXTENSION (OPTIONAL)│
                        │                          │
                        │  Circuit IR              │
                        │  Component Index         │
                        │  Validators              │
                        │  KiCad CLI (optional)    │
                        │                          │
                        │  No extra dependencies   │
                        └──────────────────────────┘
```

## Feature Matrix

| Feature | Software Only | Software + PCB |
|---------|--------------|----------------|
| **Task Management** | ✅ Full | ✅ Full |
| **Evidence Bundles** | ✅ Code/tests | ✅ Code + PCB |
| **Risk Levels** | ✅ L0-L4 software | ✅ L0-L4 hardware |
| **OpenHands** | ✅ Full integration | ✅ Full integration |
| **Event Ledger** | ✅ Hash chain | ✅ Hash chain |
| **GitHub Actions** | ✅ CI/CD | ✅ CI/CD |
| **Circuit IR** | ❌ N/A | ✅ PCB design |
| **Component Index** | ❌ N/A | ✅ Approved parts |
| **Validators** | ❌ N/A | ✅ Power/voltage |
| **KiCad** | ❌ N/A | ⚠️ Optional |

## CLI Commands

### Core Commands (No PCB Needed)
```bash
# Repository setup
agilev init

# Task management
agilev new --title "Fix authentication bug" --risk L2
agilev validate

# OpenHands (software development)
agilev openhands run --task AAV-0001
agilev openhands sessions
agilev openhands events
agilev openhands verify-chain
agilev openhands handoff

# Evidence collection
agilev collect-evidence --task AAV-0001
```

**Dependencies**: 
- ✅ Python 3.11+
- ✅ pyyaml
- ⚠️ OpenHands (for `openhands` commands)

### PCB Commands (Optional Extension)
```bash
# PCB-specific (no KiCad required)
agilev pcb validate --task AAV-0002
agilev pcb components --list --approved-only

# KiCad integration (requires KiCad installed)
agilev pcb erc --task AAV-0002
agilev pcb export --task AAV-0002
```

**Additional Dependencies**:
- ⚠️ KiCad 8.0+ (only for `pcb erc` command)

## Module Dependencies

### Software-Only Modules
```
src/agilev/
├── state.py              # ✅ Core state (no deps)
├── task_context.py       # ✅ Task resolution (no deps)
├── cli.py                # ✅ CLI (requires pyyaml)
└── openhands/
    ├── session_manager.py    # ✅ OpenHands (no extra deps)
    ├── evidence_adapter.py   # ✅ Evidence (no extra deps)
    ├── event_ledger.py       # ✅ Hash chain (no extra deps)
    ├── scaffold.py           # ✅ Scaffolding (no extra deps)
    ├── github_actions.py     # ✅ CI/CD (no extra deps)
    └── reports.py            # ✅ Reports (no extra deps)
```

### PCB Extension Modules (Optional)
```
src/agilev/pcb/
├── circuit_ir.py          # ✅ No extra deps
├── component_index.py     # ✅ No extra deps
├── validators.py          # ✅ No extra deps
├── kicad_cli.py          # ⚠️ Requires KiCad (optional)
└── cli.py                # ✅ No extra deps
```

## Import Independence

Software features never import PCB modules:
```python
# ✅ Software modules are independent
from agilev.state import EventLogger
from agilev.openhands.session_manager import OpenHandsSessionManager
# No PCB imports required!

# ✅ PCB modules are opt-in
from agilev.pcb.circuit_ir import CircuitIR  # Only if using PCB
```

CLI dynamically loads PCB commands:
```python
# src/agilev/cli.py
from agilev.pcb.cli import build_pcb_parser  # Only imported, not required

# PCB commands added to parser
build_pcb_parser(subparsers)  # Fails gracefully if PCB not installed
```

## Use Cases

### Use Case 1: Pure Software Development ✅
**User**: Web developer using Agile-V for API development  
**Tools**: Python, Git, pytest, OpenHands  
**KiCad**: Not installed  

```bash
agilev init
agilev new --title "Add OAuth2" --risk L2
agilev openhands run --task AAV-0001
agilev validate
# ✅ Everything works
```

### Use Case 2: Software + PCB Development ✅
**User**: IoT developer doing firmware + hardware  
**Tools**: Python, Git, pytest, OpenHands, KiCad  
**KiCad**: Installed  

```bash
# Software task
agilev new --title "Add BLE driver" --risk L2
agilev openhands run --task AAV-0001

# PCB task
agilev new --title "ESP32 Board" --risk L3
agilev pcb validate --task AAV-0002
agilev pcb erc --task AAV-0002
# ✅ Everything works
```

### Use Case 3: PCB-Only Development ✅
**User**: Hardware engineer doing board design  
**Tools**: Python, Git, KiCad  
**OpenHands**: Not using  

```bash
agilev init
agilev new --title "Power Supply Board" --risk L4

# Create circuit in Python (Circuit IR)
python design_circuit.py

# Validate
agilev pcb validate --task AAV-0001
agilev pcb components --list

# Manual KiCad work, then:
agilev pcb erc --task AAV-0001

# Manufacturing approval (L4)
# Evidence bundle reviewed by human EE
# ✅ Everything works
```

## Backward Compatibility

**Question**: If someone has Agile-V installed and working for software, will adding PCB features break anything?

**Answer**: ✅ **NO!**

1. **No breaking changes** to existing APIs
2. **No new required dependencies** (KiCad is optional)
3. **Additive only** - new commands under `agilev pcb`
4. **Evidence bundles extended** - old bundles still valid
5. **Risk levels reused** - L0-L4 apply to both software and hardware

## Testing Independence

### Software Tests (No PCB)
```bash
# Run software-only tests
pytest tests/test_state.py
pytest tests/test_openhands.py
pytest tests/test_task_context.py

# ✅ Pass without PCB installed
```

### PCB Tests (Optional)
```bash
# Run PCB tests
pytest tests/test_pcb.py
python test_pcb_manual.py

# ✅ Pass if PCB modules imported
# ⚠️ Skip if not available
```

## Deployment Scenarios

### Scenario 1: CI/CD Server (Software Only)
```dockerfile
FROM python:3.11
RUN pip install agilev
# ✅ Works - no KiCad needed
```

### Scenario 2: Developer Laptop (Software + PCB)
```bash
pip install agilev
brew install kicad  # Optional
# ✅ Works with or without KiCad
```

### Scenario 3: Build Server (Software + Optional PCB)
```yaml
# GitHub Actions
- name: Install Agile-V
  run: pip install agilev

- name: Install KiCad (if needed)
  run: |
    if [[ -f "*.kicad_sch" ]]; then
      sudo apt-get install kicad
    fi
```

## Summary

| Aspect | Status |
|--------|--------|
| **Software works without PCB** | ✅ YES |
| **PCB requires software** | ✅ YES (built on top) |
| **KiCad required** | ❌ NO (optional) |
| **Breaking changes** | ❌ NO |
| **New dependencies** | ❌ NO (pyyaml already used) |
| **Backward compatible** | ✅ YES |
| **Independent testing** | ✅ YES |

## Bottom Line

**Yes, the system works perfectly for software development without KiCad!**

The PCB features are a **pure extension** that:
- ✅ Don't break existing software workflows
- ✅ Don't require KiCad (except for `pcb erc` command)
- ✅ Don't add mandatory dependencies
- ✅ Can be ignored by software-only users
- ✅ Share the same evidence/risk framework

**Software developers** can use Agile-V without ever knowing PCB features exist.  
**Hardware developers** get additional PCB-specific tools built on the same foundation.  
**Full-stack IoT teams** get both, seamlessly integrated.
