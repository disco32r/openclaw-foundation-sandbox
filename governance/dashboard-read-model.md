# Dashboard Read Model

Dashboards are projections. They cannot mutate state.

## Allowed Inputs

- OpenClaw task state.
- Task Flow run state.
- Approval packet status.
- Evidence metadata.
- Candidate register.
- Deny register.
- Model/cost metrics.
- Security/audit output.
- Subagent/run closure state.

## Required Panels

- active tasks,
- failed gates,
- pending approvals,
- token/cost burn,
- model route,
- subagents open/closed,
- candidate status,
- rejected resurfacing attempts,
- stale evidence,
- protected-boundary stops.

## Forbidden Capabilities

- create task,
- mark task done,
- approve mutation,
- install skill/plugin,
- create cron/schedule,
- mutate model routing,
- mutate runtime config,
- write evidence,
- rewrite candidate or deny register.

Any dashboard action button must route to OpenClaw intake/approval. The dashboard itself never performs the action.

