# Governance Agent Rules

This directory defines the project guardrails. Before changing governance, admission, candidates, routing, skills/plugins, approvals, dashboards, or builder flow, read these files:

- `governance/blueprint.md`
- `governance/phase-gates.json`
- `governance/gate-ledger.json`
- `governance/operating-method.md`
- `governance/evidence-contract.md`
- `governance/community-evidence-contract.md`
- `governance/codex-access-contract.md`
- `governance/gate-review-contract.md`
- `governance/gate-action-review-contract.md`
- `CUSTOM-CODE-RULE.md`

## Required Check

Run from repo root before and after governance changes:

```sh
python3 tools/validate_governance.py
```

If it fails, do not claim the phase is complete.

For P1 foundation repo work, also run:

```sh
python3 tools/check_p1_environment.py
```

For every phase gate action, generate and attach a repo-wide action report before claiming status:

```sh
python3 tools/generate_gate_action_report.py --gate P1 --action blocked_review --out governance/gate-action-reports/P1-foundation-repo-YYYYMMDDTHHMMZ.json
```

## Execution Rule

Only work the `ACTIVE` phase in `governance/gate-ledger.json` unless Ryan explicitly changes the phase, delegates session-scoped approval-proxy authority, or asks for safe-local downstream preparation while a gate is blocked. Future work discovered during a phase becomes intake, not direct execution, and downstream prep cannot mark a later phase `PASS` before earlier gates pass.

## Access Rule

Do not use Windows PowerShell as the project logic layer. Source edits go through the mounted source repo or direct SSH/SFTP as `openclaw`; repo commands run through `C:\Users\Ryan\.codex\openclaw\ocssh.cmd` or an equivalent POSIX shell from `/opt/openclaw`. PowerShell is allowed only for local mount repair, not source rewriting, governance logic, or build orchestration.

Current durable locations are `/opt/openclaw` for source and `/opt/openclaw-data/runtime/oc` for runtime state. The live Docker surface is project `oc`, network `oc-net`, and container `openclaw-gateway`. Historical evidence may mention retired paths; do not use those as current targets.

## Forbidden Drift

Do not create a new scheduler, queue, approval ledger, runtime orchestrator, agent manager, mutating dashboard, mobile bypass bot, public admin surface, or local-model requirement. Use OpenClaw primitives first and record any native gap before proposing custom code.

## Proof Rule

Markdown can explain a decision, but it does not prove completion. Evidence must be a task record, check output, audit output, diff, branch, screenshot, cost report, rollback proof, approval packet, or candidate sandbox proof.

## Review Rule

No phase is complete until a gate review packet under `governance/gate-reviews/` gives a pass verdict for every completion criterion and anti-drift requirement. The validator checks packet structure; the reviewer supplies judgment.
