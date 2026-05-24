# Custom Code Rule

Custom code is allowed only when native OpenClaw primitives and existing open tooling cannot express the required gate.

## Allowed

- Intake/admission schemas.
- Policy checks and validators.
- Candidate and deny registers.
- Read-only dashboard/status projections.
- Thin adapters that submit to OpenClaw and never own state.
- Test/proof harness glue.

## Rejected By Default

- Scheduler.
- Queue.
- Approval ledger.
- Agent manager.
- Runtime orchestrator.
- Mutating dashboard.
- Mobile bot that bypasses OpenClaw.
- Middleware that owns tasks, approvals, schedules, routing, or promotion decisions.

## Required Proof Before Any Custom Code

Every custom-code proposal must have a `custom-code-decisions.jsonl` entry with:

- native gap,
- existing alternatives checked,
- scope,
- interface,
- state ownership,
- failure mode,
- kill switch,
- rollback,
- tests,
- maintenance burden,
- reason it does not become a second authority.

