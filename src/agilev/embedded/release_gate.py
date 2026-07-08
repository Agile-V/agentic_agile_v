"""
Embedded release gate.

Validates evidence bundles and enforces approval gates before release.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


class EmbeddedReleaseGate:
    """Release gate for embedded systems."""

    def __init__(self, project_root: Path):
        """Initialize release gate.

        Args:
            project_root: Project root directory
        """
        self.project_root = project_root
        self.contracts_dir = project_root / ".agentic-agile-v" / "contracts"
        self.evidence_dir = project_root / ".agentic-agile-v" / "evidence"
        self.config_path = project_root / "config" / "embedded" / "embedded_risk_levels.yaml"

    def load_risk_levels(self) -> dict[str, Any]:
        """Load risk level configuration.

        Returns:
            Risk levels configuration
        """
        if not self.config_path.exists():
            # Return default config
            return {
                "levels": {
                    "L0": {"evidence_required": ["documentation"]},
                    "L1": {"evidence_required": ["tests", "build_artifacts"]},
                    "L2": {"evidence_required": ["tests", "build_artifacts", "simulation"]},
                    "L3": {"evidence_required": ["tests", "build_artifacts", "simulation", "hil"]},
                    "L4": {
                        "evidence_required": [
                            "tests",
                            "build_artifacts",
                            "simulation",
                            "hil",
                            "human_ee_approval",
                        ]
                    },
                }
            }

        with open(self.config_path) as f:
            return yaml.safe_load(f)

    def load_evidence_bundle(self, task_id: str) -> dict[str, Any] | None:
        """Load evidence bundle for task.

        Args:
            task_id: Task identifier

        Returns:
            Evidence bundle or None
        """
        evidence_path = self.evidence_dir / f"{task_id}_evidence.json"

        if not evidence_path.exists():
            return None

        with open(evidence_path) as f:
            return json.load(f)

    def load_firmware_evidence(self, firmware_task_id: str) -> dict[str, Any] | None:
        """Load firmware evidence bundle.

        Args:
            firmware_task_id: Firmware task ID

        Returns:
            Firmware evidence or None
        """
        firmware_evidence_path = self.evidence_dir / f"{firmware_task_id}_firmware_evidence.json"

        if not firmware_evidence_path.exists():
            return None

        with open(firmware_evidence_path) as f:
            return json.load(f)

    def check_contract_hash(self, contract_path: Path, expected_hash: str) -> bool:
        """Check if contract hash matches expected.

        Args:
            contract_path: Path to contract
            expected_hash: Expected SHA-256 hash

        Returns:
            True if hash matches
        """
        if not contract_path.exists():
            return False

        sha256_hash = hashlib.sha256()
        with open(contract_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        actual_hash = sha256_hash.hexdigest()
        return actual_hash == expected_hash

    def is_evidence_stale(
        self,
        evidence: dict[str, Any],
        contract_path: Path,
    ) -> tuple[bool, str]:
        """Check if evidence is stale.

        Args:
            evidence: Evidence bundle
            contract_path: Contract file path

        Returns:
            Tuple of (is_stale, reason)
        """
        # Check if contract hash matches
        contract_hash = evidence.get("contract_hash")

        if not contract_hash:
            return True, "No contract hash in evidence"

        if not self.check_contract_hash(contract_path, contract_hash):
            return True, "Contract changed since evidence was collected"

        # Check timestamps
        evidence_timestamp = evidence.get("timestamp")
        if not evidence_timestamp:
            return True, "No timestamp in evidence"

        # If contract was modified after evidence was collected, it's stale
        if contract_path.exists():
            contract_mtime = contract_path.stat().st_mtime
            evidence_time = datetime.fromisoformat(evidence_timestamp).timestamp()

            if contract_mtime > evidence_time:
                return True, "Contract modified after evidence was collected"

        return False, ""

    def validate_evidence_for_risk_level(
        self,
        evidence: dict[str, Any],
        risk_level: str,
    ) -> list[str]:
        """Validate evidence meets risk level requirements.

        Args:
            evidence: Evidence bundle
            risk_level: Risk level (L0-L4)

        Returns:
            List of missing evidence items
        """
        risk_config = self.load_risk_levels()
        level_config = risk_config.get("levels", {}).get(risk_level, {})
        required = level_config.get("evidence_required", [])

        missing = []

        for req in required:
            if req == "documentation":
                if not evidence.get("documentation"):
                    missing.append("documentation")

            elif req == "tests":
                if not evidence.get("test_results"):
                    missing.append("test_results")
                elif not evidence["test_results"].get("passed"):
                    missing.append("passing_tests")

            elif req == "build_artifacts":
                if not evidence.get("build_artifacts"):
                    missing.append("build_artifacts")

            elif req == "simulation":
                if not evidence.get("simulation_results"):
                    missing.append("simulation_results")
                elif not evidence["simulation_results"].get("passed"):
                    missing.append("passing_simulation")

            elif req == "hil":
                if not evidence.get("hil_results"):
                    missing.append("hil_results")
                elif not evidence["hil_results"].get("passed"):
                    missing.append("passing_hil")

            elif req == "human_ee_approval":
                if not evidence.get("approvals", {}).get("electrical_engineer"):
                    missing.append("electrical_engineer_approval")

        return missing

    def check_gate(
        self,
        task_id: str,
        risk_level: str,
        firmware_task_id: str | None = None,
    ) -> dict[str, Any]:
        """Check release gate for task.

        Args:
            task_id: Task identifier
            risk_level: Risk level (L0-L4)
            firmware_task_id: Optional firmware task ID

        Returns:
            Gate check results
        """
        results = {
            "passed": True,
            "task_id": task_id,
            "risk_level": risk_level,
            "checks": [],
            "blockers": [],
            "warnings": [],
        }

        # Load evidence
        evidence = self.load_evidence_bundle(task_id)

        if not evidence:
            results["passed"] = False
            results["blockers"].append(f"No evidence bundle found for task {task_id}")
            return results

        # Check for stale evidence
        contract_path = self.contracts_dir / "hardware_firmware_contract.yaml"
        is_stale, stale_reason = self.is_evidence_stale(evidence, contract_path)

        if is_stale:
            results["passed"] = False
            results["blockers"].append(f"Evidence is stale: {stale_reason}")

        results["checks"].append(
            {
                "name": "Evidence freshness",
                "passed": not is_stale,
                "message": "Evidence is current" if not is_stale else stale_reason,
            }
        )

        # Validate evidence meets risk level requirements
        missing_evidence = self.validate_evidence_for_risk_level(evidence, risk_level)

        if missing_evidence:
            results["passed"] = False
            for item in missing_evidence:
                results["blockers"].append(f"Missing required evidence: {item}")

        results["checks"].append(
            {
                "name": f"Risk level {risk_level} requirements",
                "passed": not missing_evidence,
                "message": (
                    "All evidence present"
                    if not missing_evidence
                    else f"Missing: {', '.join(missing_evidence)}"
                ),
            }
        )

        # Check firmware evidence if provided
        if firmware_task_id:
            firmware_evidence = self.load_firmware_evidence(firmware_task_id)

            if not firmware_evidence:
                results["warnings"].append(f"No firmware evidence found for {firmware_task_id}")
            else:
                results["checks"].append(
                    {
                        "name": "Firmware evidence",
                        "passed": True,
                        "message": f"Firmware evidence available for {firmware_task_id}",
                    }
                )

        return results

    def save_gate_results(
        self,
        results: dict[str, Any],
        output_path: Path,
    ) -> None:
        """Save gate check results.

        Args:
            results: Gate results
            output_path: Output path
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)
