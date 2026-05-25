# OpenClaw Foundation Packet

This packet is the implementation seed for the OpenClaw-first personal OS / mobile builder.

The runtime foundation is a clean fork of `openclaw/openclaw`, not this cockpit workspace and not any old `lifeos`, `rook`, `openwebui`, or relay artifact. This packet may be copied into the clean fork after it passes validation.

## Authority

- OpenClaw owns runtime state: tasks, Task Flow, sessions, subagents, approvals, cron, model config, skills/plugins, and evidence.
- Codex is the initial builder cockpit only.
- Mobile/Telegram/Control UI is intake, status, and approval surface only.
- Dashboards are read-only projections.
- External tools may test, scan, route model calls, or meter cost; they may not own tasks, approvals, schedules, or runtime truth.

## Tipping Point

The foundation reaches tipping point when a phone can submit a software-builder goal, OpenClaw admits or rejects it, a tracked builder task runs on a branch, evidence is attached, the result returns to mobile, protected actions stop for approval, and rejected tools cannot resurface without new evidence.

## Current VM Location

Clean VM file workspace:

`/opt/openclaw`

Discovery marker:

`/opt/openclaw-data/workspace/OPENCLAW_FOUNDATION_SANDBOX_PATH.txt`

Quarantine root:

`/opt/openclaw-data/workspace/_quarantine`
