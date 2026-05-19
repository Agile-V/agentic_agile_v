# Agent Plan

## Task ID

`EX-001`

## Repository inspection summary

Status-related API routes are isolated. The endpoint can be added without changing authentication.

## Proposed changes

- Add a read-only status handler.
- Add unit tests for normal and unavailable device states.

## Test strategy

- Run status endpoint unit tests.
- Run full API test subset.

## Risk classification

`L2` because it is production code but read-only and internal.
