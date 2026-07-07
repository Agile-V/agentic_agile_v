"""Constants for the Agile-V OpenWiki knowledge-layer integration.

This module defines the on-disk locations and the required page structure
for the `openwiki/` documentation tree that the external `openwiki` CLI
(https://github.com/langchain-ai/openwiki) generates and maintains, plus
the `.agile-v/wiki/` runtime metadata directory that Agile-V layers on top
of it (manifest, source map, freshness, and validation records).
"""

from __future__ import annotations

# Directory (relative to repo root) where the `openwiki` CLI writes generated
# documentation. This matches upstream `openwiki`'s default behavior: it
# creates `openwiki/` when no wiki exists, and refreshes it in place
# otherwise.
WIKI_DIR = "openwiki"

# Directory (relative to repo root) where Agile-V stores its own tracking
# metadata about the wiki: manifest, source map, freshness, and validation
# results. Lives alongside the other `.agile-v/*` subsystems (impact,
# traceability, understanding).
STATE_DIR = ".agile-v/wiki"

MANIFEST_FILENAME = "manifest.json"
SOURCE_MAP_FILENAME = "source_map.json"
FRESHNESS_FILENAME = "freshness.json"
VALIDATION_FILENAME = "validation.json"

# Log directory for captured `openwiki` subprocess output.
LOGS_DIRNAME = "logs"

SCHEMA_VERSION = "1.0.0"

# Pages that are always required, regardless of repository domain mix.
# Paths are relative to WIKI_DIR.
BASE_REQUIRED_PAGES: tuple[str, ...] = (
    "README.md",
    "ARCHITECTURE.md",
    "ONBOARDING.md",
    "domains/software.md",
    "ci-and-release.md",
)

# Domain-specific pages, only required when the corresponding domain is
# detected in the repository (see agilev.wiki.domains).
PCB_REQUIRED_PAGES: tuple[str, ...] = ("domains/pcb.md",)
FIRMWARE_REQUIRED_PAGES: tuple[str, ...] = ("domains/firmware.md",)
EMBEDDED_REQUIRED_PAGES: tuple[str, ...] = ("domains/embedded.md",)

# Required once any two or more hardware-adjacent domains (pcb, firmware,
# embedded) are present, since these pages exist specifically to describe how
# those backends are co-verified together.
CO_VERIFICATION_PAGE = "co-verification.md"

# Default staleness threshold (in days) before `agilev wiki validate` emits a
# warning (not a failure) about a page being out of date relative to its
# declared source files.
DEFAULT_STALENESS_WARNING_DAYS = 30
