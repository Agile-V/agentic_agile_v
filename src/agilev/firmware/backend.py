"""
Firmware backend base class.

Defines common interface for firmware backends (PlatformIO, Zephyr, etc.).
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class FirmwareBackend(ABC):
    """Base class for firmware backends."""

    def __init__(self, contract_path: Path):
        """Initialize backend with hardware-firmware contract.

        Args:
            contract_path: Path to hardware-firmware contract YAML
        """
        self.contract_path = contract_path

    @abstractmethod
    def init_project(self, project_dir: Path) -> None:
        """Initialize firmware project structure.

        Args:
            project_dir: Directory to create project in
        """
        pass

    @abstractmethod
    def generate_from_contract(self, project_dir: Path) -> None:
        """Generate firmware code from hardware-firmware contract.

        Args:
            project_dir: Project directory
        """
        pass

    @abstractmethod
    def build(self, project_dir: Path) -> tuple[bool, str]:
        """Build firmware project.

        Args:
            project_dir: Project directory

        Returns:
            Tuple of (success, output)
        """
        pass

    @abstractmethod
    def run_host_tests(self, project_dir: Path) -> tuple[bool, str]:
        """Run host-based unit tests.

        Args:
            project_dir: Project directory

        Returns:
            Tuple of (success, output)
        """
        pass

    @abstractmethod
    def collect_evidence(self, project_dir: Path, task_id: str) -> dict[str, Any]:
        """Collect evidence bundle for firmware.

        Args:
            project_dir: Project directory
            task_id: Firmware task ID

        Returns:
            Evidence bundle dictionary
        """
        pass
