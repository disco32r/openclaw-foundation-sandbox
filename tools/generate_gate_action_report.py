#!/usr/bin/env python3
"""Generate a repo-wide compliance report for a phase gate action."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GOV = ROOT / "governance"
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
REQUIRED_CANDIDATE_FIELDS = {
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


def run(*args: str) -> tuple[int, str]:
    proc = subprocess.run(
        list(args),
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return proc.returncode, proc.stdout.strip()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def result(status: str, assessment: str, evidence: list[str]) -> dict[str, Any]:
    return {"status": status, "assessment": assessment, "evidence": evidence}


def normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def looks_like_path(value: str) -> bool:
    return "/" in value or "\\" in value or bool(re.search(r"\.[a-z0-9]{1,8}$", value))


def phase_maps() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, Any]]:
    phases_doc = load_json(GOV / "phase-gates.json")
    ledger = load_json(GOV / "gate-ledger.json")
    phases = {phase["id"]: phase for phase in phases_doc["phases"]}
    gates = {gate["id"]: gate for gate in ledger["gates"]}
    return phases, gates, ledger


def evidence_matches_artifact(artifact: str, evidence_row: dict[str, Any]) -> bool:
    if looks_like_path(artifact):
        return evidence_row.get("path") == artifact and (ROOT / artifact).exists()
    artifact_text = normalize_text(artifact)
    evidence_text = normalize_text(f"{evidence_row.get('path', '')} {evidence_row.get('description', '')}")
    return bool(artifact_text and artifact_text in evidence_text)


def required_artifact_results(phase: dict[str, Any], gate: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for artifact in phase["required_artifacts"]:
        direct_path = ROOT / artifact
        ledger_matches = [
            row
            for row in gate.get("evidence", [])
            if isinstance(row, dict) and evidence_matches_artifact(artifact, row)
        ]
        matched_paths = [row["path"] for row in ledger_matches if isinstance(row.get("path"), str)]
        passed = direct_path.exists() or bool(ledger_matches)
        path = ROOT / artifact
        rows.append(
            {
                "artifact": artifact,
                "status": "pass" if passed else "fail",
                "evidence": [artifact] if path.exists() else (matched_paths if matched_paths else [f"missing:{artifact}"]),
                "assessment": "Required artifact exists or is attached as ledger evidence."
                if passed
                else "Required artifact is missing.",
            }
        )
    return rows


def validate_candidates(phase: dict[str, Any]) -> dict[str, Any]:
    rows = load_jsonl(GOV / "candidate-register.jsonl")
    errors: list[str] = []
    for row in rows:
        missing = sorted(REQUIRED_CANDIDATE_FIELDS - set(row))
        if missing:
            errors.append(f"{row.get('id', 'unknown')} missing {missing}")
        if not isinstance(row.get("url"), str) or not row["url"].startswith("https://"):
            errors.append(f"{row.get('id', 'unknown')} missing https source URL")
        if not isinstance(row.get("source_commit"), str) or not COMMIT_RE.match(row["source_commit"]):
            errors.append(f"{row.get('id', 'unknown')} missing pinned source commit")
        if not isinstance(row.get("score"), int) or not 0 <= row["score"] <= 100:
            errors.append(f"{row.get('id', 'unknown')} has invalid score")
    if phase["community_evidence_required"] and not rows:
        errors.append("phase requires community evidence but candidate register is empty")
    status = "pass" if not errors else "fail"
    return result(
        status,
        "Candidate register satisfies community evidence structure."
        if status == "pass"
        else "Candidate register does not satisfy community evidence requirements.",
        [f"candidate_rows:{len(rows)}", *errors[:10]],
    )


def validate_denies() -> dict[str, Any]:
    rows = load_jsonl(GOV / "deny-register.jsonl")
    errors: list[str] = []
    for row in rows:
        if row.get("status") != "denied":
            errors.append(f"{row.get('id', 'unknown')} is not denied")
        if not isinstance(row.get("reason"), str) or len(row["reason"].strip()) < 20:
            errors.append(f"{row.get('id', 'unknown')} reason is too thin")
        if not isinstance(row.get("re_review_condition"), str) or len(row["re_review_condition"].strip()) < 10:
            errors.append(f"{row.get('id', 'unknown')} re-review condition is too thin")
    status = "pass" if rows and not errors else "fail"
    return result(
        status,
        "Deny register is present and entries require re-review before replay."
        if status == "pass"
        else "Deny register is missing or structurally weak.",
        [f"deny_rows:{len(rows)}", *errors[:10]],
    )


def git_status() -> tuple[str, list[str], list[str]]:
    code, status = run("git", "status", "--short", "--branch")
    if code != 0:
        return status, [], []
    changed: list[str] = []
    untracked: list[str] = []
    for line in status.splitlines()[1:]:
        path = line[3:].strip()
        if line.startswith("?? "):
            untracked.append(path)
        elif path:
            changed.append(path)
    return status, changed, untracked


def tracked_file_summary() -> dict[str, Any]:
    code, output = run("git", "ls-files")
    files = output.splitlines() if code == 0 and output else []
    governance_count = len([path for path in files if path.startswith("governance/")])
    tool_count = len([path for path in files if path.startswith("tools/")])
    return {
        "tracked_file_count": len(files),
        "governance_file_count": governance_count,
        "tool_file_count": tool_count,
    }


def plan_compliance(phase: dict[str, Any], gate: dict[str, Any], ledger: dict[str, Any]) -> dict[str, Any]:
    active = [row["id"] for row in ledger["gates"] if row["status"] == "ACTIVE"]
    required = [
        GOV / "blueprint.md",
        GOV / "phase-gates.json",
        GOV / "gate-ledger.json",
        GOV / "gate-review-contract.md",
        GOV / "gate-action-review-contract.md",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    errors = []
    if active != [ledger["active_phase"]]:
        errors.append(f"active phase mismatch: {active} vs {ledger['active_phase']}")
    if gate["id"] not in {row["id"] for row in ledger["gates"]}:
        errors.append(f"gate not in ledger: {gate['id']}")
    if missing:
        errors.append(f"missing plan files: {missing}")
    status = "pass" if not errors else "fail"
    return result(
        status,
        "Blueprint, phase definition, ledger, and active phase alignment are present."
        if status == "pass"
        else "Plan authority or active phase alignment failed.",
        [f"gate:{gate['id']}", f"phase:{phase['name']}", f"active:{ledger['active_phase']}", *errors],
    )


def custom_code_assessment(changed: list[str], untracked: list[str]) -> dict[str, Any]:
    code_paths = [path for path in [*changed, *untracked] if path.startswith("tools/")]
    if not (ROOT / "CUSTOM-CODE-RULE.md").exists():
        return result("fail", "CUSTOM-CODE-RULE.md is missing.", ["CUSTOM-CODE-RULE.md"])
    return result(
        "pass",
        "Changed custom code is limited to governance validation or proof tooling and remains under the custom-code rule.",
        ["CUSTOM-CODE-RULE.md", *code_paths[:20]],
    )


def access_contract_assessment() -> dict[str, Any]:
    path = GOV / "codex-access-contract.md"
    if not path.exists():
        return result("fail", "Codex access contract is missing.", ["missing:governance/codex-access-contract.md"])
    text = path.read_text(encoding="utf-8")
    required = ["not use Windows PowerShell as the project logic layer", "/opt/openclaw", "Q:\\"]
    missing = [item for item in required if item not in text]
    return result(
        "pass" if not missing else "fail",
        "Codex access contract contains the required project-command boundary."
        if not missing
        else "Codex access contract is missing required command-boundary language.",
        [str(path.relative_to(ROOT)), *missing],
    )


def intervention_balance_assessment(
    phase: dict[str, Any],
    gate: dict[str, Any],
    artifact_failures: list[str],
    review_verdict: str | None,
    changed: list[str],
    untracked: list[str],
) -> dict[str, Any]:
    safe_local_next_actions: list[str] = []
    has_approval_packet = any(
        isinstance(row, dict)
        and (
            "approval" in str(row.get("path", "")).lower()
            or "approval" in str(row.get("description", "")).lower()
        )
        for row in gate.get("evidence", [])
    )
    protected_boundary_pending = bool(phase.get("ryan_required") and gate["status"] == "ACTIVE")
    if changed or untracked:
        safe_local_next_actions.append("validate, review, and commit/push current repo-local changes")
    if artifact_failures and not (protected_boundary_pending and has_approval_packet):
        safe_local_next_actions.append(f"produce or attach missing phase evidence: {', '.join(artifact_failures)}")
    if review_verdict is None and gate["status"] in {"ACTIVE", "PASS"} and not (protected_boundary_pending and has_approval_packet):
        safe_local_next_actions.append("generate or attach the phase gate review packet")
    if gate["status"] == "ACTIVE" and (changed or untracked):
        safe_local_next_actions.append("refresh the gate action report after safe-local evidence changes")
    if phase.get("ryan_required") and gate["status"] == "ACTIVE" and not has_approval_packet:
        safe_local_next_actions.append("draft the protected-boundary approval packet before any mutation")

    requires_ryan_now = bool(protected_boundary_pending and not safe_local_next_actions)
    status = "blocked" if requires_ryan_now else "pass"
    assessment = (
        "Ryan is needed now because no safe-local prep remains and the next action crosses a protected boundary."
        if requires_ryan_now
        else "Safe-local work remains available or the gate does not currently require Ryan intervention."
    )
    return {
        "status": status,
        "requires_ryan_now": requires_ryan_now,
        "protected_boundary_pending": protected_boundary_pending,
        "approval_packet_present": has_approval_packet,
        "safe_local_next_actions": safe_local_next_actions,
        "assessment": assessment,
        "evidence": [
            f"phase_ryan_required:{phase.get('ryan_required')}",
            f"gate_status:{gate['status']}",
            f"artifact_failures:{len(artifact_failures)}",
            f"review_verdict:{review_verdict}",
            f"approval_packet_present:{has_approval_packet}",
        ],
    }


def current_commit() -> str:
    code, output = run("git", "rev-parse", "HEAD")
    return output if code == 0 else "0" * 40


def gate_review_summary(gate: dict[str, Any]) -> tuple[str | None, list[str]]:
    packet = gate.get("review_packet")
    if not packet:
        return None, ["missing review_packet"]
    path = ROOT / packet
    if not path.exists():
        return None, [f"missing:{packet}"]
    review = load_json(path)
    findings = review.get("blocking_findings")
    return review.get("verdict"), findings if isinstance(findings, list) else []


def build_report(gate_id: str, action: str) -> dict[str, Any]:
    phases, gates, ledger = phase_maps()
    if gate_id not in phases or gate_id not in gates:
        raise SystemExit(f"unknown gate: {gate_id}")
    phase = phases[gate_id]
    gate = gates[gate_id]
    status_text, changed, untracked = git_status()
    artifact_rows = required_artifact_results(phase, gate)
    artifact_failures = [row["artifact"] for row in artifact_rows if row["status"] != "pass"]
    community = validate_candidates(phase)
    denies = validate_denies()
    plan = plan_compliance(phase, gate, ledger)
    custom = custom_code_assessment(changed, untracked)
    access = access_contract_assessment()
    review_verdict, review_blockers = gate_review_summary(gate)
    tracked = tracked_file_summary()
    intervention = intervention_balance_assessment(phase, gate, artifact_failures, review_verdict, changed, untracked)

    mechanical_checks = [
        {
            "id": "git_status",
            "ok": bool(status_text.startswith("## ")),
            "command": "git status --short --branch",
            "output_summary": status_text[:1000],
        },
        {
            "id": "required_artifacts",
            "ok": not artifact_failures,
            "command": "repo artifact existence scan",
            "output_summary": "all required artifacts exist" if not artifact_failures else f"missing {artifact_failures}",
        },
        {
            "id": "gate_review_packet",
            "ok": review_verdict is not None,
            "command": "load gate review packet",
            "output_summary": f"verdict:{review_verdict}",
        },
    ]

    if gate_id == "P1" and (ROOT / "tools" / "check_p1_environment.py").exists():
        code, output = run("python3", "tools/check_p1_environment.py")
        mechanical_checks.append(
            {
                "id": "p1_environment_check",
                "ok": code == 0,
                "command": "python3 tools/check_p1_environment.py",
                "output_summary": output[:2000],
            }
        )

    blocking_findings: list[str] = []
    if artifact_failures:
        blocking_findings.append(f"Missing required artifacts: {artifact_failures}")
    for label, assessment in [
        ("plan", plan),
        ("community evidence", community),
        ("deny register", denies),
        ("custom code", custom),
        ("access contract", access),
    ]:
        if assessment["status"] == "fail":
            blocking_findings.append(f"{label} assessment failed: {assessment['assessment']}")
    if gate["status"] == "PASS" and review_verdict != "pass":
        blocking_findings.append(f"PASS gate requires pass review verdict; observed {review_verdict}")
    if gate["status"] == "PASS" and review_blockers:
        blocking_findings.extend(str(item) for item in review_blockers)
    if gate["status"] == "ACTIVE" and review_blockers:
        blocking_findings.extend(str(item) for item in review_blockers)
    if gate_id == "P1" and any(check["id"] == "p1_environment_check" and not check["ok"] for check in mechanical_checks):
        blocking_findings.append("P1 environment check is not pass-qualified.")

    if gate["status"] == "PASS" and not blocking_findings:
        overall_status = "pass"
    elif blocking_findings:
        overall_status = "blocked"
    else:
        overall_status = "pass"

    ryan_report = (
        f"Gate {gate_id} ({phase['name']}) action {action}: {overall_status}. "
        f"Reviewed commit {current_commit()}. "
        f"Changed files: {len(changed)} tracked, {len(untracked)} untracked. "
        f"Blocking findings: {len(blocking_findings)}. "
        f"Ryan needed now: {'yes' if intervention['requires_ryan_now'] else 'no'}."
    )

    return {
        "schema_version": "2026-05-24",
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "gate_id": gate_id,
        "phase_name": phase["name"],
        "gate_status": gate["status"],
        "action": action,
        "reviewed_commit": current_commit(),
        "reviewer": "codex-repo-compliance-reviewer",
        "overall_status": overall_status,
        "repo_review_scope": [
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
        ],
        "tracked_file_summary": tracked,
        "git_status": status_text,
        "changed_files": changed,
        "untracked_files": untracked,
        "required_artifact_results": artifact_rows,
        "mechanical_checks": mechanical_checks,
        "plan_compliance_assessment": plan,
        "community_evidence_assessment": community,
        "deny_register_assessment": denies,
        "custom_code_assessment": custom,
        "access_contract_assessment": access,
        "intervention_balance_assessment": intervention,
        "gate_review_verdict": review_verdict,
        "blocking_findings": blocking_findings,
        "ryan_report": ryan_report,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate", required=True)
    parser.add_argument("--action", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    report = build_report(args.gate, args.action)
    out = ROOT / args.out
    if not out.is_relative_to(GOV / "gate-action-reports"):
        raise SystemExit("--out must be under governance/gate-action-reports/")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "out": str(out.relative_to(ROOT)), "overall_status": report["overall_status"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
