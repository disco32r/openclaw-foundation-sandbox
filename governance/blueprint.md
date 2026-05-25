# OpenClaw Personal OS Blueprint

This is the canonical implementation blueprint for the OpenClaw-first personal OS and mobile builder foundation. Chat context, dashboards, runtime scratch files, and old project artifacts are not authority.

## Authority

- The forked `openclaw/openclaw` source tree is the build source of truth.
- OpenClaw runtime primitives own tasks, Task Flow state, sessions, subagents, approvals, skills/plugins, model config, and evidence.
- Codex is the initial builder cockpit, not the system of record.
- Telegram, mobile UI, and Control UI are intake, status, and approval surfaces. They do not own tasks or approvals.
- Dashboards are read-only projections. They cannot admit, approve, schedule, install, promote, or mark work done.

## Tipping Point

The foundation reaches tipping point only when this drill passes end to end:

1. Owner submits a harmless repo goal from mobile.
2. The request becomes an intake packet.
3. Admission accepts or rejects it before builder execution.
4. Accepted builder work creates an OpenClaw-tracked task or Task Flow step.
5. Codex or ACP runs bounded work on a branch.
6. Tests or checks run.
7. Evidence is attached.
8. Mobile receives the result.
9. Dashboard shows the same state as a read-only projection.
10. A vague request is rejected.
11. A protected mutation produces an approval packet instead of execution.
12. A denied candidate or pattern cannot resurface without new evidence and a re-review condition.

## Work Lifecycle

All work follows this lifecycle:

`intake -> admission -> bounded_task -> proof -> promote_or_reject -> retrospective -> deny_register_update`

No agent may skip intake/admission because the next task feels obvious. Adjacent work becomes a new intake packet.


## Final System Domains

The final personal OS includes these governed domains, each admitted by the active phase process rather than ad hoc wiring:

- Software builder and repo operations.
- Host, VM, and runtime operations.
- Network monitoring and management.
- Home Assistant and device state.
- Digital-life read-only data surfaces.
- Finance and medical data surfaces, read-only first.

Network monitoring and management is first-class. It covers LAN health, WAN/VPN reachability, DNS/DHCP, router/switch/AP state, device inventory, Proxmox/VM connectivity, Home Assistant reachability, and service exposure checks. It starts read-only. Firewall, DNS, DHCP, VPN, port-forward, device, and network-segmentation mutations require an approval packet, affected-system list, validation command, and rollback command.

## Phase Gate Rule

`governance/phase-gates.json` defines the phases, required artifacts, required checks, completion criteria, anti-drift requirements, and Ryan approval requirements.

`governance/gate-ledger.json` records phase status. Exactly one phase may be `ACTIVE` at a time. Agents execute only the active phase unless Ryan explicitly changes direction.

`tools/validate_governance.py` is the local blocking check for this governance packet. A phase is complete only when the ledger says `PASS`, the required evidence exists, and the validator accepts the packet.

## Native Primitive Preference

Use existing OpenClaw primitives first: Tasks, Task Flow, sessions, subagents, approvals, skills/plugins, model configuration, and evidence artifacts.

Custom code is allowed only under `CUSTOM-CODE-RULE.md` after native-gap proof. Custom code may validate, adapt, project read-only status, or test. It may not become a second authority for tasks, approvals, schedules, routing, promotion, or dashboard truth.

## Community Evidence Rule

Community evidence is required for adopting foundation candidates, integrations, dashboards, builders, or proof harnesses. It must be recorded in `governance/candidate-register.jsonl` with source URL, pinned version or commit, evidence grade, score, verdict, and re-review condition.

Community evidence can nominate and support choices, but local reproducible proof wins. A candidate that cannot pass sandbox setup, smoke, rollback, security, and cost checks does not become live.

## Anti-Drift Rule

Rejected tools, patterns, shortcuts, and old artifacts go in `governance/deny-register.jsonl`. Future agents must check it before reviving similar ideas.

The old project graveyard is quarantine/reference only. No old runtime code, relay code, life OS files, or experimental autonomy stack may be imported wholesale into the clean foundation.
