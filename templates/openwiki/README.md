---
title: Repository Knowledge Base
sources:
  - README.md
  - AGENTS.md
owners:
  - agile-v-core
last_reviewed: null
---

# Repository Knowledge Base

This directory is the Agile-V repository knowledge layer, generated and
maintained by [OpenWiki](https://github.com/langchain-ai/openwiki) and
validated by `agilev wiki validate`.

## Index

- [Architecture](ARCHITECTURE.md)
- [Onboarding](ONBOARDING.md)
- [Software / OpenHands backend](domains/software.md)
- [PCB backend](domains/pcb.md) (if present)
- [Firmware backend](domains/firmware.md) (if present)
- [Embedded backend](domains/embedded.md) (if present)
- [Co-verification across hardware domains](co-verification.md) (if present)
- [CI, evidence bundles, task briefs, and release gates](ci-and-release.md)

## Keeping this current

- `openwiki --update` regenerates page content from the current repository.
- `agilev wiki update` recomputes the Agile-V manifest/source-map/freshness
  records in `.agile-v/wiki/` from whatever is currently on disk here.
- `agilev wiki validate` fails CI if a required page is missing or if this
  directory has changed without a matching `agilev wiki update`.
