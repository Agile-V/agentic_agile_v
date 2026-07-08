"""Agile-V Control Matrix runtime enforcement checks.

Implements: REQ-CM-004 (data class check), REQ-CM-005 (tool check),
            REQ-CM-006 (model/vendor check), REQ-CM-007 (cost check),
            REQ-CM-008 (rollback check), REQ-CM-009 (tests check),
            REQ-CM-010 (max permissions check)
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
        ``deny`` — data class is explicitly forbidden or unknown and policy denies.
        ``require_human_gate`` — data class is unknown and policy requires a gate.
        ``allow`` — data class is explicitly allowed (or unknown_action is 'allow').
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
        if action == "allow":
            return ControlDecision(
                "allow", cid, f"Unknown data class allowed by policy: {data_class!r}"
            )
        # deny by default (covers "deny" and any unrecognised action value)
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

    Gate and approver-role values are read from the control's
    ``human_gates.required_before`` list when a matching action is configured,
    falling back to hardcoded defaults for backward compatibility.

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
        gate, approver = _resolve_gate(
            control, "tool_gate", default_gate="G2", default_approver="technical_owner"
        )
        return ControlDecision(
            "require_human_gate",
            cid,
            f"Tool requires Human Gate approval: {tool_class!r}",
            required_gate=gate,
            approver_role=approver,
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

    When ``allow_external_vendor`` is True, the vendor check is skipped and the
    model-name check is also skipped (any model from any external vendor is
    permitted unless the data class triggers a review gate).

    Returns:
        ``deny`` — vendor or model is not allowed.
        ``require_human_gate`` — vendor review required for this data class.
        ``allow`` — model is permitted.
    """
    model = control["model"]
    cid = control["id"]

    allowed_vendor = model.get("vendor", "")
    external_ok = model.get("allow_external_vendor", False)
    is_external = vendor != allowed_vendor

    if is_external and not external_ok:
        return ControlDecision(
            "deny",
            cid,
            f"Vendor not allowed: {vendor!r} (expected {allowed_vendor!r})",
        )

    # Skip model-name check for approved external vendors
    if not is_external:
        fallback = model.get("fallback_model")
        allowed_model = model.get("model_name", "")
        if model_name not in (allowed_model, fallback):
            return ControlDecision(
                "deny",
                cid,
                f"Model not allowed: {model_name!r} (expected {allowed_model!r} or fallback {fallback!r})",
            )

    review_classes = model.get("require_vendor_review_for_data_classes", [])
    if data_class in review_classes:
        gate, approver = _resolve_gate(
            control, "vendor_review", default_gate="G1", default_approver="security_owner"
        )
        return ControlDecision(
            "require_human_gate",
            cid,
            f"Vendor review required for data class: {data_class!r}",
            required_gate=gate,
            approver_role=approver,
        )

    return ControlDecision("allow", cid, f"Model allowed: {vendor!r}/{model_name!r}")


# ---------------------------------------------------------------------------
# Cost check
# ---------------------------------------------------------------------------


