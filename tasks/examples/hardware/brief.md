# Hardware or Firmware Brief

## Task ID

`EX-003`

## Title

Adjust SPI sensor initialization delay.

## Objective

Increase initialization delay after sensor reset to satisfy datasheet timing.

## Board and device context

- board revision: A2
- MCU: example MCU
- sensor: example SPI sensor
- toolchain: example gcc

## Constraints

- Do not change pinout.
- Do not change SPI clock.
- Keep boot time below limit.

## Acceptance criteria

- [ ] Firmware builds.
- [ ] Simulator boot test passes.
- [ ] HIL sensor init test passes.
- [ ] Timing trace attached.

## Risk level

`L4`
