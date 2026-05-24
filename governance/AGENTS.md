# Governance Agent Rules

This directory defines the project guardrails. Before changing governance, admission, candidates, routing, skills/plugins, approvals, dashboards, or builder flow, read these files:

- `governance/blueprint.md`
- `governance/phase-gates.json`
- `governance/gate-ledger.json`
- `governance/operating-method.md`
- `governance/evidence-contract.md`
- `governance/community-evidence-contract.md`
- `CUSTOM-CODE-RULE.md`

## Required Check

Run from repo root before and after governance changes:

```sh
python3 tools/validate_governance.py
```

If it fails, do not claim the phase is complete.

## Execution Rule

Only work the `ACTIVE` phase in `governance/gate-ledger.json` unless Ryan explicitly changes the phase or asks for analysis outside the gate. Future work discovered during a phase becomes intake, not direct execution.

## Forbidden Drift

Do not create a new scheduler, queue, approval ledger, runtime orchestrator, agent manager, mutating dashboard, mobile bypass bot, public admin surface, or local-model requirement. Use OpenClaw primitives first and record any native gap before proposing custom code.

## Proof Rule

Markdown can explain a decision, but it does not prove completion. Evidence must be a task record, check output, audit output, diff, branch, screenshot, cost report, rollback proof, approval packet, or candidate sandbox proof.
