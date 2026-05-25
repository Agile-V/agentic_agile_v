# Feature Brief

## Task ID

`EX-001`

## Title

Add device status endpoint.

## Objective

Expose read-only device health status for internal monitoring.

## User-visible behavior

Internal clients can query `/status` and receive current state, firmware version, and uptime.

## Non-goals

- No authentication changes.
- No firmware update behavior.
- No public API exposure.

## Affected modules

- `src/api/status.py`
- `tests/test_status.py`

## Acceptance criteria

- [ ] `/status` returns HTTP 200 for authenticated internal callers.
- [ ] Response includes `state`, `firmware_version`, and `uptime_s`.
- [ ] Unit tests cover normal and unavailable device state.

## Risk level

`L2`
