#!/usr/bin/env python3
"""Validate the OpenClaw foundation governance packet without external deps."""

from __future__ import annotations

import json
import re
import subprocess
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
    GOV / "gate-review-contract.md",
    GOV / "gate-action-review-contract.md",
    GOV / "p1-environment.example.json",
    GOV / "policy-rules.json",
    ROOT / "tools" / "check_p1_environment.py",
    ROOT / "tools" / "generate_gate_action_report.py",
    ROOT / "tools" / "setup_p1_github_environment.py",
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
REQUIRED_REVIEW_PACKET_FIELDS = {
    "gate_id",
    "phase_name",
    "reviewed_commit",
    "reviewer",
    "reviewer_independence",
    "verdict",
    "summary",
    "mechanical_validation",
    "criteria_results",
    "anti_drift_results",
    "runtime_enforcement",
    "blocking_findings",
    "next_action",
}
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
REVIEW_VERDICTS = {"pass", "fail", "blocked"}
REVIEW_ITEM_STATUSES = {"pass", "fail", "blocked", "needs_review"}
RUNTIME_ENFORCEMENT_STATUSES = {"not_applicable", "repo_only", "openclaw_enforced", "approval_required", "blocked"}
GATE_ACTION_REPORT_STATUSES = {"pass", "blocked", "fail"}
GATE_ACTIONS = {"activate", "pass_review", "blocked_review", "reject_review", "status_review"}
REQUIRED_GATE_ACTION_REPORT_FIELDS = {
    "schema_version",
    "generated_at",
    "gate_id",
    "phase_name",
    "gate_status",
    "action",
    "reviewed_commit",
    "reviewer",
    "overall_status",
    "repo_review_scope",
    "tracked_file_summary",
    "git_status",
    "changed_files",
    "untracked_files",
    "required_artifact_results",
    "mechanical_checks",
    "plan_compliance_assessment",
    "community_evidence_assessment",
    "deny_register_assessment",
    "custom_code_assessment",
    "access_contract_assessment",
    "intervention_balance_assessment",
    "gate_review_verdict",
    "blocking_findings",
    "ryan_report",
}
REQUIRED_GATE_ACTION_SCOPE = {
    "blueprint",
    "phase-gates",
    "gate-ledger",
    "community-evidence",
    "deny-register",
    "custom-code-rule",
    "codex-access-contract",
    "changed-files",
    "mechanical-checks",
    "intervention-balance",
    "ryan-report",
}


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


