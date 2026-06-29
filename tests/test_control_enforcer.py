"""Unit tests for control_enforcer.py checks.

Implements: REQ-CM-004 through REQ-CM-008
"""

from __future__ import annotations

import pytest

from agilev.control_enforcer import (
    check_cost,
    check_data_class,
    check_model,
    check_rollback,
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
    control = {**CONTROL, "model": {**CONTROL["model"], "allow_external_vendor": True}}
    result = check_model(control, "third-party-ai", "third-party-model", "internal")
    # Model name still checked; should deny since model name doesn't match
    assert result.decision == "deny"


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
