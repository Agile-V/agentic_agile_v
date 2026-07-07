"""Domain detection for the OpenWiki knowledge layer.

Determines which optional domain knowledge pages (PCB, firmware, embedded)
are required for a given repository, based on the presence of the
corresponding backends. This mirrors how `agilev` already detects the PCB
and firmware/embedded subsystems elsewhere in the codebase (see
`src/agilev/pcb/`, `src/agilev/firmware/`, `src/agilev/embedded/`).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agilev.wiki import constants


@dataclass(frozen=True)
class DomainInventory:
    """Which optional domains are present in the repository."""

    pcb: bool
    firmware: bool
    embedded: bool

    @property
    def any_hardware_adjacent(self) -> bool:
        """True if two or more hardware-adjacent domains are present.

        Co-verification pages only make sense once there is more than one
        hardware-adjacent backend to co-verify.
        """
        return sum([self.pcb, self.firmware, self.embedded]) >= 2


def detect_domains(repo_root: Path) -> DomainInventory:
    """Detect which optional domains are present in the repository.

    Args:
        repo_root: Repository root directory.

    Returns:
        DomainInventory describing which domains were detected.
    """
    pcb = _any_exists(
        repo_root,
        [
            "src/agilev/pcb",
            "examples/pcb",
        ],
    )
    firmware = _any_exists(
        repo_root,
        [
            "src/agilev/firmware",
        ],
    )
    embedded = _any_exists(
        repo_root,
        [
            "src/agilev/embedded",
        ],
    )
    return DomainInventory(pcb=pcb, firmware=firmware, embedded=embedded)


def required_pages(repo_root: Path) -> list[str]:
    """Compute the full list of required wiki pages for this repository.

    Args:
        repo_root: Repository root directory.

    Returns:
        List of page paths (relative to `openwiki/`) that must exist.
    """
    domains = detect_domains(repo_root)
    pages = list(constants.BASE_REQUIRED_PAGES)

    if domains.pcb:
        pages.extend(constants.PCB_REQUIRED_PAGES)
    if domains.firmware:
        pages.extend(constants.FIRMWARE_REQUIRED_PAGES)
    if domains.embedded:
        pages.extend(constants.EMBEDDED_REQUIRED_PAGES)
    if domains.any_hardware_adjacent:
        pages.append(constants.CO_VERIFICATION_PAGE)

    return pages


def _any_exists(repo_root: Path, relative_paths: list[str]) -> bool:
    return any((repo_root / rel).exists() for rel in relative_paths)
