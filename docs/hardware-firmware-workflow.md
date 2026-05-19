# Hardware and Firmware Workflow

Hardware and firmware work is higher risk because generated artifacts may interact with physical systems.

## Required inputs

- board revision
- chip, MCU, SoC, or FPGA variant
- datasheet excerpts
- register map
- pinout
- clock tree
- memory map
- bus or protocol rules
- RTOS or bare-metal assumptions
- timing constraints
- power and thermal constraints
- safety states
- toolchain version
- simulator or emulator
- HIL setup
- rollback or recovery method

## Required evidence by default

- build log
- simulator or emulator output where available
- HIL log for hardware-facing behavior
- timing or memory analysis where relevant
- protocol trace where relevant
- rollback evidence for firmware deployment
- reviewer approval

## Rule

Never accept hardware or firmware changes based only on generated code and explanation.
