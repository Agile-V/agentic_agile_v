"""Tests for agilev.wiki.domains."""

from __future__ import annotations

from pathlib import Path

from agilev.wiki import constants
from agilev.wiki.domains import detect_domains, required_pages


def test_detect_domains_none_present(tmp_path: Path) -> None:
    domains = detect_domains(tmp_path)
    assert domains.pcb is False
    assert domains.firmware is False
    assert domains.embedded is False
    assert domains.any_hardware_adjacent is False


def test_detect_domains_pcb_only(tmp_path: Path) -> None:
    (tmp_path / "src/agilev/pcb").mkdir(parents=True)
    domains = detect_domains(tmp_path)
    assert domains.pcb is True
    assert domains.firmware is False
    assert domains.any_hardware_adjacent is False


def test_detect_domains_pcb_via_examples(tmp_path: Path) -> None:
    (tmp_path / "examples/pcb").mkdir(parents=True)
    domains = detect_domains(tmp_path)
    assert domains.pcb is True


def test_detect_domains_two_present_triggers_co_verification(tmp_path: Path) -> None:
    (tmp_path / "src/agilev/pcb").mkdir(parents=True)
    (tmp_path / "src/agilev/firmware").mkdir(parents=True)
    domains = detect_domains(tmp_path)
    assert domains.any_hardware_adjacent is True


def test_required_pages_base_only(tmp_path: Path) -> None:
    pages = required_pages(tmp_path)
    assert pages == list(constants.BASE_REQUIRED_PAGES)


def test_required_pages_with_all_domains(tmp_path: Path) -> None:
    (tmp_path / "src/agilev/pcb").mkdir(parents=True)
    (tmp_path / "src/agilev/firmware").mkdir(parents=True)
    (tmp_path / "src/agilev/embedded").mkdir(parents=True)

    pages = required_pages(tmp_path)

    assert "domains/pcb.md" in pages
    assert "domains/firmware.md" in pages
    assert "domains/embedded.md" in pages
    assert constants.CO_VERIFICATION_PAGE in pages
    for base in constants.BASE_REQUIRED_PAGES:
        assert base in pages
