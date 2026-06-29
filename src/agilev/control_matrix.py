"""Agile-V Control Matrix loader, validator, and resolver.

Implements: REQ-CM-001 (control matrix loader), REQ-CM-002 (semantic validator),
            REQ-CM-003 (control resolver)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml

RiskLevel = Literal["L0", "L1", "L2", "L3", "L4"]
Decision = Literal["allow", "deny", "require_human_gate", "warn"]

RISK_ORDER: dict[str, int] = {"L0": 0, "L1": 1, "L2": 2, "L3": 3, "L4": 4}

#: Owner fields that must not be placeholders in active controls.
REQUIRED_OWNER_KEYS = ("business_owner", "technical_owner", "security_owner", "reviewer")

#: Values treated as unresolved owner placeholders.
PLACEHOLDER_VALUES = frozenset({"TBD", "unknown", "", None})


@dataclass(frozen=True)
class ControlDecision:
    """Result of a single control matrix check."""

    decision: Decision
    control_id: str
    reason: str
    required_gate: str | None = None
    approver_role: str | None = None
    evidence_ref: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "control_id": self.control_id,
            "reason": self.reason,
            "required_gate": self.required_gate,
            "approver_role": self.approver_role,
            "evidence_ref": self.evidence_ref,
        }


class ControlMatrixError(RuntimeError):
    """Raised when the control matrix is invalid or cannot be loaded."""


class ControlMatrix:
    """Loaded and validated control matrix.

    Load order:
    1. ``<root>/.agile-v/CONTROL_MATRIX.yaml``
    2. ``<root>/config/control_matrix.yaml``
    """

    def __init__(self, data: dict[str, Any], source_path: Path) -> None:
        self.data = data
        self.source_path = source_path

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def load(cls, root: Path) -> "ControlMatrix":
        """Load the control matrix from the canonical search path.

        Raises ``ControlMatrixError`` when no matrix is found.
        """
        candidates = [
            root / ".agile-v" / "CONTROL_MATRIX.yaml",
            root / "config" / "control_matrix.yaml",
        ]
        for path in candidates:
            if path.exists():
                with path.open("r", encoding="utf-8") as handle:
                    data = yaml.safe_load(handle) or {}
                matrix = cls(data=data, source_path=path)
                matrix.validate_semantics()
                return matrix
        raise ControlMatrixError(
            "No control matrix found. Expected one of: " + ", ".join(str(c) for c in candidates)
        )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_semantics(self) -> None:
        """Run semantic checks beyond JSON Schema.

        Checks:
        - At least one control entry exists.
        - No duplicate control IDs.
        - No allowed/forbidden tool overlap per control.
        - Active controls have no unresolved owner placeholders.
        """
        controls = self.data.get("controls", [])
        if not controls:
            raise ControlMatrixError("Control matrix has no controls.")

        seen_ids: set[str] = set()
        for control in controls:
            cid = control.get("id", "<missing-id>")
            if cid in seen_ids:
                raise ControlMatrixError(f"Duplicate control id: {cid!r}")
            seen_ids.add(cid)

            # Tool overlap check
            tools = control.get("tools", {})
            allowed = set(tools.get("allowed", []))
            forbidden = set(tools.get("forbidden", []))
            overlap = allowed & forbidden
            if overlap:
                raise ControlMatrixError(
                    f"Control {cid!r} has overlapping tools in allowed and forbidden: {sorted(overlap)}"
                )

            # Owner placeholder check for active controls
            if control.get("status") == "active":
                owner = control.get("owner", {})
                for key in REQUIRED_OWNER_KEYS:
                    val = owner.get(key)
                    if val in PLACEHOLDER_VALUES:
                        raise ControlMatrixError(
                            f"Active control {cid!r} has unresolved owner field: {key}={val!r}. "
                            "Replace all placeholder values before enabling enforcement."
                        )

    # ------------------------------------------------------------------
    # Resolution
    # ------------------------------------------------------------------

    def resolve(
        self,
        task_type: str,
        risk_level: RiskLevel,
        agent_mode: str,
        skill: str | None = None,
    ) -> dict[str, Any]:
        """Return the first active control that matches the given context.

        Raises ``ControlMatrixError`` when no control matches.
        """
        active = [c for c in self.data["controls"] if c.get("status") == "active"]
        for control in active:
            applies = control.get("applies_to", {})
            task_types = applies.get("task_types", [])
            agent_modes = applies.get("agent_modes", [])
            skills = applies.get("skills", [])
            min_risk = control.get("minimum_risk_level", "L0")

            task_ok = "*" in task_types or task_type in task_types
            mode_ok = "*" in agent_modes or agent_mode in agent_modes
            skill_ok = skill is None or "*" in skills or skill in skills
            risk_ok = RISK_ORDER.get(risk_level, 0) >= RISK_ORDER.get(min_risk, 0)

            if task_ok and mode_ok and skill_ok and risk_ok:
                return control

        raise ControlMatrixError(
            f"No matching active control for task_type={task_type!r}, "
            f"risk_level={risk_level!r}, agent_mode={agent_mode!r}, skill={skill!r}. "
            "Ensure at least one active control covers this combination."
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def version(self) -> str:
        return str(self.data.get("version", "unknown"))

    @property
    def default_fail_mode(self) -> str:
        return str(self.data.get("default_fail_mode", "closed"))

    def summary(self) -> str:
        controls = self.data.get("controls", [])
        active = sum(1 for c in controls if c.get("status") == "active")
        return (
            f"Control matrix v{self.version} loaded from {self.source_path} — "
            f"{len(controls)} control(s), {active} active, "
            f"fail_mode={self.default_fail_mode!r}"
        )
