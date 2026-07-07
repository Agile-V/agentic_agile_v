"""Tests for agilev.wiki.scaffolder."""

from __future__ import annotations

from pathlib import Path

from agilev.wiki import constants
from agilev.wiki.scaffolder import scaffold_wiki


def test_scaffold_wiki_creates_base_required_pages(tmp_path: Path) -> None:
    written = scaffold_wiki(tmp_path)

    wiki_dir = tmp_path / constants.WIKI_DIR
    for page in constants.BASE_REQUIRED_PAGES:
        assert (wiki_dir / page).exists()

    assert len(written) == len(constants.BASE_REQUIRED_PAGES)


def test_scaffold_wiki_does_not_overwrite_without_force(tmp_path: Path) -> None:
    scaffold_wiki(tmp_path)
    readme = tmp_path / constants.WIKI_DIR / "README.md"
    readme.write_text("custom content", encoding="utf-8")

    written = scaffold_wiki(tmp_path, force=False)

    assert readme.read_text(encoding="utf-8") == "custom content"
    assert readme not in written


def test_scaffold_wiki_overwrites_with_force(tmp_path: Path) -> None:
    scaffold_wiki(tmp_path)
    readme = tmp_path / constants.WIKI_DIR / "README.md"
    readme.write_text("custom content", encoding="utf-8")

    scaffold_wiki(tmp_path, force=True)

    assert readme.read_text(encoding="utf-8") != "custom content"


def test_scaffold_wiki_includes_pcb_page_when_domain_present(tmp_path: Path) -> None:
    (tmp_path / "src/agilev/pcb").mkdir(parents=True)
    scaffold_wiki(tmp_path)

    assert (tmp_path / constants.WIKI_DIR / "domains" / "pcb.md").exists()
    assert not (tmp_path / constants.WIKI_DIR / "domains" / "firmware.md").exists()
