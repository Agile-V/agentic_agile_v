"""Unit tests for control_enforcer.py checks.

Implements: REQ-CM-004 through REQ-CM-010
"""

from __future__ import annotations

from agilev.control_enforcer import (
    check_cost,
    check_data_class,
    check_max_permissions,
    check_model,
    check_rollback,
    check_tests,
    check_tool,
)

# ---------------------------------------------------------------------------
# Shared fixture control dict
# ---------------------------------------------------------------------------


CONTROL: dict = {
    "id": "cm-test",
    "data_class": {
        "allowed": ["public", "internal"],
        "forbidden": ["secret", "regulated_health"],
        "unknown_action": "require_human_gate",
        "redaction_required": True,
        "default_if_unknown": "internal",
    },
    "tools": {
        "allowed": ["read_file", "write_file", "run_tests"],
        "forbidden": ["deploy_production", "delete_data"],
        "requires_gate": ["shell_exec", "network_egress"],
    },
    "model": {
        "vendor": "acme-ai",
        "model_name": "acme-model-v1",
        "fallback_model": "acme-model-v0",
        "allow_external_vendor": False,
        "require_vendor_review_for_data_classes": ["confidential"],
        "record_model_in_evidence": True,
    },
    "cost_limit": {
        "currency": "EUR",
        "max_run_cost": 2.00,
        "max_daily_cost": 25.00,
        "action_on_limit": "stop_and_request_approval",
        "cost_log": ".agile-v/logs/costs.jsonl",
    },
    "rollback": {
        "required": True,
        "strategy": "revert_commit",
        "rollback_path_required_for": ["L2", "L3", "L4"],
        "feature_flag_required_for": ["L3", "L4"],
        "max_rollback_time_minutes": 30,
        "rollback_owner_role": "technical_owner",
    },
}

# ---------------------------------------------------------------------------
# check_data_class
# ---------------------------------------------------------------------------


def test_allowed_data_class_returns_allow():
    result = check_data_class(CONTROL, "public")
    assert result.decision == "allow"


def test_forbidden_data_class_returns_deny():
    result = check_data_class(CONTROL, "secret")
    assert result.decision == "deny"


def test_unknown_data_class_returns_require_human_gate():
    result = check_data_class(CONTROL, "mystery_class")
    assert result.decision == "require_human_gate"
    assert result.required_gate == "G1"
    assert result.approver_role == "security_owner"


def test_unknown_data_class_deny_when_configured():
    control = {**CONTROL, "data_class": {**CONTROL["data_class"], "unknown_action": "deny"}}
    result = check_data_class(control, "mystery_class")
    assert result.decision == "deny"


# ---------------------------------------------------------------------------
# check_tool
# ---------------------------------------------------------------------------


def test_allowed_tool_returns_allow():
    result = check_tool(CONTROL, "read_file")
    assert result.decision == "allow"


def test_forbidden_tool_returns_deny():
    result = check_tool(CONTROL, "deploy_production")
    assert result.decision == "deny"


def test_gated_tool_returns_require_human_gate():
    result = check_tool(CONTROL, "shell_exec")
    assert result.decision == "require_human_gate"
    assert result.required_gate == "G2"
    assert result.approver_role == "technical_owner"


def test_unlisted_tool_returns_deny():
    result = check_tool(CONTROL, "some_random_tool")
    assert result.decision == "deny"


# ---------------------------------------------------------------------------
# check_model
# ---------------------------------------------------------------------------


def test_allowed_vendor_and_model_returns_allow():
    result = check_model(CONTROL, "acme-ai", "acme-model-v1", "internal")
    assert result.decision == "allow"


def test_fallback_model_returns_allow():
    result = check_model(CONTROL, "acme-ai", "acme-model-v0", "internal")
    assert result.decision == "allow"


def test_unauthorized_vendor_returns_deny():
    result = check_model(CONTROL, "rival-ai", "rival-model", "internal")
    assert result.decision == "deny"


def test_unauthorized_model_returns_deny():
    result = check_model(CONTROL, "acme-ai", "unknown-model", "internal")
    assert result.decision == "deny"


def test_vendor_review_required_for_sensitive_data_class():
    result = check_model(CONTROL, "acme-ai", "acme-model-v1", "confidential")
    assert result.decision == "require_human_gate"
    assert result.required_gate == "G1"


def test_external_vendor_ok_when_allowed():
    """When allow_external_vendor=True, vendor and model-name checks are skipped."""
    control = {**CONTROL, "model": {**CONTROL["model"], "allow_external_vendor": True}}
    result = check_model(control, "third-party-ai", "third-party-model", "internal")
    assert result.decision == "allow"


def test_external_vendor_still_gated_for_sensitive_data_class():
    """Even with allow_external_vendor=True, sensitive data classes still require a gate."""
    control = {**CONTROL, "model": {**CONTROL["model"], "allow_external_vendor": True}}
    result = check_model(control, "third-party-ai", "third-party-model", "confidential")
    assert result.decision == "require_human_gate"


