"""Agile-V Control Matrix runtime enforcement checks.

Implements: REQ-CM-004 (data class check), REQ-CM-005 (tool check),
            REQ-CM-006 (model/vendor check), REQ-CM-007 (cost check),
            REQ-CM-008 (rollback check)
"""

from __future__ import annotations

from typing import Any

from agilev.control_matrix import ControlDecision


# ---------------------------------------------------------------------------
# Data class check
# ---------------------------------------------------------------------------


def check_data_class(control: dict[str, Any], data_class: str) -> ControlDecision:
    """Check whether *data_class* is permitted under *control*.

    Returns:
        ``deny`` — data class is explicitly forbidden.
        ``require_human_gate`` — data class is unknown and policy requires a gate.
        ``allow`` — data class is explicitly allowed.
    """
    cfg = control["data_class"]
    cid = control["id"]

    if data_class in cfg.get("forbidden", []):
        return ControlDecision(
            "deny",
            cid,
            f"Forbidden data class: {data_class!r}",
        )

    if data_class not in cfg.get("allowed", []):
        action = cfg.get("unknown_action", "deny")
        if action == "require_human_gate":
            return ControlDecision(
                "require_human_gate",
                cid,
                f"Unknown data class requires Human Gate: {data_class!r}",
                required_gate="G1",
                approver_role="security_owner",
            )
        # deny by default
        return ControlDecision(
            "deny",
            cid,
            f"Unknown data class denied: {data_class!r}",
        )

    return ControlDecision("allow", cid, f"Data class allowed: {data_class!r}")


# ---------------------------------------------------------------------------
# Tool check
# ---------------------------------------------------------------------------


def check_tool(control: dict[str, Any], tool_class: str) -> ControlDecision:
    """Check whether *tool_class* is permitted under *control*.

    Returns:
        ``deny`` — tool is forbidden or not allowlisted.
        ``require_human_gate`` — tool requires gate approval.
        ``allow`` — tool is explicitly allowed.
    """
    tools = control["tools"]
    cid = control["id"]

    if tool_class in tools.get("forbidden", []):
        return ControlDecision(
            "deny",
            cid,
            f"Forbidden tool: {tool_class!r}",
        )

    if tool_class in tools.get("requires_gate", []):
        return ControlDecision(
            "require_human_gate",
            cid,
            f"Tool requires Human Gate approval: {tool_class!r}",
            required_gate="G2",
            approver_role="technical_owner",
        )

    if tool_class not in tools.get("allowed", []):
        return ControlDecision(
            "deny",
            cid,
            f"Tool not in allowlist: {tool_class!r}",
        )

    return ControlDecision("allow", cid, f"Tool allowed: {tool_class!r}")


# ---------------------------------------------------------------------------
# Model / vendor check
# ---------------------------------------------------------------------------


def check_model(
    control: dict[str, Any],
    vendor: str,
    model_name: str,
    data_class: str,
) -> ControlDecision:
    """Check whether *vendor*/*model_name* is permitted for *data_class*.

    Returns:
        ``deny`` — vendor or model is not allowed.
        ``require_human_gate`` — vendor review required for this data class.
        ``allow`` — model is permitted.
    """
    model = control["model"]
    cid = control["id"]

    allowed_vendor = model.get("vendor", "")
    fallback = model.get("fallback_model")
    external_ok = model.get("allow_external_vendor", False)

    if vendor != allowed_vendor and not external_ok:
        return ControlDecision(
            "deny",
            cid,
            f"Vendor not allowed: {vendor!r} (expected {allowed_vendor!r})",
        )

    allowed_model = model.get("model_name", "")
    if model_name not in (allowed_model, fallback):
        return ControlDecision(
            "deny",
            cid,
            f"Model not allowed: {model_name!r} (expected {allowed_model!r} or fallback {fallback!r})",
        )

    review_classes = model.get("require_vendor_review_for_data_classes", [])
    if data_class in review_classes:
        return ControlDecision(
            "require_human_gate",
            cid,
            f"Vendor review required for data class: {data_class!r}",
            required_gate="G1",
            approver_role="security_owner",
        )

    return ControlDecision("allow", cid, f"Model allowed: {vendor!r}/{model_name!r}")


# ---------------------------------------------------------------------------
# Cost check
# ---------------------------------------------------------------------------


def check_cost(
    control: dict[str, Any],
    run_cost: float,
    daily_cost: float,
) -> ControlDecision:
    """Check whether *run_cost* and *daily_cost* are within the cost limits.

    Returns:
        ``require_human_gate`` — a limit is exceeded.
        ``allow`` — costs are within limits.
    """
    cost = control["cost_limit"]
    cid = control["id"]

    if run_cost > cost.get("max_run_cost", float("inf")):
        return ControlDecision(
            "require_human_gate",
            cid,
            f"Run cost limit exceeded: {run_cost} > {cost['max_run_cost']} {cost.get('currency', '')}",
            required_gate="G2",
            approver_role="business_owner",
        )

    if daily_cost > cost.get("max_daily_cost", float("inf")):
        return ControlDecision(
            "require_human_gate",
            cid,
            f"Daily cost limit exceeded: {daily_cost} > {cost['max_daily_cost']} {cost.get('currency', '')}",
            required_gate="G2",
            approver_role="business_owner",
        )

    return ControlDecision("allow", cid, "Cost within limits")


# ---------------------------------------------------------------------------
# Rollback check
# ---------------------------------------------------------------------------


def check_rollback(
    control: dict[str, Any],
    risk_level: str,
    evidence: dict[str, Any],
) -> ControlDecision:
    """Check whether rollback evidence meets the matrix requirements.

    Returns:
        ``deny`` — rollback path required but missing.
        ``require_human_gate`` — feature flag required but not documented.
        ``allow`` — rollback evidence is acceptable.
    """
    rollback = control.get("rollback", {})
    cid = control["id"]

    required_levels = set(rollback.get("rollback_path_required_for", []))
    if risk_level in required_levels and not evidence.get("rollback_path"):
        return ControlDecision(
            "deny",
            cid,
            f"rollback_path is missing for risk level {risk_level!r}",
        )

    flag_levels = set(rollback.get("feature_flag_required_for", []))
    rollback_path = evidence.get("rollback_path", "")
    if risk_level in flag_levels and "feature_flag" not in str(rollback_path):
        return ControlDecision(
            "require_human_gate",
            cid,
            f"Feature flag or documented rollback required for risk level {risk_level!r}",
            required_gate="G2",
            approver_role="technical_owner",
        )

    return ControlDecision("allow", cid, "Rollback evidence acceptable")