def check_cost(
    control: dict[str, Any],
    run_cost: float,
    daily_cost: float,
    monthly_cost: float | None = None,
) -> ControlDecision:
    """Check whether costs are within the cost limits.

    Args:
        control: Resolved control matrix entry.
        run_cost: Estimated cost for this run.
        daily_cost: Estimated daily accumulated cost.
        monthly_cost: Estimated monthly accumulated cost (optional).

    Returns:
        ``require_human_gate`` — a limit is exceeded.
        ``allow`` — costs are within limits.
    """
    cost = control["cost_limit"]
    cid = control["id"]
    gate, approver = _resolve_gate(
        control, "cost_approval", default_gate="G2", default_approver="business_owner"
    )

    if run_cost > cost.get("max_run_cost", float("inf")):
        return ControlDecision(
            "require_human_gate",
            cid,
            f"Run cost limit exceeded: {run_cost} > {cost['max_run_cost']} {cost.get('currency', '')}",
            required_gate=gate,
            approver_role=approver,
        )

    if daily_cost > cost.get("max_daily_cost", float("inf")):
        return ControlDecision(
            "require_human_gate",
            cid,
            f"Daily cost limit exceeded: {daily_cost} > {cost['max_daily_cost']} {cost.get('currency', '')}",
            required_gate=gate,
            approver_role=approver,
        )

    if monthly_cost is not None and monthly_cost > cost.get("max_monthly_cost", float("inf")):
        return ControlDecision(
            "require_human_gate",
            cid,
            f"Monthly cost limit exceeded: {monthly_cost} > {cost['max_monthly_cost']} {cost.get('currency', '')}",
            required_gate=gate,
            approver_role=approver,
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

    When ``rollback.required`` is explicitly ``False``, all level-based checks
    are skipped and the function returns ``allow``.

    Returns:
        ``deny`` — rollback path required but missing.
        ``require_human_gate`` — feature flag required but not documented.
        ``allow`` — rollback evidence is acceptable.
    """
    rollback = control.get("rollback", {})
    cid = control["id"]

    # Explicit opt-out overrides all level-based requirements
    if rollback.get("required") is False:
        return ControlDecision("allow", cid, "Rollback not required by policy (required=false)")

    required_levels = set(rollback.get("rollback_path_required_for", []))
    if risk_level in required_levels and not evidence.get("rollback_path"):
        return ControlDecision(
            "deny",
            cid,
            f"rollback_path is missing for risk level {risk_level!r}",
        )

    flag_levels = set(rollback.get("feature_flag_required_for", []))
    rollback_path = evidence.get("rollback_path", "")
    if risk_level in flag_levels:
        # Check the dedicated feature_flag field first, then fall back to
        # a word-boundary search in the rollback path string.
        feature_flag_name = evidence.get("feature_flag")
        path_mentions_flag = _path_mentions_feature_flag(str(rollback_path))
        if not feature_flag_name and not path_mentions_flag:
            gate, approver = _resolve_gate(
                control, "rollback_gate", default_gate="G2", default_approver="technical_owner"
            )
            return ControlDecision(
                "require_human_gate",
                cid,
                f"Feature flag or documented rollback required for risk level {risk_level!r}",
                required_gate=gate,
                approver_role=approver,
            )

    return ControlDecision("allow", cid, "Rollback evidence acceptable")


# ---------------------------------------------------------------------------
# Tests check
# ---------------------------------------------------------------------------


def check_tests(
    control: dict[str, Any],
    risk_level: str,
    evidence: dict[str, Any],
) -> ControlDecision:
    """Check whether test evidence satisfies the control's test requirements.

    Args:
        control: Resolved control matrix entry.
        risk_level: Current task risk level (L0–L4).
        evidence: Evidence dict, expected to contain ``tests_passed`` (list of
            test type strings) and optionally ``coverage_percent`` (float).

    Returns:
        ``deny`` — a required test type is missing or coverage is insufficient.
        ``allow`` — test evidence meets all requirements.
    """
    from agilev.control_matrix import RISK_ORDER

    tests_cfg = control.get("tests", {})
    cid = control["id"]

    required_types: list[str] = list(tests_cfg.get("required", []))
    if RISK_ORDER.get(risk_level, 0) >= RISK_ORDER.get("L3", 3):
        required_types += list(tests_cfg.get("required_for_l3_plus", []))
    if RISK_ORDER.get(risk_level, 0) >= RISK_ORDER.get("L4", 4):
        required_types += list(tests_cfg.get("required_for_l4", []))

    passed = set(evidence.get("tests_passed", []))
    missing = [t for t in required_types if t not in passed]
    if missing:
        return ControlDecision(
            "deny",
            cid,
            f"Missing required test types: {missing}",
        )

    min_coverage = tests_cfg.get("minimum_coverage_percent")
    if min_coverage is not None:
        actual_coverage = evidence.get("coverage_percent")
        if actual_coverage is None or actual_coverage < min_coverage:
            return ControlDecision(
                "deny",
                cid,
                f"Coverage {actual_coverage}% is below minimum {min_coverage}%",
            )

    return ControlDecision("allow", cid, "Test evidence satisfactory")


# ---------------------------------------------------------------------------
# Max permissions check
# ---------------------------------------------------------------------------


def check_max_permissions(
    control: dict[str, Any],
    requested_permissions: dict[str, str],
) -> ControlDecision:
    """Check that *requested_permissions* do not exceed the control's limits.

    Args:
        control: Resolved control matrix entry.
        requested_permissions: Dict mapping permission dimension to requested
            level (e.g. ``{"file_access": "global", "network_access": "open"}``).

    Returns:
        ``deny`` — one or more requested permissions exceed the allowed level.
        ``allow`` — all permissions are within limits.
    """
    max_perms = control.get("max_permissions", {})
    cid = control["id"]

    # Ordering of permission tiers from most restrictive to least
    _PERM_ORDER: dict[str, int] = {
        "none": 0,
        "blocked": 0,
        "blocked_unless_approved": 1,
        "read_only": 2,
        "repo_scoped": 2,
        "diff_status_only": 2,
        "task_allowed_paths_only": 3,
        "tests_and_local_tools_only": 3,
        "local_only": 3,
        "restricted": 3,
        "full": 4,
        "global": 4,
        "open": 4,
        "unrestricted": 4,
    }

    violations: list[str] = []
    for dimension, requested in requested_permissions.items():
        allowed = max_perms.get(dimension)
        if allowed is None:
            continue  # dimension not constrained by this control
        allowed_rank = _PERM_ORDER.get(str(allowed).lower(), 99)
        requested_rank = _PERM_ORDER.get(str(requested).lower(), 99)
        if requested_rank > allowed_rank:
            violations.append(f"{dimension}: requested {requested!r} exceeds allowed {allowed!r}")

    if violations:
        return ControlDecision(
            "deny",
            cid,
            "Permission limit exceeded: " + "; ".join(violations),
        )
    return ControlDecision("allow", cid, "Permissions within limits")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _resolve_gate(
    control: dict[str, Any],
    action: str,
    default_gate: str,
    default_approver: str,
) -> tuple[str, str]:
    """Return (gate, approver_role) for *action* from ``human_gates.required_before``.

    Falls back to *default_gate* / *default_approver* when no matching entry is
    found, preserving backward compatibility with controls that predate
    per-action gate configuration.
    """
    gates: list[dict[str, Any]] = control.get("human_gates", {}).get("required_before", [])
    for entry in gates:
        if entry.get("action") == action:
            return entry.get("gate", default_gate), entry.get("approver_role", default_approver)
    return default_gate, default_approver


def _path_mentions_feature_flag(path: str) -> bool:
    """Return True when *path* contains the word 'feature_flag' as a word boundary."""
    import re

    return bool(re.search(r"\bfeature_flag\b", path, re.IGNORECASE))
