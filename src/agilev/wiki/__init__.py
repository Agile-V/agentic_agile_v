"""Agile-V OpenWiki knowledge-layer integration.

Wraps the external `openwiki` CLI (https://github.com/langchain-ai/openwiki)
with Agile-V tracking: a manifest of generated pages, a source map linking
pages to the code/config they document, freshness detection, structural
validation, and evidence bundle integration via `knowledge_snapshot`.

See `agilev wiki --help` for the CLI surface, and
`docs/integrations/openwiki.md` for the full integration design.
"""

from __future__ import annotations

from agilev.wiki.domains import DomainInventory, detect_domains, required_pages
from agilev.wiki.errors import WikiError, WikiNotInitializedError, WikiRunnerError
from agilev.wiki.freshness import FreshnessReport, compute_freshness
from agilev.wiki.manifest import WikiManifest, build_manifest, load_manifest, save_manifest
from agilev.wiki.runner import OpenWikiRunner
from agilev.wiki.snapshot import build_knowledge_snapshot, write_snapshot_to_task
from agilev.wiki.validator import WikiValidationResult
from agilev.wiki.validator import validate as validate_wiki

__all__ = [
    "DomainInventory",
    "detect_domains",
    "required_pages",
    "WikiError",
    "WikiNotInitializedError",
    "WikiRunnerError",
    "FreshnessReport",
    "compute_freshness",
    "WikiManifest",
    "build_manifest",
    "load_manifest",
    "save_manifest",
    "OpenWikiRunner",
    "build_knowledge_snapshot",
    "write_snapshot_to_task",
    "WikiValidationResult",
    "validate_wiki",
]
