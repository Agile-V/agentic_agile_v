"""Scaffolds the `openwiki/` required page skeletons.

This is intentionally independent of the real `openwiki` CLI: it writes
Agile-V's minimal required-page skeletons (see `page_templates.py`) so that
`agilev wiki validate` never fails on a freshly-cloned repository, and so
CI/tests never need network access or an LLM API key. The real `openwiki`
CLI (invoked via `agilev.wiki.runner.OpenWikiRunner`, optionally, with
`--run-openwiki`) is what fills these pages in with real generated content.
"""

from __future__ import annotations

from pathlib import Path

from agilev.wiki import constants, domains
from agilev.wiki.page_templates import PAGE_TEMPLATES


def scaffold_wiki(repo_root: Path, force: bool = False) -> list[Path]:
    """Write required page skeletons into `openwiki/`.

    Args:
        repo_root: Repository root directory.
        force: If True, overwrite existing pages. If False (default),
            existing pages are left untouched.

    Returns:
        List of paths that were written (created or overwritten).
    """
    wiki_dir = repo_root / constants.WIKI_DIR
    required = domains.required_pages(repo_root)
    written: list[Path] = []

    for page in required:
        content = PAGE_TEMPLATES.get(page)
        if content is None:
            # No canonical template for this page (shouldn't normally
            # happen since PAGE_TEMPLATES covers every constant); skip
            # rather than fail scaffolding for unrelated pages.
            continue

        page_path = wiki_dir / page
        if page_path.exists() and not force:
            continue

        page_path.parent.mkdir(parents=True, exist_ok=True)
        page_path.write_text(content, encoding="utf-8")
        written.append(page_path)

    return written
