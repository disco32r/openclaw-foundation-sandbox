# Approval Request: Optional Docker Sandbox Runtime

## Decision Needed

Approve or reject creating a new isolated Docker/container sandbox for proving the OpenClaw private runtime and mobile-to-builder loop.

This is not required for Phase 0-3 governance implementation. It is useful for Phase 4+ runtime proof.

## Affected Systems

- Docker/container state on `openclaw@192.168.2.242`.
- Source files under `/opt/openclaw`.
- Runtime files under `/opt/openclaw-data/runtime/openclaw-foundation-sandbox`.
- Network exposure if ports are bound.

## Proposed Apply

Do not run until approved.

```sh
cd /opt/openclaw
# Use official OpenClaw Docker/VM deployment instructions pinned to the selected upstream commit.
# Bind admin/control surfaces to localhost or private network only.
```

## Required Safety Conditions

- No public admin surface.
- No public tunnel.
- No web terminal exposed.
- No broad file manager exposed.
- Persistent volume lives under the foundation sandbox path.
- Hosted-model secrets are supplied by reference, not copied into evidence.
- Exec approvals enabled before protected mutation tests.

## Validation

```sh
docker ps
curl -fsS http://127.0.0.1:<private-port>/healthz
curl -fsS http://127.0.0.1:<private-port>/readyz
openclaw security audit --deep
```

Also run an external exposure check from a separate network path before declaring private UI safe.

## Rollback

```sh
docker compose down
docker ps
```

Remove only the foundation sandbox container/volume names listed in the approval-specific manifest.

## Risk

Main risk is accidentally creating a second active OpenClaw runtime or exposing admin surfaces. The mitigation is private binding, explicit container names, no public tunnel, and rollback proof before any live adoption.
