#!/usr/bin/env python3
"""Validate the OpenClaw foundation governance packet without external deps."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GOV = ROOT / "governance"


REQUIRED_FILES = [
    ROOT / "FOUNDATION.md",
    ROOT / "CUSTOM-CODE-RULE.md",
    GOV / "README.md",
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
    GOV / "policy-rules.json",
]


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
        "re_review_condition",
    }
    for row in candidates:
        missing = candidate_required - set(row)
        require(not missing, f"candidate {row.get('id')} missing {sorted(missing)}")
        require(isinstance(row["score"], int) and 0 <= row["score"] <= 100, f"candidate {row['id']} invalid score")

    denies = load_jsonl(GOV / "deny-register.jsonl")
    require(denies, "deny register must not be empty")
    deny_required = {"id", "pattern", "status", "reason", "re_review_condition"}
    for row in denies:
        missing = deny_required - set(row)
        require(not missing, f"deny entry {row.get('id')} missing {sorted(missing)}")
        require(row["status"] == "denied", f"deny entry {row['id']} status must be denied")


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


def main() -> int:
    checks = [
        validate_required_files,
        validate_registers,
        validate_schema_alignment,
        validate_fixtures,
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
