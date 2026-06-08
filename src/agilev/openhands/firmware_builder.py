"""
Firmware builder integration for OpenHands.

Extends OpenHands session manager to support firmware development tasks.
"""

from pathlib import Path
from typing import Any

from agilev.firmware.platformio_backend import PlatformIOBackend
from agilev.openhands.session_manager import SessionConfig


class FirmwareBuilderConfig:
    """Configuration for firmware builder sessions."""

    def __init__(
        self,
        contract_path: Path,
        project_dir: Path,
        backend: str = "platformio",
        task_id: str | None = None,
    ):
        """Initialize firmware builder config.

        Args:
            contract_path: Path to hardware-firmware contract
            project_dir: Firmware project directory
            backend: Firmware backend (platformio, zephyr, etc.)
            task_id: Task identifier
        """
        self.contract_path = contract_path
        self.project_dir = project_dir
        self.backend = backend
        self.task_id = task_id


def create_firmware_session_config(
    fw_config: FirmwareBuilderConfig,
    base_session_config: SessionConfig | None = None,
) -> SessionConfig:
    """Create OpenHands session config for firmware tasks.

    Args:
        fw_config: Firmware builder configuration
        base_session_config: Base session config to extend

    Returns:
        SessionConfig for firmware development
    """
    if base_session_config:
        session_config = base_session_config
    else:
        session_config = SessionConfig()

    # Add firmware-specific context
    session_config.environment_vars = session_config.environment_vars or {}
    session_config.environment_vars.update(
        {
            "AGILEV_TASK_TYPE": "firmware",
            "AGILEV_FIRMWARE_BACKEND": fw_config.backend,
            "AGILEV_CONTRACT_PATH": str(fw_config.contract_path),
            "AGILEV_PROJECT_DIR": str(fw_config.project_dir),
        }
    )

    # Add firmware task context
    if fw_config.task_id:
        session_config.environment_vars["AGILEV_TASK_ID"] = fw_config.task_id

    # Set workspace to firmware project
    session_config.workspace = fw_config.project_dir

    return session_config


def initialize_firmware_project(fw_config: FirmwareBuilderConfig) -> dict[str, Any]:
    """Initialize firmware project before OpenHands session.

    Args:
        fw_config: Firmware builder configuration

    Returns:
        Initialization result with status and details
    """
    result = {
        "status": "success",
        "project_dir": str(fw_config.project_dir),
        "contract_path": str(fw_config.contract_path),
        "backend": fw_config.backend,
        "files_created": [],
    }

    try:
        # Create backend
        if fw_config.backend == "platformio":
            backend = PlatformIOBackend(fw_config.contract_path)
        else:
            raise ValueError(f"Unsupported backend: {fw_config.backend}")

        # Initialize project if it doesn't exist
        if not fw_config.project_dir.exists():
            backend.init_project(fw_config.project_dir)
            result["files_created"].append("project_structure")

            # Generate initial code from contract
            backend.generate_from_contract(fw_config.project_dir)
            result["files_created"].extend(
                [
                    "platformio.ini",
                    "include/board_contract.h",
                    "src/main.cpp",
                    "src/diagnostics.cpp",
                ]
            )

        result["initialized"] = True

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        result["initialized"] = False

    return result


def collect_firmware_session_evidence(
    fw_config: FirmwareBuilderConfig, session_id: str
) -> dict[str, Any]:
    """Collect evidence from firmware development session.

    Args:
        fw_config: Firmware builder configuration
        session_id: OpenHands session ID

    Returns:
        Evidence dictionary
    """
    evidence = {
        "session_id": session_id,
        "task_type": "firmware",
        "backend": fw_config.backend,
        "contract_path": str(fw_config.contract_path),
        "project_dir": str(fw_config.project_dir),
    }

    # Collect firmware-specific evidence
    try:
        if fw_config.backend == "platformio":
            backend = PlatformIOBackend(fw_config.contract_path)

            # Check if build exists
            firmware_bin = fw_config.project_dir / ".pio" / "build" / "target" / "firmware.bin"
            if firmware_bin.exists():
                evidence["build"] = {
                    "status": "passed",
                    "firmware_binary": str(firmware_bin),
                    "size_bytes": firmware_bin.stat().st_size,
                }
            else:
                evidence["build"] = {"status": "not_run"}

            # Collect test evidence
            # TODO: Check for test results

            # Collect full evidence bundle
            if fw_config.task_id:
                full_evidence = backend.collect_evidence(fw_config.project_dir, fw_config.task_id)
                evidence["evidence_bundle"] = full_evidence

    except Exception as e:
        evidence["error"] = str(e)

    return evidence
