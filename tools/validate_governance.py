#!/usr/bin/env python3
"""Validate the OpenClaw foundation governance packet without external deps."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GOV = ROOT / "governance"


REQUIRED_FILES = [
    ROOT / "FOUNDATION.md",
    ROOT / "CUSTOM-CODE-RULE.md",
    GOV / "README.md",
    GOV / "AGENTS.md",
    GOV / "blueprint.md",
    GOV / "phase-gates.json",
    GOV / "gate-ledger.json",
    GOV / "operating-method.md",
    GOV / "task-admission.schema.json",
    GOV / "candidate-register.jsonl",
    GOV / "deny-register.jsonl",
    GOV / "model-routing.md",
    GOV / "branch-protection-plan.md",
    GOV / "dashboard-read-model.md",
    GOV / "skill-plugin-register.jsonl",
    GOV / "custom-code-decisions.jsonl",
    GOV / "evidence-contract.md",
    GOV / "community-evidence-contract.md",
    GOV / "codex-access-contract.md",
    GOV / "policy-rules.json",
]

ALLOWED_GATE_STATUSES = {"NOT_STARTED", "ACTIVE", "PASS", "BLOCKED", "REJECTED"}
REQUIRED_PHASE_FIELDS = {
    "id",
    "name",
    "objective",
    "required_artifacts",
    "required_checks",
    "completion_criteria",
    "anti_drift_requirements",
    "community_evidence_required",
    "community_evidence_requirements",
    "ryan_required",
}
REQUIRED_PASS_REVIEW_FIELDS = {"reviewer", "verdict", "evidence_assessment", "drift_assessment", "runtime_enforcement_assessment"}
REQUIRED_LEDGER_FIELDS = {
    "id",
    "status",
    "owner",
    "evidence",
    "checks",
    "anti_drift_confirmed",
    "disposition",
}
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.read_text(encoding="utf-8").strip():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise AssertionError(f"{path}:{line_no}: invalid JSONL: {exc}") from exc
            if not isinstance(value, dict):
                raise AssertionError(f"{path}:{line_no}: JSONL row must be an object")
            rows.append(value)
    return rows


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_required_files() -> None:
    missing = [str(p.relative_to(ROOT)) for p in REQUIRED_FILES if not p.exists()]
    require(not missing, f"missing required files: {missing}")


def validate_registers() -> None:
    candidates = load_jsonl(GOV / "candidate-register.jsonl")
    require(candidates, "candidate register must not be empty")
    candidate_required = {
        "id",
        "name",
        "url",
        "role",
        "status",
        "evidence_grade",
        "score",
        "verdict",
        "source_commit",
        "re_review_condition",
    }
    for row in candidates:
        missing = candidate_required - set(row)
        require(not missing, f"candidate {row.get('id')} missing {sorted(missing)}")
        require(isinstance(row["score"], int) and 0 <= row["score"] <= 100, f"candidate {row['id']} invalid score")
        require(isinstance(row["url"], str) and row["url"].startswith("https://"), f"candidate {row['id']} must have https URL")
        require(isinstance(row["source_commit"], str) and COMMIT_RE.match(row["source_commit"]), f"candidate {row['id']} must pin a 40-char commit")
        require(isinstance(row["verdict"], str) and len(row["verdict"].strip()) >= 20, f"candidate {row['id']} verdict too thin")
        require(isinstance(row["re_review_condition"], str) and len(row["re_review_condition"].strip()) >= 10, f"candidate {row['id']} re-review condition too thin")

    denies = load_jsonl(GOV / "deny-register.jsonl")
    require(denies, "deny register must not be empty")
    deny_required = {"id", "pattern", "status", "reason", "re_review_condition"}
    for row in denies:
        missing = deny_required - set(row)
        require(not missing, f"deny entry {row.get('id')} missing {sorted(missing)}")
        require(row["status"] == "denied", f"deny entry {row['id']} status must be denied")
        require(isinstance(row["reason"], str) and len(row["reason"].strip()) >= 20, f"deny entry {row['id']} reason too thin")


def validate_task_packet(packet: dict[str, Any], rules: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in rules["required_task_fields"]:
        if field not in packet:
            errors.append(f"missing required field: {field}")

    if errors:
        return errors

    text_fields = [
        "id",
        "title",
        "goal",
        "expected_value",
        "data_class",
        "risk_class",
        "model_class",
        "evidence_target",
        "stop_condition",
        "rollback",
        "owner",
    ]
    for field in text_fields:
        if not isinstance(packet.get(field), str) or not packet[field].strip():
            errors.append(f"{field} must be a non-empty string")

    if packet.get("model_class") not in rules["allowed_model_classes"]:
        errors.append(f"model_class is not allowed: {packet.get('model_class')}")

    allowed_tools = packet.get("allowed_tools")
    if not isinstance(allowed_tools, list) or not allowed_tools:
        errors.append("allowed_tools must be a non-empty list")

    budget = packet.get("budget")
    required_budget = [
        "max_usd_per_run",
        "max_tokens_per_run",
        "max_wall_clock_minutes",
        "max_tool_calls",
        "max_subagents",
        "max_retries",
        "approval_required_above_usd",
        "stop_if_no_new_evidence",
    ]
    if not isinstance(budget, dict):
        errors.append("budget must be an object")
    else:
        for field in required_budget:
            if field not in budget:
                errors.append(f"budget missing {field}")
        for field in required_budget[:-1]:
            if field in budget and not isinstance(budget[field], (int, float)):
                errors.append(f"budget.{field} must be numeric")
        if "stop_if_no_new_evidence" in budget and not isinstance(budget["stop_if_no_new_evidence"], bool):
            errors.append("budget.stop_if_no_new_evidence must be boolean")

    admission = packet.get("admission")
    if not isinstance(admission, dict):
        errors.append("admission must be an object")
    else:
        result = admission.get("result")
        if result not in rules["allowed_admission_results"]:
            errors.append(f"admission.result is not allowed: {result}")
        if not isinstance(admission.get("reason"), str) or len(admission.get("reason", "").strip()) < 10:
            errors.append("admission.reason must be meaningful")

    protected = packet.get("protected_boundaries")
    if not isinstance(protected, list):
        errors.append("protected_boundaries must be a list")
    else:
        unknown = sorted(set(protected) - set(rules["protected_boundaries"]))
        if unknown:
            errors.append(f"unknown protected boundaries: {unknown}")
        if protected and admission and admission.get("result") not in {"approval_required", "reject"}:
            errors.append("protected boundaries require approval_required or reject admission result")

    forbidden = packet.get("forbidden_patterns", [])
    if forbidden:
        denied = set(rules["forbidden_patterns"])
        matched = sorted(set(forbidden) & denied)
        if matched and admission and admission.get("result") != "reject":
            errors.append(f"denied patterns require reject admission: {matched}")

    return errors


def validate_fixtures() -> None:
    rules = load_json(GOV / "policy-rules.json")
    fixture_dir = GOV / "admission-fixtures"
    require(fixture_dir.exists(), "admission-fixtures directory missing")
    fixtures = sorted(fixture_dir.glob("*.json"))
    require(fixtures, "admission fixtures missing")

    good = [p for p in fixtures if p.name.startswith("good-")]
    bad = [p for p in fixtures if p.name.startswith("bad-")]
    require(good, "at least one good fixture required")
    require(bad, "at least one bad fixture required")

    for path in good:
        errors = validate_task_packet(load_json(path), rules)
        require(not errors, f"good fixture failed {path.name}: {errors}")

    bad_passed: list[str] = []
    for path in bad:
        errors = validate_task_packet(load_json(path), rules)
        if not errors:
            bad_passed.append(path.name)
    require(not bad_passed, f"bad fixtures unexpectedly passed: {bad_passed}")


def validate_schema_alignment() -> None:
    schema = load_json(GOV / "task-admission.schema.json")
    rules = load_json(GOV / "policy-rules.json")
    schema_required = set(schema.get("required", []))
    rule_required = set(rules.get("required_task_fields", []))
    require(schema_required == rule_required, "schema required fields do not match policy required fields")


def path_exists_for_evidence(path_value: str) -> bool:
    return (ROOT / path_value).exists()


def validate_phase_gates() -> None:
    phase_doc = load_json(GOV / "phase-gates.json")
    ledger = load_json(GOV / "gate-ledger.json")

    require(phase_doc.get("authority") == "governance/blueprint.md", "phase gates must point to blueprint authority")
    require(phase_doc.get("ledger") == "governance/gate-ledger.json", "phase gates must point to gate ledger")
    require(phase_doc.get("enforcement") == "tools/validate_governance.py", "phase gates must name validator enforcement")
    require(ALLOWED_GATE_STATUSES <= set(phase_doc.get("phase_statuses", [])), "phase status list missing allowed statuses")
    pass_requires = phase_doc.get("pass_requires")
    require(isinstance(pass_requires, list) and len(pass_requires) >= 5, "phase gates must define pass requirements")
    require(all(isinstance(item, str) and item.strip() for item in pass_requires), "pass requirements must be non-empty strings")

    phases = phase_doc.get("phases")
    require(isinstance(phases, list) and phases, "phase-gates must contain phases")
    phase_by_id: dict[str, dict[str, Any]] = {}
    for phase in phases:
        require(isinstance(phase, dict), "phase entry must be an object")
        missing = REQUIRED_PHASE_FIELDS - set(phase)
        require(not missing, f"phase {phase.get('id')} missing {sorted(missing)}")
        phase_id = phase["id"]
        require(isinstance(phase_id, str) and re.match(r"^P[0-9]+$", phase_id), f"phase id invalid: {phase_id}")
        require(phase_id not in phase_by_id, f"duplicate phase id: {phase_id}")
        phase_by_id[phase_id] = phase
        for field in ["required_artifacts", "required_checks", "completion_criteria", "anti_drift_requirements"]:
            require(isinstance(phase[field], list) and phase[field], f"phase {phase_id} {field} must be a non-empty list")
            require(all(isinstance(item, str) and item.strip() for item in phase[field]), f"phase {phase_id} {field} must contain non-empty strings")
        require(isinstance(phase["community_evidence_required"], bool), f"phase {phase_id} community_evidence_required must be boolean")
        require(isinstance(phase["community_evidence_requirements"], list), f"phase {phase_id} community_evidence_requirements must be a list")
        if phase["community_evidence_required"]:
            require(phase["community_evidence_requirements"], f"phase {phase_id} requires community evidence details")
        require(isinstance(phase["ryan_required"], bool), f"phase {phase_id} ryan_required must be boolean")

    require(ledger.get("authority") == "governance/phase-gates.json", "gate ledger must point to phase gates")
    active_phase = ledger.get("active_phase")
    require(active_phase in phase_by_id, f"active phase is not defined: {active_phase}")

    gates = ledger.get("gates")
    require(isinstance(gates, list) and gates, "gate ledger must contain gates")
    gate_by_id: dict[str, dict[str, Any]] = {}
    active_gates: list[str] = []
    for gate in gates:
        require(isinstance(gate, dict), "gate entry must be an object")
        missing = REQUIRED_LEDGER_FIELDS - set(gate)
        require(not missing, f"gate {gate.get('id')} missing {sorted(missing)}")
        gate_id = gate["id"]
        require(gate_id in phase_by_id, f"gate {gate_id} has no phase definition")
        require(gate_id not in gate_by_id, f"duplicate gate id: {gate_id}")
        gate_by_id[gate_id] = gate
        status = gate["status"]
        require(status in ALLOWED_GATE_STATUSES, f"gate {gate_id} invalid status: {status}")
        if status == "ACTIVE":
            active_gates.append(gate_id)
        require(isinstance(gate["owner"], str) and gate["owner"].strip(), f"gate {gate_id} owner required")
        require(isinstance(gate["evidence"], list), f"gate {gate_id} evidence must be a list")
        require(isinstance(gate["checks"], list), f"gate {gate_id} checks must be a list")
        require(isinstance(gate["anti_drift_confirmed"], bool), f"gate {gate_id} anti_drift_confirmed must be boolean")
        require(isinstance(gate["disposition"], str) and len(gate["disposition"].strip()) >= 20, f"gate {gate_id} disposition too thin")

        if status in {"PASS", "ACTIVE"}:
            require(gate["evidence"], f"gate {gate_id} {status} requires evidence")
            require(gate["checks"], f"gate {gate_id} {status} requires checks")
            require(gate["anti_drift_confirmed"], f"gate {gate_id} {status} requires anti_drift_confirmed=true")

        if status == "PASS":
            review = gate.get("review")
            require(isinstance(review, dict), f"gate {gate_id} PASS requires independent review object")
            missing_review = REQUIRED_PASS_REVIEW_FIELDS - set(review)
            require(not missing_review, f"gate {gate_id} review missing {sorted(missing_review)}")
            require(review.get("verdict") == "pass", f"gate {gate_id} PASS requires review.verdict=pass")
            for field in REQUIRED_PASS_REVIEW_FIELDS - {"verdict"}:
                require(isinstance(review.get(field), str) and len(review[field].strip()) >= 20, f"gate {gate_id} review.{field} too thin")
            if phase_by_id[gate_id]["ryan_required"]:
                require(isinstance(gate.get("ryan_approval"), dict) and gate["ryan_approval"].get("status") == "approved", f"gate {gate_id} requires Ryan approval")
            for artifact in phase_by_id[gate_id]["required_artifacts"]:
                if artifact.startswith(("governance/", "tools/")) or artifact in {"FOUNDATION.md", "CUSTOM-CODE-RULE.md"}:
                    require(path_exists_for_evidence(artifact), f"gate {gate_id} PASS missing artifact {artifact}")

        for evidence in gate["evidence"]:
            require(isinstance(evidence, dict), f"gate {gate_id} evidence rows must be objects")
            require(isinstance(evidence.get("type"), str) and evidence["type"].strip(), f"gate {gate_id} evidence type required")
            require(isinstance(evidence.get("path"), str) and evidence["path"].strip(), f"gate {gate_id} evidence path required")
            require(isinstance(evidence.get("description"), str) and len(evidence["description"].strip()) >= 10, f"gate {gate_id} evidence description too thin")
            if evidence["type"] == "file":
                require(path_exists_for_evidence(evidence["path"]), f"gate {gate_id} evidence file missing: {evidence['path']}")

    require(set(gate_by_id) == set(phase_by_id), "gate ledger ids must match phase-gate ids")
    require(active_gates == [active_phase], f"exactly one ACTIVE gate must match active_phase; got {active_gates}, expected {[active_phase]}")


def validate_agent_entrypoint() -> None:
    agent_text = (GOV / "AGENTS.md").read_text(encoding="utf-8")
    readme_text = (GOV / "README.md").read_text(encoding="utf-8")
    for required in [
        "governance/blueprint.md",
        "governance/phase-gates.json",
        "governance/gate-ledger.json",
        "governance/codex-access-contract.md",
        "tools/validate_governance.py",
    ]:
        require(required in agent_text, f"governance/AGENTS.md must point agents to {required}")
    require("ACTIVE" in agent_text and "ACTIVE" in readme_text, "agent entry/readme must mention active phase execution")
    require("second authority" in (GOV / "blueprint.md").read_text(encoding="utf-8"), "blueprint must reject second authority drift")


def validate_community_evidence_contract() -> None:
    text = (GOV / "community-evidence-contract.md").read_text(encoding="utf-8")
    for required in ["source URL", "evidence grade", "score", "pinned source commit", "re-review condition", "local sandbox proof"]:
        require(required in text, f"community evidence contract missing: {required}")


def validate_codex_access_contract() -> None:
    text = (GOV / "codex-access-contract.md").read_text(encoding="utf-8")
    for required in [
        "/home/openclaw/foundation-source",
        "Q:\\",
        "PowerShell",
        "not use Windows PowerShell as the project logic layer",
        "Use the sudo helper only for protected VM/runtime/system operations",
    ]:
        require(required in text, f"codex access contract missing: {required}")


def main() -> int:
    checks = [
        validate_required_files,
        validate_registers,
        validate_schema_alignment,
        validate_fixtures,
        validate_phase_gates,
        validate_agent_entrypoint,
        validate_community_evidence_contract,
        validate_codex_access_contract,
    ]
    try:
        for check in checks:
            check()
    except AssertionError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 1

    print(json.dumps({"ok": True, "validated": str(ROOT), "checks": [c.__name__ for c in checks]}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())