# ---------------------------------------------------------------------------
# check_cost
# ---------------------------------------------------------------------------


def test_cost_within_limits_returns_allow():
    result = check_cost(CONTROL, run_cost=1.00, daily_cost=10.00)
    assert result.decision == "allow"


def test_run_cost_over_limit_requires_gate():
    result = check_cost(CONTROL, run_cost=3.00, daily_cost=10.00)
    assert result.decision == "require_human_gate"
    assert result.approver_role == "business_owner"


def test_daily_cost_over_limit_requires_gate():
    result = check_cost(CONTROL, run_cost=1.00, daily_cost=30.00)
    assert result.decision == "require_human_gate"
    assert result.approver_role == "business_owner"


# ---------------------------------------------------------------------------
# check_rollback
# ---------------------------------------------------------------------------


def test_rollback_ok_when_path_present_for_l2():
    result = check_rollback(CONTROL, "L2", {"rollback_path": "git revert HEAD"})
    assert result.decision == "allow"


def test_rollback_deny_when_path_missing_for_l2():
    result = check_rollback(CONTROL, "L2", {})
    assert result.decision == "deny"


def test_rollback_ok_for_l1():
    # L1 is not in rollback_path_required_for
    result = check_rollback(CONTROL, "L1", {})
    assert result.decision == "allow"


def test_rollback_feature_flag_required_for_l3():
    # No "feature_flag" in rollback_path string
    result = check_rollback(CONTROL, "L3", {"rollback_path": "git revert HEAD"})
    assert result.decision == "require_human_gate"
    assert result.required_gate == "G2"


def test_rollback_feature_flag_ok_when_mentioned():
    result = check_rollback(CONTROL, "L3", {"rollback_path": "disable feature_flag FF-001"})
    assert result.decision == "allow"


def test_rollback_required_false_skips_all_checks():
    """rollback.required=False overrides all level-based requirements."""
    control = {**CONTROL, "rollback": {**CONTROL["rollback"], "required": False}}
    # L2 normally requires rollback_path — should be skipped when required=False
    result = check_rollback(control, "L2", {})
    assert result.decision == "allow"


def test_rollback_feature_flag_via_dedicated_field():
    """A dedicated 'feature_flag' key in evidence satisfies the flag requirement."""
    result = check_rollback(
        CONTROL, "L3", {"rollback_path": "git revert HEAD", "feature_flag": "FF-001"}
    )
    assert result.decision == "allow"


def test_rollback_flag_string_underscore_adjacent_does_not_match():
    """'disable_legacy_feature_flag_migration' does NOT match because the \b boundary
    does not fire between underscores (all are word characters)."""
    result = check_rollback(
        CONTROL, "L3", {"rollback_path": "disable_legacy_feature_flag_migration"}
    )
    # \bfeature_flag\b doesn't match when surrounded by underscores → gate required
    assert result.decision == "require_human_gate"


# ---------------------------------------------------------------------------
# check_data_class — additional cases
# ---------------------------------------------------------------------------


def test_unknown_data_class_allow_when_configured():
    control = {**CONTROL, "data_class": {**CONTROL["data_class"], "unknown_action": "allow"}}
    result = check_data_class(control, "mystery_class")
    assert result.decision == "allow"
    assert "allowed by policy" in result.reason


# ---------------------------------------------------------------------------
# check_cost — additional cases
# ---------------------------------------------------------------------------


def test_run_cost_at_exact_limit_is_allowed():
    """Exactly at the limit is allowed (strict greater-than check)."""
    result = check_cost(CONTROL, run_cost=2.00, daily_cost=10.00)
    assert result.decision == "allow"


def test_monthly_cost_over_limit_requires_gate():
    control = {**CONTROL, "cost_limit": {**CONTROL["cost_limit"], "max_monthly_cost": 100.00}}
    result = check_cost(control, run_cost=1.00, daily_cost=10.00, monthly_cost=150.00)
    assert result.decision == "require_human_gate"
    assert result.approver_role == "business_owner"


def test_monthly_cost_within_limit_allows():
    control = {**CONTROL, "cost_limit": {**CONTROL["cost_limit"], "max_monthly_cost": 100.00}}
    result = check_cost(control, run_cost=1.00, daily_cost=10.00, monthly_cost=50.00)
    assert result.decision == "allow"


def test_monthly_cost_none_does_not_check():
    control = {**CONTROL, "cost_limit": {**CONTROL["cost_limit"], "max_monthly_cost": 100.00}}
    # monthly_cost=None means no monthly check
    result = check_cost(control, run_cost=1.00, daily_cost=10.00, monthly_cost=None)
    assert result.decision == "allow"


# ---------------------------------------------------------------------------
# check_tests
# ---------------------------------------------------------------------------

