# Bug Brief

## Task ID

`EX-002`

## Title

Fix timeout handling in device polling.

## Observed behavior

Polling blocks longer than configured timeout under device disconnect.

## Expected behavior

Polling returns timeout error within configured limit.

## Reproduction steps

1. Start device service.
2. Disconnect simulated device.
3. Run polling call with 500 ms timeout.

## Regression test requirement

- [ ] Add failing regression test before fix.

## Risk level

`L2`
