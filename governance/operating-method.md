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

### Session-Scoped Approval Proxy

Ryan may explicitly delegate approval authority inside the active Codex/OpenClaw work session. When that happens, the agent may execute a previously reviewed protected-boundary packet as Ryan's approval proxy if all of these are true:

- the delegation text is recorded as governance evidence,
- the action has exact apply, validation, rollback, affected systems, risk, downtime estimate, and stop conditions,
- the action remains within the delegated scope,
- the agent records command output and rollback evidence,
- the action does not approve secrets disclosure, public posting, payment, medical/financial mutation, device actuation, or broad network/security changes beyond the packet scope.

Session delegation does not mark a phase complete. It only satisfies the human-approval precondition for the bounded action. The phase still needs concrete evidence, gate review, gate action report, validator pass, and ledger update.

### Work-Conserving Blocked Gates

A blocked active gate is not permission to idle. If Ryan explicitly directs continuation, agents must keep doing safe-local work that supports the active phase or prepares downstream phases, while preserving pass order. Downstream prep may create intake packets, read-only reviews, candidate evidence, test harnesses, and approval packets, but it may not mark a later phase `PASS` before earlier gates pass.

### Critical Updates

Critical blockers, approval requests, and failed communication paths must be surfaced through the configured owner channel when available. If Telegram or another owner channel is not proven by a current real send/receive check, agents must use the current Codex thread as fallback and keep repairing the native channel.

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
