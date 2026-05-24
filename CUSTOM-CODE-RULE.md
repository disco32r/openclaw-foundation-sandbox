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

## Required Qualification Before Any Custom Code

Every custom-code proposal must qualify before implementation. Qualification does not require Ryan intervention for safe-local governance, validation, proof, or read-only reporting glue. It does require a `custom-code-decisions.jsonl` entry proving the code is necessary and bounded.

- native gap,
- requirement proof,
- existing alternatives checked,
- why those alternatives are insufficient,
- scope,
- interface,
- state ownership,
- failure mode,
- kill switch,
- rollback,
- tests,
- maintenance burden,
- reason it does not become a second authority.

Ryan intervention is required only when the custom code crosses a protected boundary: runtime config, scheduler/cron, Docker/container/session state, network, Home Assistant, UniFi, secrets/auth, external accounts, public channels, or destructive cleanup.
