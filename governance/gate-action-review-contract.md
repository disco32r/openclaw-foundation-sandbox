# Gate Action Review Contract

A gate action is any phase status movement, pass review, blocked review, or activation claim recorded in `governance/gate-ledger.json`.

Every gate action must produce a repo-wide compliance report under:

`governance/gate-action-reports/`

The report is separate from the judgment packet in `governance/gate-reviews/`. The review packet decides whether phase criteria are met. The gate action report proves the repo was checked against the whole plan before that decision is used.

## Required Coverage

Each gate action report must cover:

- blueprint authority,
- phase definition and gate ledger alignment,
- active phase status,
- required artifacts,
- required checks,
- community evidence requirements,
- deny register and rejected-pattern replay,
- custom-code rule compliance,
- Codex access contract compliance,
- changed files and untracked files,
- mechanical check output,
- intervention balance,
- blocking findings,
- Ryan-facing report text.

## Required Command

Generate a report from the repo root:

```sh
python3 tools/generate_gate_action_report.py --gate P1 --action blocked_review --out governance/gate-action-reports/P1-foundation-repo-YYYYMMDDTHHMMZ.json
```

Then reference the report from the matching gate ledger row as `gate_action_report` and include it in that gate's evidence list.

## Required Artifact Resolution

Required artifacts may be literal repo paths or evidence categories. A literal path must exist in the repo. An evidence category must be satisfied by a matching `governance/gate-ledger.json` evidence row whose path exists and whose description names the required proof category. Missing proof categories must stay blocking even when adjacent preflight evidence exists.

## Promotion Rule

A phase may be marked `PASS` only when:

- the gate review packet verdict is `pass`,
- the gate action report exists,
- the gate action report `overall_status` is `pass`,
- the gate action report has no blocking findings,
- the validator accepts both the review packet and the action report.

For `ACTIVE` gates, blocking findings are allowed only when the gate disposition says the phase is active but not pass-qualified.

## Active Report Freshness

For the currently `ACTIVE` gate, the action report must review the current source state. Because the report is committed after it is generated, the only allowed diff between `reviewed_commit` and `HEAD` is the report file itself. Any other changed file means the active report is stale and must be regenerated.

## Intervention Balance Rule

Every gate action report must state whether Ryan is needed now. The default answer is no. A report may say Ryan is needed only when the next action crosses a protected boundary and no safe-local evidence, review, or approval-packet drafting remains.

The report must also list safe-local next actions. If the list is empty while the phase is not pass-qualified, the report must identify the exact protected boundary, affected systems, validation command, rollback command, and stop condition.
