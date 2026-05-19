# Hardware or Firmware Brief

## Task ID

`AAV-000`

## Title

Short hardware or firmware task title.

## Objective

What hardware-facing behavior should change?

## Board and device context

- board revision:
- chip/MCU/SoC/FPGA:
- toolchain version:
- firmware version:
- RTOS or bare-metal:

## Required technical context

- datasheet excerpts:
- register map:
- pinout:
- clock tree:
- memory map:
- bus/protocol:
- timing constraints:
- power/thermal constraints:
- safety states:

## Non-goals

What must not change?

## Acceptance criteria

- [ ] Build passes
- [ ] Simulation/emulation passes
- [ ] HIL test passes, if applicable
- [ ] Timing/memory/protocol evidence attached
- [ ] Rollback path verified

## Risk level

Usually `L3` or `L4`.

## Required evidence

- build log:
- simulator log:
- HIL log:
- timing or protocol trace:
- traceability matrix:
- reviewer approval:

## Rollback or recovery plan

How can the device recover from failed deployment?
