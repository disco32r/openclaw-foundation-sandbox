# P5 Sandbox Docker Remediation Approval Request

## Decision

Approve or reject a protected runtime/container remediation so OpenClaw's native sandboxed agent execution can reach Docker and produce the P5 owner-mobile protected-action approval or terminal-denial proof.

## Why This Exists

P5 is active and blocked. Fresh evidence in `governance/evidence/p5-current-state-sandbox-blocker-20260525T153133Z.json` shows:

- VM, memory, gateway health/readiness, hosted model route, and native Telegram channel are healthy.
- Exec policy is `ask=always`, `security=allowlist`, and Telegram exec approvals are configured.
- The final protected-action drills are native task records, but they fail before approval/denial because sandbox mode is `all` and the node-side Docker sandbox backend cannot find `docker` in `PATH`.

The source `docker-compose.yml` documents the native Docker deployment requirement: sandbox mode requires Docker CLI in the OpenClaw image plus `/var/run/docker.sock` mounted with the host Docker group.

## Affected Systems

- VM: OpenClaw VM `openclaw` at `/opt/openclaw`.
- Docker host daemon and socket: `/var/run/docker.sock`.
- Runtime container: `openclaw-gateway`.
- Docker network/project surface: `oc-net`, `openclaw-gateway`, loopback ports `127.0.0.1:18789-18790`.
- Runtime config root: `/opt/openclaw-data/runtime/oc`.
- New local Docker image tag: `openclaw:p5-sandbox-cli-f74f1e25af`.
- Sandbox image: `openclaw-sandbox:bookworm-slim`.
- Native Telegram approval path for the follow-up P5 drill.

## Exact Apply Command

Run only after approval:

```sh
cd /opt/openclaw
P5_SANDBOX_APPROVED=1 sh governance/approval-requests/P5-sandbox-docker-remediation-20260525T1542Z.sh apply
P5_SANDBOX_APPROVED=1 sh governance/approval-requests/P5-sandbox-docker-remediation-20260525T1542Z.sh validate
```

This builds an OpenClaw gateway image tagged from the current repo HEAD with Docker CLI support, builds the sandbox image, writes `/opt/openclaw-data/runtime/oc/compose.p5-sandbox.yml`, mounts `/var/run/docker.sock` into the gateway, adds the host Docker group, restarts only `openclaw-gateway`, and validates health, loopback exposure, Docker CLI/socket access, sandbox explain output, and exec approval policy.

## Rollback Command

```sh
cd /opt/openclaw
P5_SANDBOX_APPROVED=1 sh governance/approval-requests/P5-sandbox-docker-remediation-20260525T1542Z.sh rollback
```

Rollback removes the P5 sandbox compose overlay, restarts `openclaw-gateway` with the existing base runtime compose files, validates health/readiness, and verifies Docker CLI/socket access is no longer present inside the gateway container.

## Validation After Apply

The script runs:

```sh
curl -fsS http://127.0.0.1:18789/healthz
curl -fsS http://127.0.0.1:18789/readyz
ss -H -ltn | grep -q '127[.]0[.]0[.]1:18789'
ss -H -ltn | grep -q '127[.]0[.]0[.]1:18790'
docker exec openclaw-gateway sh -lc 'command -v docker && docker --version && test -S /var/run/docker.sock && docker ps --format "{{.Names}}" | head'
docker exec openclaw-gateway openclaw sandbox explain --json
docker exec openclaw-gateway openclaw approvals get --json
```

After validation, the next gate step is exactly one native Telegram-owner protected-action drill. P5 still does not pass unless that drill returns a clean approval packet or terminal denial and no marker command executes without approval.

## Risk

- Mounting `/var/run/docker.sock` gives the gateway container effective control over the host Docker daemon. This is the main security risk.
- Building the local image uses Docker BuildKit and may use network to fetch Docker CLI packages. Prior OOM evidence means builds must remain bounded and monitored.
- Restarting `openclaw-gateway` interrupts the local gateway briefly.
- If compose rendering exposes ports beyond `127.0.0.1`, validation stops before promotion.

## Downtime Estimate

- Build time: estimated 5-20 minutes depending on cache/network.
- Gateway restart: estimated 30-90 seconds.

## Stop Conditions

- `MemAvailable` drops below 4 GiB or host swap usage rises materially.
- Docker build exceeds 20 minutes without progress.
- Rendered Compose binds `18789` or `18790` anywhere except `127.0.0.1`.
- Docker socket mount appears on an unexpected path or without Docker group access.
- Gateway health/readiness fails after restart.
- `openclaw sandbox explain --json` no longer shows sandbox mode enforcing the active session.
- The follow-up protected-action drill executes the marker command without approval or denial.

## What Stops If Ryan Does Nothing?

P5 remains `ACTIVE` and blocked. P6/P7 builder harness work does not start, because the ledger has no P5 pass review. The gateway, model route, and native Telegram channel remain as they are; no Docker socket is mounted and no runtime/container change is applied.

## Safe Prep Already Completed

- Fresh P5 blocker evidence recorded and pushed.
- Fresh blocked gate review recorded and pushed.
- Active gate action report refreshed at current HEAD.
- Source inspection confirmed the existing compose/setup path expects Docker CLI plus Docker socket for sandbox mode.
- This packet and script are source-only until Ryan approves `P5_SANDBOX_APPROVED=1`.