TESTS_CONTROL: dict = {
    **CONTROL,
    "tests": {
        "required": ["schema_validation", "unit_tests"],
        "required_for_l3_plus": ["integration_tests"],
        "required_for_l4": ["security_scan"],
        "minimum_coverage_percent": 80,
    },
}


def test_check_tests_all_present_returns_allow():
    evidence = {"tests_passed": ["schema_validation", "unit_tests"], "coverage_percent": 85}
    result = check_tests(TESTS_CONTROL, "L1", evidence)
    assert result.decision == "allow"


def test_check_tests_missing_required_returns_deny():
    evidence = {"tests_passed": ["schema_validation"], "coverage_percent": 85}
    result = check_tests(TESTS_CONTROL, "L1", evidence)
    assert result.decision == "deny"
    assert "unit_tests" in result.reason


def test_check_tests_l3_requires_integration():
    evidence = {"tests_passed": ["schema_validation", "unit_tests"], "coverage_percent": 85}
    result = check_tests(TESTS_CONTROL, "L3", evidence)
    assert result.decision == "deny"
    assert "integration_tests" in result.reason


def test_check_tests_l3_with_integration_passes():
    evidence = {
        "tests_passed": ["schema_validation", "unit_tests", "integration_tests"],
        "coverage_percent": 85,
    }
    result = check_tests(TESTS_CONTROL, "L3", evidence)
    assert result.decision == "allow"


def test_check_tests_l4_requires_security_scan():
    evidence = {
        "tests_passed": ["schema_validation", "unit_tests", "integration_tests"],
        "coverage_percent": 85,
    }
    result = check_tests(TESTS_CONTROL, "L4", evidence)
    assert result.decision == "deny"
    assert "security_scan" in result.reason


def test_check_tests_coverage_below_minimum():
    evidence = {"tests_passed": ["schema_validation", "unit_tests"], "coverage_percent": 70}
    result = check_tests(TESTS_CONTROL, "L1", evidence)
    assert result.decision == "deny"
    assert "70" in result.reason


def test_check_tests_coverage_at_minimum_passes():
    evidence = {"tests_passed": ["schema_validation", "unit_tests"], "coverage_percent": 80}
    result = check_tests(TESTS_CONTROL, "L1", evidence)
    assert result.decision == "allow"


def test_check_tests_no_coverage_field_blocks():
    evidence = {"tests_passed": ["schema_validation", "unit_tests"]}
    result = check_tests(TESTS_CONTROL, "L1", evidence)
    assert result.decision == "deny"


def test_check_tests_no_min_coverage_configured():
    control = {
        **TESTS_CONTROL,
        "tests": {**TESTS_CONTROL["tests"], "minimum_coverage_percent": None},
    }
    evidence = {"tests_passed": ["schema_validation", "unit_tests"]}
    result = check_tests(control, "L1", evidence)
    assert result.decision == "allow"


# ---------------------------------------------------------------------------
# check_max_permissions
# ---------------------------------------------------------------------------


MAX_PERM_CONTROL: dict = {
    **CONTROL,
    "max_permissions": {
        "file_access": "repo_scoped",
        "write_access": "task_allowed_paths_only",
        "network_access": "blocked_unless_approved",
        "database_access": "none",
    },
}


def test_check_max_permissions_all_within_limit():
    result = check_max_permissions(
        MAX_PERM_CONTROL,
        {"file_access": "repo_scoped", "network_access": "blocked_unless_approved"},
    )
    assert result.decision == "allow"


def test_check_max_permissions_exceeds_file_access():
    result = check_max_permissions(MAX_PERM_CONTROL, {"file_access": "global"})
    assert result.decision == "deny"
    assert "file_access" in result.reason


def test_check_max_permissions_unknown_dimension_ignored():
    """Dimensions not in max_permissions are not constrained."""
    result = check_max_permissions(MAX_PERM_CONTROL, {"unknown_dimension": "global"})
    assert result.decision == "allow"


def test_check_max_permissions_empty_requested_allows():
    result = check_max_permissions(MAX_PERM_CONTROL, {})
    assert result.decision == "allow"


def test_check_max_permissions_no_max_permissions_key():
    """Control without max_permissions key allows everything."""
    control = {k: v for k, v in CONTROL.items() if k != "max_permissions"}
    result = check_max_permissions(control, {"file_access": "global"})
    assert result.decision == "allow"


def test_check_max_permissions_exceeds_file_access_base_control():
    result = check_max_permissions(MAX_PERM_CONTROL, {"file_access": "global"})
    assert result.decision == "deny"
    assert "file_access" in result.reason


def test_check_max_permissions_unknown_dimension_ignored_base_control():
    """Dimensions not in max_permissions are not constrained."""
    result = check_max_permissions(CONTROL, {"unknown_dimension": "global"})
    assert result.decision == "allow"


def test_check_max_permissions_empty_requested_allows_base_control():
    result = check_max_permissions(CONTROL, {})
    assert result.decision == "allow"
