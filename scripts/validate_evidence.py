#!/usr/bin/env python3
"""Validate Agentic Agile-V evidence bundles without external dependencies."""
import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

RISK_ORDER = {"L0": 0, "L1": 1, "L2": 2, "L3": 3, "L4": 4}

BASE_REQUIRED = [
    "task_id",
    "title",
    "task_type",
    "risk_level",
    "brief_path",
    "plan_path",
    "changed_files",
    "tests",
    "checks",
    "evidence_artifacts",
    "reviewer_gate",
    "rollback_path",
    "residual_risks",
]


def is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def path_exists(repo: Path, value: str) -> bool:
    if not value or is_url(value):
        return True
    return (repo / value).exists()


def result_ok(items):
    return any(str(item.get("result", "")).lower() in {"pass", "passed", "ok", "success"} for item in items if isinstance(item, dict))


def has_named(items, keywords):
    text = "\n".join(json.dumps(item).lower() for item in items)
    return any(k in text for k in keywords)


def validate_bundle(bundle_path: Path, repo: Path):
    errors = []
    warnings = []
    try:
        data = json.loads(bundle_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"{bundle_path}: cannot parse JSON: {exc}"], []

    for field in BASE_REQUIRED:
        if field not in data:
            errors.append(f"missing field: {field}")

    risk = data.get("risk_level")
    if risk not in RISK_ORDER:
        errors.append(f"invalid risk_level: {risk}")
        risk_num = -1
    else:
        risk_num = RISK_ORDER[risk]

    for field in ["brief_path", "plan_path"]:
        value = data.get(field, "")
        if value and not path_exists(repo, value):
            errors.append(f"{field} does not exist: {value}")

    for artifact in data.get("evidence_artifacts", []):
        if artifact and not path_exists(repo, artifact):
            warnings.append(f"evidence artifact not found locally: {artifact}")

    tests = data.get("tests", [])
    checks = data.get("checks", [])
    reviewer = data.get("reviewer_gate", {}) if isinstance(data.get("reviewer_gate"), dict) else {}

    if risk_num >= 1:
        if not tests:
            errors.append("L1+ requires tests or explicit test rationale")
        if not checks:
            errors.append("L1+ requires at least one check such as lint, type, build, or static analysis")

    if risk_num >= 2:
        if not result_ok(tests):
            errors.append("L2+ requires at least one passing test entry")
        if not result_ok(checks):
            errors.append("L2+ requires at least one passing check entry")
        if reviewer.get("required") is not True:
            errors.append("L2+ requires reviewer_gate.required = true")

    if risk_num >= 3:
        if not has_named(checks + tests, ["security", "privacy", "regression", "integration"]):
            errors.append("L3+ requires security/privacy/regression/integration evidence")
        rollback = str(data.get("rollback_path", "")).strip().lower()
        if not rollback or rollback in {"n/a", "none", "not applicable"}:
            errors.append("L3+ requires a concrete rollback path")

    if risk_num >= 4:
        if not has_named(checks + tests + [{"artifact": a} for a in data.get("evidence_artifacts", [])], ["hil", "simulation", "formal", "timing", "traceability", "independent"]):
            errors.append("L4 requires independent verification, HIL, simulation, formal, timing, or traceability evidence")

    residual = data.get("residual_risks", [])
    if not residual:
        warnings.append("residual_risks is empty; record 'none' explicitly if no risk remains")

    prefix_errors = [f"{bundle_path}: {e}" for e in errors]
    prefix_warnings = [f"{bundle_path}: {w}" for w in warnings]
    return prefix_errors, prefix_warnings


def find_bundles(root: Path):
    if root.is_file():
        return [root]
    return sorted(root.rglob("evidence_bundle.json"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Agentic Agile-V evidence bundles.")
    parser.add_argument("--bundle", type=Path, help="Path to one evidence_bundle.json")
    parser.add_argument("--root", type=Path, default=Path("evidence"), help="Root directory containing bundles")
    args = parser.parse_args()

    repo = Path.cwd()
    target = args.bundle if args.bundle else args.root
    bundles = find_bundles(target)
    if not bundles:
        print(f"No evidence bundles found under {target}")
        return 1

    all_errors = []
    all_warnings = []
    for bundle in bundles:
        errors, warnings = validate_bundle(bundle, repo)
        all_errors.extend(errors)
        all_warnings.extend(warnings)

    for warning in all_warnings:
        print(f"WARNING: {warning}")
    for error in all_errors:
        print(f"ERROR: {error}")

    if all_errors:
        print(f"Validation failed: {len(all_errors)} error(s), {len(all_warnings)} warning(s)")
        return 1
    print(f"Validation passed: {len(bundles)} bundle(s), {len(all_warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
