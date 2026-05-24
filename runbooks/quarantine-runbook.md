# Reversible Quarantine Runbook

Quarantine old workspace material by moving it, not deleting it.

## Quarantine Root

`/opt/openclaw-data/workspace/_quarantine`

## Candidate Old Material

Initial read-only inventory found old or potentially confusing top-level material:

- `/opt/openclaw-data/workspace/lifeos`
- `/opt/openclaw-data/workspace/rook`
- `/opt/openclaw-data/workspace/openwebui`
- `/opt/openclaw-data/workspace/openwebui-*.png`
- `/opt/openclaw-data/workspace/LIFEOS_MIGRATION_APPROVAL.md`

Do not move active authority paths without approval:

- `/opt/openclaw-data/workspace/openclaw-native`
- `/opt/openclaw-data/workspace/openclaw-plugins`
- `/opt/openclaw-data/workspace/skills`
- `/opt/openclaw-data/workspace/memory`
- `/opt/openclaw-data/workspace/runtime-evidence`
- `/opt/openclaw-data/workspace/runtime-trust`

## Required Manifest Fields

Each quarantine batch must write `manifest.jsonl` with:

- original path
- quarantine path
- reason
- command
- actor
- timestamp
- rollback command

## Rollback

Move each manifest entry back to its original path only after confirming no newer replacement exists.

