"""Independent runtime implementation of the issue-42 conformance subset.

This module does not import or execute the skills reference implementation.
The trusted input file contains schema/profile/authority snapshots selected by
the conformance driver, never by fields in the candidate request.
"""
import hashlib
import json
from datetime import datetime


def digest(record):
    data = json.dumps(record, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode()
    return "sha256:" + hashlib.sha256(data).hexdigest()


def evaluate(request, trusted, schemas):
    from jsonschema import Draft202012Validator, FormatChecker

    findings = []

    def fail(code):
        if {"code": code} not in findings:
            findings.append({"code": code})

    def valid(record, name):
        schema = json.loads((schemas / (name + ".schema.json")).read_text())
        if list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(record)):
            fail("SCHEMA_INVALID")
            return False
        return True

    def result():
        return {"status": "rejected" if findings else "admitted", "findings": findings}

    def instant(text):
        value = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if value.tzinfo is None:
            raise ValueError("timezone required")
        return value

    if request.get("operation") == "reuse":
        item = request["evaluation"]
        coverage = item.get("dependency_coverage", request.get("assessment_coverage", "unknown"))
        return {"eligible": item.get("result") == "UNCHANGED" and coverage == "complete",
                "status": "admitted" if item.get("result") == "UNCHANGED" and coverage == "complete"
                else "rejected", "findings": []}

    gate_record, bundle_record = request["gate"], request["bundle"]
    if not valid(gate_record, "GATE_RECEIPT") or not valid(bundle_record, "EVIDENCE_BUNDLE.v2"):
        return result()
    gate, bundle = gate_record["gate_receipt"], bundle_record["bundle"]
    context = trusted["decision_context"]
    now = instant(trusted["now"])
    claims = {c["claim_id"]: c for c in bundle["claims"]}
    if len(claims) != len(bundle["claims"]):
        fail("DUPLICATE_CLAIM_ID")
    established = {key: set() for key in claims}
    failed = set()
    adapters = trusted.get("adapters")
    profiles = trusted.get("property_profiles")
    if adapters is None:
        fail("EVIDENCE_SOURCE_RESOLVER_REQUIRED")
    if profiles is None:
        fail("EVIDENCE_PROPERTY_RESOLVER_REQUIRED")
    seen = set()
    for item in bundle["evidence"]:
        if item["evidence_id"] in seen:
            fail("DUPLICATE_EVIDENCE_ID")
        seen.add(item["evidence_id"])
        if not set(item["supports"]) <= claims.keys():
            fail("UNKNOWN_SUPPORTED_CLAIM")
        if any(item["state_binding"].get(k) != bundle["baseline"]["subject_state"][k]
               for k in ("subject_type", "subject_ref", "subject_digest")):
            fail("EVIDENCE_STATE_MISMATCH")
        policy_digest = bundle["policy_binding"]["policy_digest"]
        if item.get("policy_binding", {}).get("policy_digest") != policy_digest:
            fail("EVIDENCE_POLICY_MISMATCH")
        source = item.get("evidence_source", {})
        source_record = (adapters or {}).get(source.get("adapter_ref"))
        capability = set()
        if source_record is None:
            fail("EVIDENCE_SOURCE_UNRESOLVED")
        elif valid(source_record, "EVIDENCE_SOURCE_PROFILE"):
            adapter = source_record["adapter"]
            if (adapter["adapter_id"] != source.get("adapter_ref") or
                    adapter["evidence_type"] != item["evidence_type"]):
                fail("EVIDENCE_SOURCE_IDENTITY_MISMATCH")
            elif source.get("adapter_digest") != digest(source_record):
                fail("EVIDENCE_SOURCE_DIGEST_MISMATCH")
            else:
                capability = set(adapter["may_establish"]) - set(adapter["may_not_establish"])
                if not set(item["establishes_properties"]) <= capability:
                    fail("EVIDENCE_PROPERTY_OVERCLAIM")
        for claim in set(item["supports"]) & claims.keys():
            if item["result"]["status"] in {"fail", "error"}:
                failed.add(claim)
            if item["result"]["status"] == "pass":
                established[claim].update(set(item["establishes_properties"]) & capability)
    for key, claim in claims.items():
        profile_record = (profiles or {}).get(claim["claim_type"] + ":" + bundle["risk_level"])
        required = set(claim["required_evidence_properties"])
        if profile_record is None:
            fail("EVIDENCE_PROPERTY_PROFILE_UNRESOLVED")
        elif valid(profile_record, "EVIDENCE_PROPERTY_PROFILE"):
            profile = profile_record["profile"]
            expected_profile = (claim["claim_type"], bundle["risk_level"])
            if (profile["claim_type"], profile["risk_level"]) != expected_profile:
                fail("EVIDENCE_PROPERTY_PROFILE_MISMATCH")
            else:
                required.update(profile["required_properties"])
        if key in failed or not required <= established[key]:
            fail("EVIDENCE_ADMISSION_INCONSISTENT")
    if bundle["admission"]["status"] != "admitted":
        fail("EVIDENCE_NOT_ADMITTED")
    if any(o["state"] != "discharged" for o in bundle.get("obligations", [])):
        fail("EVIDENCE_OBLIGATION_UNRESOLVED")

    if (gate["task_id"] != context["task_id"] or gate["gate"] != context["gate"] or
            gate["subject_state"] != context["subject_state"] or
            gate["policy"]["policy_digest"] != context["policy_digest"]):
        fail("DECISION_CONTEXT_MISMATCH")
    subject = gate["subject_state"]
    baseline = bundle["baseline"]
    if (gate["task_id"] != bundle["task_id"] or
            subject.get("subject_digest") != baseline["subject_state"]["subject_digest"] or
            subject.get("requirement_baseline_id") != baseline["requirement_baseline_id"] or
            gate["policy"] != bundle["policy_binding"] or
            set(gate["claims"]["required"]) != claims.keys()):
        fail("GATE_EVIDENCE_BINDING_MISMATCH")
    if bundle["risk_level"] != context["risk_level"]:
        fail("RISK_LEVEL_MISMATCH")
    if context["critical_risks"]:
        fail("UNRESOLVED_CRITICAL_RISK")
    minimum = {"L0": 0, "L1": 1, "L2": 2, "L3": 2, "L4": 3}[context["risk_level"]]
    verifier = gate.get("verifier", {})
    minimum = max(minimum, int(verifier.get("required_independence_class", "I0")[1]))
    if int(verifier.get("independence_class", "I0")[1]) < minimum:
        fail("INDEPENDENCE_BELOW_MINIMUM")

    status = gate["decision"]["status"]
    unresolved = (set(gate["claims"]["required"]) - set(gate["claims"]["admitted"]))
    unresolved.update(gate["claims"]["rejected"] + gate["claims"]["stale"])
    obligations = set(gate.get("obligations", {}).get("open", []))
    if status == "PASS" and (unresolved or obligations):
        fail("DECISION_INCONSISTENT")
    if status == "WAIVED":
        covered = set()
        deny = {"GATE_INTEGRITY", "SUBJECT_BINDING", "UNKNOWN_IDENTITY", "RECEIPT_INTEGRITY"}
        deny.update(context.get("non_waivable_controls", []))
        refs = gate.get("exception_refs", [])
        for ref in refs:
            record = trusted.get("exceptions", {}).get(ref)
            if record is None or record not in trusted.get("authenticated_exceptions", []):
                fail("HUMAN_AUTHORITY_UNVERIFIED")
                continue
            if not valid(record, "EXCEPTION_DECISION"):
                continue
            exc = record["exception"]
            if (exc["id"] == ref and exc["task_id"] == gate["task_id"] and
                    exc["type"] in {"waiver", "concession"} and
                    exc["control_or_claim_ref"] not in deny and
                    instant(exc["issued_at"]) <= now < instant(exc["expires_at"])):
                covered.add(exc["control_or_claim_ref"])
        if not refs or obligations or not unresolved <= covered:
            fail("WAIVER_NOT_JUSTIFIED")
    if status not in {"PASS", "WAIVED"}:
        return {"status": "rejected", "findings": findings}
    if gate["gate"] in {"gate_1", "gate_2"}:
        approved = False
        for entry in gate.get("approvals", []):
            record = trusted.get("approvals", {}).get(entry["approval_ref"])
            if record is None or record not in trusted.get("authenticated_approvals", []):
                fail("HUMAN_AUTHORITY_UNVERIFIED")
                continue
            if not valid(record, "APPROVAL.v2"):
                continue
            approval = record["approval"]
            if (approval["scope"]["action"] != context["action"] or
                    not set(context["resources"]) <= set(approval["scope"]["resources"])):
                fail("APPROVAL_SCOPE_MISMATCH")
                continue
            binding = approval["binding"]
            baseline_matches = (
                binding.get("requirement_baseline_id") == subject.get("requirement_baseline_id")
            )
            if (approval["id"] == entry["approval_ref"] and approval["decision"] == "approved" and
                    approval["task_id"] == gate["task_id"] and
                    approval["gate_id"] == gate["gate"] and
                    binding["artifact_digest"] == gate["subject_state"]["subject_digest"] and
                    binding.get("policy_digest") == gate["policy"]["policy_digest"] and
                    baseline_matches and
                    instant(approval["issued_at"]) <= now < instant(approval["expires_at"]) and
                    (approval["usage"]["reusable"] or not approval["usage"].get("consumed_at"))):
                approved = True
        if not approved:
            fail("APPROVAL_NOT_JUSTIFIED")
    return result()
