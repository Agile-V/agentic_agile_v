"""Agile-V Control Matrix loader, validator, and resolver.

Implements: REQ-CM-001 (control matrix loader), REQ-CM-002 (semantic validator),
            REQ-CM-003 (control resolver)
"""

from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml

logger = logging.getLogger(__name__)

RiskLevel = Literal["L0", "L1", "L2", "L3", "L4"]
Decision = Literal["allow", "deny", "require_human_gate", "warn"]

RISK_ORDER: dict[str, int] = {"L0": 0, "L1": 1, "L2": 2, "L3": 3, "L4": 4}

#: Owner fields that must not be placeholders in active controls.
REQUIRED_OWNER_KEYS = ("business_owner", "technical_owner", "security_owner", "reviewer")

#: Values treated as unresolved owner placeholders (for owners and model fields).
PLACEHOLDER_VALUES = frozenset({"TBD", "unknown", "approved_vendor", "approved_model", "", None})


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
        result: dict[str, Any] = {
            "decision": self.decision,
            "control_id": self.control_id,
            "reason": self.reason,
        }
        if self.required_gate is not None:
            result["required_gate"] = self.required_gate
        if self.approver_role is not None:
            result["approver_role"] = self.approver_role
        if self.evidence_ref is not None:
            result["evidence_ref"] = self.evidence_ref
        return result


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
        - No requires_gate/forbidden tool overlap per control.
        - minimum_risk_level is a recognised risk level when present.
        - Active controls have no unresolved owner or model placeholder values.
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

            # Tool overlap checks
            tools = control.get("tools", {})
            allowed = set(tools.get("allowed", []))
            forbidden = set(tools.get("forbidden", []))
            requires_gate = set(tools.get("requires_gate", []))
            overlap_af = allowed & forbidden
            if overlap_af:
                raise ControlMatrixError(
                    f"Control {cid!r} has overlapping tools in allowed and forbidden: {sorted(overlap_af)}"
                )
            overlap_gf = requires_gate & forbidden
            if overlap_gf:
                raise ControlMatrixError(
                    f"Control {cid!r} has overlapping tools in requires_gate and forbidden: {sorted(overlap_gf)}"
                )

            # minimum_risk_level validity
            min_risk = control.get("minimum_risk_level")
            if min_risk is not None and min_risk not in RISK_ORDER:
                raise ControlMatrixError(
                    f"Control {cid!r} has invalid minimum_risk_level: {min_risk!r}. "
                    f"Expected one of: {sorted(RISK_ORDER)}"
                )

            # Placeholder checks for active controls
            if control.get("status") == "active":
                owner = control.get("owner", {})
                for key in REQUIRED_OWNER_KEYS:
                    val = owner.get(key)
                    if val in PLACEHOLDER_VALUES:
                        raise ControlMatrixError(
                            f"Active control {cid!r} has unresolved owner field: {key}={val!r}. "
                            "Replace all placeholder values before enabling enforcement."
                        )
                model = control.get("model", {})
                for key in ("vendor", "model_name"):
                    val = model.get(key)
                    if val in PLACEHOLDER_VALUES:
                        raise ControlMatrixError(
                            f"Active control {cid!r} has unresolved model field: {key}={val!r}. "
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

        Resolution uses first-match semantics: the first active control whose
        ``applies_to`` scope and ``minimum_risk_level`` all match wins.  Order
        your controls from most-specific to least-specific in the YAML.

        Raises ``ControlMatrixError`` when no control matches.
        """
        if risk_level not in RISK_ORDER:
            warnings.warn(
                f"Unrecognised risk level {risk_level!r}; treating as L0. "
                f"Valid levels: {sorted(RISK_ORDER)}",
                stacklevel=2,
            )

        all_controls = self.data.get("controls", [])
        active = [c for c in all_controls if c.get("status") == "active"]
        skipped_statuses: list[str] = [
            c.get("status", "unknown") for c in all_controls if c.get("status") != "active"
        ]

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
                logger.debug(
                    "Resolved control %r for task_type=%r risk=%r mode=%r skill=%r",
                    control["id"],
                    task_type,
                    risk_level,
                    agent_mode,
                    skill,
                )
                return control

        skipped_note = (
            f" ({len(skipped_statuses)} control(s) skipped due to status: "
            + ", ".join(sorted(set(skipped_statuses)))
            + ")"
            if skipped_statuses
            else ""
        )
        raise ControlMatrixError(
            f"No matching active control for task_type={task_type!r}, "
            f"risk_level={risk_level!r}, agent_mode={agent_mode!r}, skill={skill!r}."
            f"{skipped_note} "
            "Ensure at least one active control covers this combination."
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"ControlMatrix(version={self.version!r}, "
            f"source={self.source_path!r}, "
            f"controls={len(self.data.get('controls', []))})"
        )

    @property
    def version(self) -> str:
        v = self.data.get("version")
        if v is None:
            warnings.warn(
                f"Control matrix at {self.source_path} has no 'version' field; "
                "evidence bundles will record policy_version='unknown'.",
                stacklevel=2,
            )
            return "unknown"
        return str(v)

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
