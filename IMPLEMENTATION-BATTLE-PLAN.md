# Implementation Battle Plan

## Goal

Reach the tipping point without importing the old graveyard:

phone goal -> intake packet -> admission -> OpenClaw tracked builder task -> branch/test/evidence -> mobile result -> protected action approval packet -> denied pattern replay blocked.

## Phase Order

1. Foundation fork handoff.
2. Operating-method and governance files.
3. Blocking policy checks.
4. Private sandbox runtime.
5. Mobile operator loop.
6. Builder harness loop.
7. Proof harness.
8. First workflow admission.
9. Read-only dashboard/status.
10. Protected-domain expansion.

## Current Implemented Packet

This packet implements phases 0-3 as files and a validator:

```powershell
python foundation-packet/tools/validate_governance.py
```

The packet is designed to be copied into the clean `openclaw/openclaw` fork and mirrored to:

`/opt/openclaw`

## Stop Conditions

- Any task can start without intake/admission.
- Any bad fixture passes validation.
- Any public admin/control surface is introduced.
- Any custom scheduler/queue/approval/dashboard authority appears.
- Any protected action executes without approval.
- Any workflow is admitted without rollback proof.
