# Operating Method

Every unit of work must move through exactly this lifecycle:

1. Intake
2. Admission
3. Bounded task
4. Proof
5. Promotion or rejection
6. Retrospective
7. Deny-register update

## Intake

Requests from Codex, mobile, chat, Control UI, cron, standing orders, or human conversation become intake packets. They do not become active work directly.

Required fields:

- goal
- expected value
- data class
- risk class
- allowed tools
- model class
- evidence target
- stop condition
- budget
- rollback
- owner
- protected-boundary flags

## Admission

Admission returns one of:

- `reject`
- `needs_clarification`
- `sandbox`
- `approval_required`
- `admit`

Missing evidence, rollback, budget, data class, risk class, or stop condition is an automatic rejection.

## Bounded Task

Admitted work becomes an OpenClaw-tracked task or Task Flow step. It must have fixed scope, max runtime, max spend, max tool calls, max subagents, allowed model class, and terminal condition.

Agents may not expand scope. Adjacent work becomes a new intake packet.

## Intervention Balance

Agents must keep moving on safe-local work without Ryan intervention. Safe-local work includes source inspection, repo-local edits, validators, fixture checks, evidence generation, gate reviews, gate action reports, approval packet drafting, and read-only runtime discovery.

Ryan intervention is allowed only when all three are true:

- the next action crosses a protected boundary listed in `governance/policy-rules.json`,
- no remaining safe-local evidence or prep work can reduce uncertainty first,
- the request includes exact apply, rollback, validation, affected systems, risk, and stop conditions.

If a phase has `ryan_required=true`, that does not make every step human-blocked. It means phase promotion cannot be claimed until the exact protected action or approval requirement has been satisfied. Before that point, agents must continue bounded safe-local work and report the remaining protected boundary directly.

## Proof

Completion requires concrete evidence: task record, test output, audit output, diff, screenshot, health check, cost report, rollback proof, approval packet, or failure proof.

Chat summaries and dashboards are not proof.

## Promotion Or Rejection

Passing proof may promote work from `sandbox` to `admitted`, `admitted` to `live`, or `active` to `done`.

Failed proof creates rejection, quarantine, or repair intake.

Protected actions stop at approval packet, not execution.

## Retrospective

Each completed or rejected task records what happened, what proved it, what failed, and what must not recur.

Retrospectives are short structured records, not essays.

## Deny-Register Update

Rejected tools, task shapes, patterns, workflows, and unsafe shortcuts are recorded in `deny-register.jsonl` with reason and re-review condition.

Future agents must check this before re-nominating or rebuilding similar work.
