# Evidence Contract

Evidence is required for admission, promotion, completion, rollback, and rejection.

## Accepted Evidence

- OpenClaw task id and task state.
- Task Flow run state.
- Test command and output.
- Security audit command and output.
- Health/readiness check output.
- Git diff or branch reference.
- Screenshot or rendered UI proof.
- Cost/token report.
- Rollback command and rollback output.
- Approval packet with apply, rollback, validation, risk, and affected systems.
- Candidate source links, pinned commits, and sandbox proof.

## Not Evidence

- Chat summary.
- Dashboard-only status.
- Markdown claim without command output or artifact.
- Agent confidence.
- "Looks good" review with no failure test.
- Placeholder approval proposal.

## Evidence Path Rule

Every admitted task must name the expected evidence path before work begins. Completion fails if the evidence path is missing or stale.

