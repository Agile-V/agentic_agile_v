"""
Firmware evidence adapter for OpenHands integration.

Extends evidence adapter to handle firmware-specific evidence bundles.
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from agilev.firmware.platformio_backend import PlatformIOBackend


class FirmwareEvidenceAdapter:
    """Adapter for firmware evidence bundles in OpenHands sessions."""

    def __init__(self, task_id: str, project_dir: Path, contract_path: Path):
        """Initialize firmware evidence adapter.

        Args:
            task_id: Firmware task ID
            project_dir: Firmware project directory
            contract_path: Path to hardware-firmware contract
        """
        self.task_id = task_id
        self.project_dir = project_dir
        self.contract_path = contract_path

    def collect_firmware_evidence(
        self, session_id: str, backend: str = "platformio"
    ) -> dict[str, Any]:
        """Collect firmware evidence from session.

        Args:
            session_id: OpenHands session ID
            backend: Firmware backend type

        Returns:
            Firmware evidence bundle
        """
        evidence = {
            "task_id": self.task_id,
            "artifact_type": "firmware",
            "session_id": session_id,
            "collected_at": datetime.now(UTC).isoformat(),
            "project_dir": str(self.project_dir),
            "contract_path": str(self.contract_path),
            "backend": backend,
        }

        # Use backend to collect evidence
        if backend == "platformio":
            backend_instance = PlatformIOBackend(self.contract_path)
            backend_evidence = backend_instance.collect_evidence(self.project_dir, self.task_id)
            evidence.update(backend_evidence)

        # Add firmware-specific metadata
        evidence["firmware_files"] = self._collect_firmware_files()
        evidence["contract_validation"] = self._validate_contract_compliance()

        return evidence

    def _collect_firmware_files(self) -> list[str]:
        """Collect list of firmware source files.

        Returns:
            List of firmware file paths
        """
        files = []

        # Collect source files
        src_dir = self.project_dir / "src"
        if src_dir.exists():
            for ext in ["*.cpp", "*.c", "*.h"]:
                files.extend([str(f.relative_to(self.project_dir)) for f in src_dir.rglob(ext)])

        # Collect header files
        include_dir = self.project_dir / "include"
        if include_dir.exists():
            for ext in ["*.h", "*.hpp"]:
                files.extend([str(f.relative_to(self.project_dir)) for f in include_dir.rglob(ext)])

        return sorted(files)

    def _validate_contract_compliance(self) -> dict[str, Any]:
        """Validate firmware complies with hardware-firmware contract.

        Returns:
            Validation result dictionary
        """
        validation = {
            "status": "unknown",
            "checks": [],
        }

        # Check if board_contract.h exists
        board_contract = self.project_dir / "include" / "board_contract.h"
        if board_contract.exists():
            validation["checks"].append({
                "name": "board_contract_h_exists",
                "status": "passed",
            })
        else:
            validation["checks"].append({
                "name": "board_contract_h_exists",
                "status": "failed",
                "message": "board_contract.h not found",
            })

        # Check if contract file is referenced
        if board_contract.exists():
            content = board_contract.read_text()
            if "DO NOT EDIT" in content and "hardware-firmware contract" in content:
                validation["checks"].append({
                    "name": "contract_header_present",
                    "status": "passed",
                })
            else:
                validation["checks"].append({
                    "name": "contract_header_present",
                    "status": "warning",
                    "message": "Contract header may be modified",
                })

        # Determine overall status
        failed = any(c["status"] == "failed" for c in validation["checks"])
        if failed:
            validation["status"] = "failed"
        elif validation["checks"]:
            validation["status"] = "passed"

        return validation

    def save_evidence_bundle(self, evidence: dict[str, Any], output_path: Path) -> None:
        """Save firmware evidence bundle to file.

        Args:
            evidence: Evidence dictionary
            output_path: Path to save evidence bundle
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(evidence, f, indent=2)

    def merge_with_openhands_evidence(
        self, firmware_evidence: dict[str, Any], openhands_evidence: dict[str, Any]
    ) -> dict[str, Any]:
        """Merge firmware evidence with OpenHands session evidence.

        Args:
            firmware_evidence: Firmware-specific evidence
            openhands_evidence: OpenHands session evidence

        Returns:
            Combined evidence bundle
        """
        combined = {
            "task_id": self.task_id,
            "artifact_type": "firmware_with_openhands",
            "created_at": datetime.now(UTC).isoformat(),
            "firmware_evidence": firmware_evidence,
            "openhands_evidence": openhands_evidence,
        }

        # Extract key metadata to top level
        combined["session_id"] = firmware_evidence.get("session_id")
        combined["risk_level"] = firmware_evidence.get("risk_level", "L2")
        combined["backend"] = firmware_evidence.get("backend")
        combined["project_dir"] = firmware_evidence.get("project_dir")

        # Combine traceability
        fw_trace = firmware_evidence.get("traceability", {})
        oh_trace = openhands_evidence.get("traceability", {})

        combined["traceability"] = {
            "requirements": fw_trace.get("requirements", []),
            "pcb_nets": fw_trace.get("pcb_nets", []),
            "firmware_files": fw_trace.get("firmware_files", []),
            "changed_files": oh_trace.get("changed_files", []),
        }

        return combined
