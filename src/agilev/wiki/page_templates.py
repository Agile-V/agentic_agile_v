"""Canonical content for required OpenWiki pages.

This module is the single source of truth for the Agile-V "required page"
skeletons that `agilev wiki init` scaffolds into `openwiki/`. The same
content is also materialized as static files under `templates/openwiki/`
in the repository for human browsing; keep both in sync if you edit this
module (the CLI reads from here, not from disk, so it works regardless of
whether the package is installed from a repo checkout or a wheel).

Each page is plain Markdown with a YAML front-matter block:

    ---
    title: <page title>
    sources:
      - <repo-relative path or directory this page documents>
    owners:
      - <team or skill responsible for keeping this page current>
    last_reviewed: null
    ---

`sources:` entries are used by `agilev.wiki.source_map` and
`agilev.wiki.freshness` to detect when a page may need a refresh.
"""

from __future__ import annotations


def _page(title: str, sources: list[str], owners: list[str], body: str) -> str:
    sources_yaml = "\n".join(f"  - {s}" for s in sources) or "  []"
    owners_yaml = "\n".join(f"  - {o}" for o in owners) or "  []"
    return (
        "---\n"
        f"title: {title}\n"
        f"sources:\n{sources_yaml}\n"
        f"owners:\n{owners_yaml}\n"
        "last_reviewed: null\n"
        "---\n\n"
        f"{body.strip()}\n"
    )


README = _page(
    title="Repository Knowledge Base",
    sources=["README.md", "AGENTS.md"],
    owners=["agile-v-core"],
    body="""
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
""",
)

ARCHITECTURE = _page(
    title="Architecture Overview",
    sources=["src/agilev", "ARCHITECTURE.md", "pyproject.toml"],
    owners=["agile-v-core"],
    body="""
# Architecture Overview

High-level map of the `agilev` runtime: state kernel, task context
resolution, control matrix enforcement, OpenHands integration, graph/impact
analysis, and the domain backends (PCB, firmware/embedded).

> Populate this page by running `openwiki --update` (or `openwiki -p`) once
> the OpenWiki CLI is configured with an inference provider. This
> Agile-V-scaffolded stub only guarantees the page exists and is tracked;
> it is not a substitute for a generated architecture description.
""",
)

ONBOARDING = _page(
    title="Agent & Contributor Onboarding",
    sources=["AGENTS.md", "CONTRIBUTIONS.md"],
    owners=["agile-v-core"],
    body="""
# Agent & Contributor Onboarding

Start here before making changes to this repository.

1. Read `AGENTS.md` at the repository root.
2. Read this knowledge base (`openwiki/`), starting with
   [Architecture](ARCHITECTURE.md).
3. Find or create a task brief under `.agentic-agile-v/tasks/`.
4. Run `agilev wiki status` to confirm the knowledge layer is fresh before
   relying on it for context.

> Populate this page with repository-specific onboarding steps via
> `openwiki --update`.
""",
)

DOMAIN_SOFTWARE = _page(
    title="Software / OpenHands Backend",
    sources=["src/agilev/openhands", "src/agilev/cli.py", "src/agilev/state.py"],
    owners=["agile-v-core"],
    body="""
# Software / OpenHands Backend

Describes the `agilev` CLI, state kernel, task context resolution, and the
OpenHands session/hook/evidence integration.

> Populate this page via `openwiki --update`.
""",
)

DOMAIN_PCB = _page(
    title="PCB Backend",
    sources=["src/agilev/pcb", "examples/pcb"],
    owners=["agile-v-core"],
    body="""
# PCB Backend

Describes the circuit IR, component index, validators, and KiCad CLI
integration for the (planned) PCB development backend.

**Manufacturing red line:** no AI-generated PCB design may be sent to
fabrication, customers, test subjects, or production without explicit human
electrical engineering approval and risk-appropriate evidence (see
`AGENTS.md`). This is a blocking gate, not a documentation nicety.

> Populate this page via `openwiki --update`.
""",
)

DOMAIN_FIRMWARE = _page(
    title="Firmware Backend",
    sources=["src/agilev/firmware"],
    owners=["agile-v-core"],
    body="""
# Firmware Backend

Describes the firmware/embedded build backend (PlatformIO integration, PCB
import, build evidence).

> Populate this page via `openwiki --update`.
""",
)

DOMAIN_EMBEDDED = _page(
    title="Embedded Systems Backend",
    sources=["src/agilev/embedded"],
    owners=["agile-v-core"],
    body="""
# Embedded Systems Backend

Describes the embedded system contract/CLI layer used for RTOS/microcontroller
targets.

> Populate this page via `openwiki --update`.
""",
)

CO_VERIFICATION = _page(
    title="Cross-Domain Co-Verification",
    sources=["src/agilev/pcb", "src/agilev/firmware", "src/agilev/embedded"],
    owners=["agile-v-core"],
    body="""
# Cross-Domain Co-Verification

Describes how the PCB, firmware, and embedded backends are verified
together: shared circuit IR, interface contracts between board and
firmware, and the combined evidence required before a hardware-adjacent
change can pass Gate 2 (see `AGENTS.md` testing expectations for PCB
design and firmware/hardware).

> Populate this page via `openwiki --update`.
""",
)

CI_AND_RELEASE = _page(
    title="CI, Evidence Bundles, Task Briefs, and Release Gates",
    sources=[
        ".github/workflows",
        "schemas/evidence_bundle.schema.json",
        "schemas/task_brief.schema.json",
    ],
    owners=["agile-v-core"],
    body="""
# CI, Evidence Bundles, Task Briefs, and Release Gates

Describes the task brief lifecycle (`.agentic-agile-v/tasks/AAV-XXXX/`),
evidence bundle schema (`schemas/evidence_bundle.schema.json`), the CI
quality gates (`.github/workflows/agentic-agile-v-gates.yml`), the
control matrix enforcement layer, and the risk-based (L0-L4) human
approval/release gates.

## Knowledge layer as evidence

`agilev wiki snapshot --task AAV-XXXX` writes a `knowledge_snapshot` object
into that task's evidence bundle, recording whether the knowledge layer was
valid and current at evidence-collection time.

> Populate the narrative sections of this page via `openwiki --update`.
""",
)

# Mapping of page path (relative to `openwiki/`) -> content.
PAGE_TEMPLATES: dict[str, str] = {
    "README.md": README,
    "ARCHITECTURE.md": ARCHITECTURE,
    "ONBOARDING.md": ONBOARDING,
    "domains/software.md": DOMAIN_SOFTWARE,
    "domains/pcb.md": DOMAIN_PCB,
    "domains/firmware.md": DOMAIN_FIRMWARE,
    "domains/embedded.md": DOMAIN_EMBEDDED,
    "co-verification.md": CO_VERIFICATION,
    "ci-and-release.md": CI_AND_RELEASE,
}
