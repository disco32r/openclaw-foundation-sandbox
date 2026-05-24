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

## Execution Rule

Only work the `ACTIVE` phase in `governance/gate-ledger.json` unless Ryan explicitly changes the phase or asks for analysis outside the gate. Future work discovered during a phase becomes intake, not direct execution.

## Access Rule

Do not use Windows PowerShell as the project logic layer. Source edits go through the mounted source repo or direct SSH/SFTP as `openclaw`; repo commands run from `/home/openclaw/foundation-source` with a POSIX shell. PowerShell is allowed only for local mount repair, not source rewriting, governance logic, or build orchestration.

## Forbidden Drift

Do not create a new scheduler, queue, approval ledger, runtime orchestrator, agent manager, mutating dashboard, mobile bypass bot, public admin surface, or local-model requirement. Use OpenClaw primitives first and record any native gap before proposing custom code.

## Proof Rule

Markdown can explain a decision, but it does not prove completion. Evidence must be a task record, check output, audit output, diff, branch, screenshot, cost report, rollback proof, approval packet, or candidate sandbox proof.

## Review Rule

No phase is complete until a gate review packet under `governance/gate-reviews/` gives a pass verdict for every completion criterion and anti-drift requirement. The validator checks packet structure; the reviewer supplies judgment.