def run_git(*args: str) -> tuple[int, str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return proc.returncode, proc.stdout.strip()


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

    custom_decisions = load_jsonl(GOV / "custom-code-decisions.jsonl")
    custom_required = {
        "id",
        "status",
        "native_gap",
        "requirement_proof",
        "existing_alternatives_checked",
        "alternative_failure_evidence",
        "scope",
        "interface",
        "state_ownership",
        "failure_mode",
        "kill_switch",
        "rollback",
        "tests",
        "maintenance_burden",
        "no_second_authority_reason",
    }
    for row in custom_decisions:
        missing = custom_required - set(row)
        require(not missing, f"custom-code decision {row.get('id')} missing {sorted(missing)}")
        require(row["status"] in {"accepted", "rejected", "superseded"}, f"custom-code decision {row['id']} invalid status")
        for field in custom_required - {"alternative_failure_evidence", "existing_alternatives_checked", "status"}:
            require(isinstance(row[field], str) and len(row[field].strip()) >= 20, f"custom-code decision {row['id']} {field} too thin")
        require(
            isinstance(row["existing_alternatives_checked"], list) and len(row["existing_alternatives_checked"]) >= 2,
            f"custom-code decision {row['id']} must list alternatives checked",
        )
        require(
            isinstance(row["alternative_failure_evidence"], list) and len(row["alternative_failure_evidence"]) >= 2,
            f"custom-code decision {row['id']} must explain why alternatives are insufficient",
        )

    code, tracked = run_git("ls-files", "tools/*.py")
    if code == 0:
        tracked_tools = [line.strip() for line in tracked.splitlines() if line.strip()]
        governance_tools = [
            path
            for path in tracked_tools
            if path.startswith("tools/")
            and path.endswith(".py")
            and path not in {"tools/validate_governance.py", "tools/check_p1_environment.py"}
        ]
        for path in governance_tools:
            require(
                any(path in str(row.get("scope", "")) or path in str(row.get("interface", "")) for row in custom_decisions),
                f"custom-code decision required for {path}",
            )


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
    bad_wrong_reason: list[str] = []
    for path in bad:
        packet = load_json(path)
        errors = validate_task_packet(packet, rules)
        if not errors:
            bad_passed.append(path.name)
            continue
        expected_errors = packet.get("expected_errors")
        if not isinstance(expected_errors, list) or not expected_errors:
            bad_wrong_reason.append(f"{path.name}: missing expected_errors")
            continue
        missing_expected = [
            expected
            for expected in expected_errors
            if not isinstance(expected, str) or not any(expected in error for error in errors)
        ]
        if missing_expected:
            bad_wrong_reason.append(f"{path.name}: missing expected errors {missing_expected}; got {errors}")
    require(not bad_passed, f"bad fixtures unexpectedly passed: {bad_passed}")
    require(not bad_wrong_reason, f"bad fixtures failed for wrong reason: {bad_wrong_reason}")


def validate_schema_alignment() -> None:
    schema = load_json(GOV / "task-admission.schema.json")
    rules = load_json(GOV / "policy-rules.json")
    schema_required = set(schema.get("required", []))
    rule_required = set(rules.get("required_task_fields", []))
    require(schema_required == rule_required, "schema required fields do not match policy required fields")


def path_exists_for_evidence(path_value: str) -> bool:
    return (ROOT / path_value).exists()


def validate_review_packet(gate: dict[str, Any], phase: dict[str, Any]) -> None:
    gate_id = gate["id"]
    review_path_value = gate.get("review_packet")
    require(isinstance(review_path_value, str) and review_path_value.strip(), f"gate {gate_id} requires review_packet")
    require(review_path_value.startswith("governance/gate-reviews/"), f"gate {gate_id} review_packet must live under governance/gate-reviews")
    review_path = ROOT / review_path_value
    require(review_path.exists(), f"gate {gate_id} review packet missing: {review_path_value}")
    review = load_json(review_path)
    require(isinstance(review, dict), f"gate {gate_id} review packet must be an object")
    missing = REQUIRED_REVIEW_PACKET_FIELDS - set(review)
    require(not missing, f"gate {gate_id} review packet missing {sorted(missing)}")
    require(review["gate_id"] == gate_id, f"gate {gate_id} review packet gate_id mismatch")
    require(review["phase_name"] == phase["name"], f"gate {gate_id} review packet phase_name mismatch")
    require(isinstance(review["reviewed_commit"], str) and COMMIT_RE.match(review["reviewed_commit"]), f"gate {gate_id} review reviewed_commit must be a 40-char commit")
    require(isinstance(review["reviewer"], str) and len(review["reviewer"].strip()) >= 4, f"gate {gate_id} reviewer too thin")
    require(isinstance(review["reviewer_independence"], str) and len(review["reviewer_independence"].strip()) >= 20, f"gate {gate_id} reviewer_independence too thin")
    require(review["verdict"] in REVIEW_VERDICTS, f"gate {gate_id} invalid review verdict: {review['verdict']}")
    require(isinstance(review["summary"], str) and len(review["summary"].strip()) >= 40, f"gate {gate_id} review summary too thin")

    mechanical = review["mechanical_validation"]
    require(isinstance(mechanical, dict), f"gate {gate_id} mechanical_validation must be an object")
    for field in ["command", "ok", "output_summary"]:
        require(field in mechanical, f"gate {gate_id} mechanical_validation missing {field}")
    require(isinstance(mechanical["command"], str) and mechanical["command"].strip(), f"gate {gate_id} mechanical command required")
    require(isinstance(mechanical["ok"], bool), f"gate {gate_id} mechanical ok must be boolean")
    require(isinstance(mechanical["output_summary"], str) and len(mechanical["output_summary"].strip()) >= 20, f"gate {gate_id} mechanical output summary too thin")

    criteria = review["criteria_results"]
    require(isinstance(criteria, list) and criteria, f"gate {gate_id} criteria_results required")
    criteria_by_name: dict[str, dict[str, Any]] = {}
    for row in criteria:
        require(isinstance(row, dict), f"gate {gate_id} criteria rows must be objects")
        for field in ["criterion", "status", "evidence", "assessment"]:
            require(field in row, f"gate {gate_id} criteria row missing {field}")
        require(row["status"] in REVIEW_ITEM_STATUSES, f"gate {gate_id} invalid criterion status: {row['status']}")
        require(isinstance(row["evidence"], list) and row["evidence"], f"gate {gate_id} criterion evidence required: {row['criterion']}")
        require(isinstance(row["assessment"], str) and len(row["assessment"].strip()) >= 25, f"gate {gate_id} criterion assessment too thin: {row['criterion']}")
        criteria_by_name[row["criterion"]] = row
    require(set(criteria_by_name) == set(phase["completion_criteria"]), f"gate {gate_id} criteria must match phase completion criteria")

    anti_drift = review["anti_drift_results"]
    require(isinstance(anti_drift, list) and anti_drift, f"gate {gate_id} anti_drift_results required")
    drift_by_name: dict[str, dict[str, Any]] = {}
    for row in anti_drift:
        require(isinstance(row, dict), f"gate {gate_id} anti-drift rows must be objects")
        for field in ["requirement", "status", "evidence", "assessment"]:
            require(field in row, f"gate {gate_id} anti-drift row missing {field}")
        require(row["status"] in REVIEW_ITEM_STATUSES, f"gate {gate_id} invalid anti-drift status: {row['status']}")
        require(isinstance(row["evidence"], list) and row["evidence"], f"gate {gate_id} anti-drift evidence required: {row['requirement']}")
        require(isinstance(row["assessment"], str) and len(row["assessment"].strip()) >= 25, f"gate {gate_id} anti-drift assessment too thin: {row['requirement']}")
        drift_by_name[row["requirement"]] = row
    require(set(drift_by_name) == set(phase["anti_drift_requirements"]), f"gate {gate_id} anti-drift rows must match phase requirements")

    runtime = review["runtime_enforcement"]
    require(isinstance(runtime, dict), f"gate {gate_id} runtime_enforcement must be an object")
    require(runtime.get("status") in RUNTIME_ENFORCEMENT_STATUSES, f"gate {gate_id} invalid runtime enforcement status: {runtime.get('status')}")
    require(isinstance(runtime.get("assessment"), str) and len(runtime["assessment"].strip()) >= 30, f"gate {gate_id} runtime enforcement assessment too thin")

    blocking = review["blocking_findings"]
    require(isinstance(blocking, list), f"gate {gate_id} blocking_findings must be a list")
    require(isinstance(review["next_action"], str) and len(review["next_action"].strip()) >= 20, f"gate {gate_id} next_action too thin")

    if gate["status"] == "PASS":
        require(review["verdict"] == "pass", f"gate {gate_id} PASS requires review verdict pass")
        require(mechanical["ok"], f"gate {gate_id} PASS requires mechanical validation ok")
        require(not blocking, f"gate {gate_id} PASS requires no blocking findings")
        require(all(row["status"] == "pass" for row in criteria), f"gate {gate_id} PASS requires all criteria pass")
        require(all(row["status"] == "pass" for row in anti_drift), f"gate {gate_id} PASS requires all anti-drift rows pass")


def validate_action_assessment(gate_id: str, report: dict[str, Any], field: str) -> None:
    assessment = report[field]
    require(isinstance(assessment, dict), f"gate {gate_id} action report {field} must be an object")
    require(assessment.get("status") in GATE_ACTION_REPORT_STATUSES, f"gate {gate_id} action report {field} has invalid status")
    require(
        isinstance(assessment.get("assessment"), str) and len(assessment["assessment"].strip()) >= 25,
        f"gate {gate_id} action report {field} assessment too thin",
    )
    require(isinstance(assessment.get("evidence"), list), f"gate {gate_id} action report {field} evidence must be a list")


def validate_gate_action_report(gate: dict[str, Any], phase: dict[str, Any]) -> None:
    gate_id = gate["id"]
    report_path_value = gate.get("gate_action_report")
    require(isinstance(report_path_value, str) and report_path_value.strip(), f"gate {gate_id} requires gate_action_report")
    require(
        report_path_value.startswith("governance/gate-action-reports/"),
        f"gate {gate_id} gate_action_report must live under governance/gate-action-reports",
    )
    report_path = ROOT / report_path_value
    require(report_path.exists(), f"gate {gate_id} action report missing: {report_path_value}")
    report = load_json(report_path)
    require(isinstance(report, dict), f"gate {gate_id} action report must be an object")
    missing = REQUIRED_GATE_ACTION_REPORT_FIELDS - set(report)
    require(not missing, f"gate {gate_id} action report missing {sorted(missing)}")
    require(report["gate_id"] == gate_id, f"gate {gate_id} action report gate_id mismatch")
    require(report["phase_name"] == phase["name"], f"gate {gate_id} action report phase_name mismatch")
    require(report["gate_status"] == gate["status"], f"gate {gate_id} action report gate_status mismatch")
    require(report["action"] in GATE_ACTIONS, f"gate {gate_id} action report invalid action: {report['action']}")
    require(isinstance(report["reviewed_commit"], str) and COMMIT_RE.match(report["reviewed_commit"]), f"gate {gate_id} action report reviewed_commit must be a 40-char commit")
    require(isinstance(report["reviewer"], str) and len(report["reviewer"].strip()) >= 4, f"gate {gate_id} action report reviewer too thin")
    require(report["overall_status"] in GATE_ACTION_REPORT_STATUSES, f"gate {gate_id} action report invalid overall_status")

    if gate["status"] == "ACTIVE":
        code, changed_since_review = run_git("diff", "--name-only", f"{report['reviewed_commit']}..HEAD")
        require(code == 0, f"gate {gate_id} active action report reviewed_commit is not comparable to HEAD")
        changed_files = {line.strip() for line in changed_since_review.splitlines() if line.strip()}
        allowed_changes = {report_path_value}
        stale_changes = sorted(changed_files - allowed_changes)
        require(
            not stale_changes,
            f"gate {gate_id} active action report is stale; files changed after reviewed_commit: {stale_changes}",
        )

    scope = report["repo_review_scope"]
    require(isinstance(scope, list), f"gate {gate_id} action report repo_review_scope must be a list")
    require(REQUIRED_GATE_ACTION_SCOPE <= set(scope), f"gate {gate_id} action report missing review scope: {sorted(REQUIRED_GATE_ACTION_SCOPE - set(scope))}")

    for field in ["tracked_file_summary", "required_artifact_results"]:
        require(isinstance(report[field], (dict, list)), f"gate {gate_id} action report {field} malformed")
    for field in ["changed_files", "untracked_files", "blocking_findings"]:
        require(isinstance(report[field], list), f"gate {gate_id} action report {field} must be a list")

    mechanical = report["mechanical_checks"]
    require(isinstance(mechanical, list) and mechanical, f"gate {gate_id} action report mechanical_checks required")
    for row in mechanical:
        require(isinstance(row, dict), f"gate {gate_id} action report mechanical row must be an object")
        for field in ["id", "ok", "command", "output_summary"]:
            require(field in row, f"gate {gate_id} action report mechanical row missing {field}")
        require(isinstance(row["ok"], bool), f"gate {gate_id} action report mechanical ok must be boolean")
        require(isinstance(row["command"], str) and row["command"].strip(), f"gate {gate_id} action report mechanical command required")

    for field in [
        "plan_compliance_assessment",
        "community_evidence_assessment",
        "deny_register_assessment",
        "custom_code_assessment",
        "access_contract_assessment",
        "intervention_balance_assessment",
    ]:
        validate_action_assessment(gate_id, report, field)

    intervention = report["intervention_balance_assessment"]
    require(isinstance(intervention.get("requires_ryan_now"), bool), f"gate {gate_id} intervention requires_ryan_now must be boolean")
    require(
        isinstance(intervention.get("protected_boundary_pending"), bool),
        f"gate {gate_id} intervention protected_boundary_pending must be boolean",
    )
    require(
        isinstance(intervention.get("approval_packet_present"), bool),
        f"gate {gate_id} intervention approval_packet_present must be boolean",
    )
    require(
        isinstance(intervention.get("safe_local_next_actions"), list),
        f"gate {gate_id} intervention safe_local_next_actions must be a list",
    )
    if intervention["requires_ryan_now"]:
        require(
            phase["ryan_required"],
            f"gate {gate_id} may require Ryan now only when the phase is marked ryan_required",
        )
        require(
            not intervention["safe_local_next_actions"],
            f"gate {gate_id} cannot require Ryan while safe-local next actions remain",
        )

    require(isinstance(report["ryan_report"], str) and len(report["ryan_report"].strip()) >= 50, f"gate {gate_id} action report ryan_report too thin")

    if gate["status"] == "PASS":
        require(report["overall_status"] == "pass", f"gate {gate_id} PASS requires action report overall_status pass")
        require(not report["blocking_findings"], f"gate {gate_id} PASS requires action report with no blocking findings")
        require(
            all(row.get("ok") for row in mechanical),
            f"gate {gate_id} PASS requires all action report mechanical checks ok",
        )


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
            validate_review_packet(gate, phase_by_id[gate_id])
            validate_gate_action_report(gate, phase_by_id[gate_id])
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

        if status == "ACTIVE":
            if gate.get("review_packet"):
                validate_review_packet(gate, phase_by_id[gate_id])
            validate_gate_action_report(gate, phase_by_id[gate_id])

    require(set(gate_by_id) == set(phase_by_id), "gate ledger ids must match phase-gate ids")
    require(active_gates == [active_phase], f"exactly one ACTIVE gate must match active_phase; got {active_gates}, expected {[active_phase]}")


def validate_agent_entrypoint() -> None:
    root_agent_text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    agent_text = (GOV / "AGENTS.md").read_text(encoding="utf-8")
    readme_text = (GOV / "README.md").read_text(encoding="utf-8")
    for required in [
        "governance/AGENTS.md",
        "governance/codex-access-contract.md",
        "Do not use Windows PowerShell as the project logic layer",
        "/opt/openclaw",
    ]:
        require(required in root_agent_text, f"root AGENTS.md must point agents to {required}")
    for required in [
        "governance/blueprint.md",
        "governance/phase-gates.json",
        "governance/gate-ledger.json",
        "governance/codex-access-contract.md",
        "governance/gate-review-contract.md",
        "governance/gate-action-review-contract.md",
        "tools/validate_governance.py",
        "tools/generate_gate_action_report.py",
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
        "/opt/openclaw",
        "/opt/openclaw-data/runtime/oc",
        "Q:\\opt\\openclaw",
        "C:\\Users\\Ryan\\.codex\\openclaw\\ocssh.cmd",
        "~/.git-credentials-openclaw",
        "git push --dry-run origin codex/foundation-governance-bootstrap",
        "oc-net",
        "openclaw-gateway",
        "Q:\\",
        "PowerShell",
        "not use Windows PowerShell as the project logic layer",
        "Use the sudo helper only for protected VM/runtime/system operations",
    ]:
        require(required in text, f"codex access contract missing: {required}")
    require(
        "Q:\\opt\\openclaw-data\\workspace\\" not in text,
        "codex access contract must not point agents at retired workspace mounts",
    )


def validate_gate_review_contract() -> None:
    text = (GOV / "gate-review-contract.md").read_text(encoding="utf-8")
    for required in [
        "governance/gate-reviews/",
        "governance/gate-action-reports/",
        "every `completion_criteria` item",
        "every `anti_drift_requirements` item",
        "A phase may be marked `PASS` only when",
        "Independence Limits",
    ]:
        require(required in text, f"gate review contract missing: {required}")


def validate_gate_action_review_contract() -> None:
    text = (GOV / "gate-action-review-contract.md").read_text(encoding="utf-8")
    for required in [
        "governance/gate-action-reports/",
        "blueprint authority",
        "community evidence requirements",
        "deny register",
        "custom-code rule compliance",
        "Codex access contract compliance",
        "changed files and untracked files",
        "intervention balance",
        "Active Report Freshness",
        "the only allowed diff between `reviewed_commit` and `HEAD` is the report file itself",
        "Ryan-facing report text",
        "python3 tools/generate_gate_action_report.py",
        "Required Artifact Resolution",
        "Required artifacts may be literal repo paths or evidence categories",
        "Missing proof categories must stay blocking",
    ]:
        require(required in text, f"gate action review contract missing: {required}")


def validate_intervention_balance_contract() -> None:
    text = (GOV / "operating-method.md").read_text(encoding="utf-8")
    for required in [
        "Intervention Balance",
        "safe-local work",
        "Ryan intervention is allowed only when all three are true",
        "If a phase has `ryan_required=true`, that does not make every step human-blocked",
        "agents must continue bounded safe-local work",
    ]:
        require(required in text, f"operating method missing intervention balance rule: {required}")


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
        validate_gate_review_contract,
        validate_gate_action_review_contract,
        validate_intervention_balance_contract,
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

