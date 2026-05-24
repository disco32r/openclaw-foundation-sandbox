# P4 Approval Packet: Private Sandbox Runtime

Status: drafted, not executed.

## Decision

Approve or reject a protected runtime action to start an isolated OpenClaw Docker sandbox from the foundation source tree.

## Why Approval Is Required

This crosses protected boundaries in `governance/policy-rules.json`:

- `docker_container`
- `runtime_config`
- `network`
- `secrets`
- `auth`

The safe-local preflight is complete in `governance/evidence/p4-runtime-preflight-20260524T2340Z.json`. Docker is available, no foundation containers are running, and ports `18789`/`18790` are unused, but health/readiness/model/approval proof cannot be produced without starting the sandbox.

## Affected Systems

- VM host: `openclaw@192.168.2.242`
- Source tree: `/home/openclaw/foundation-source`
- Runtime state root: `/opt/openclaw-data/runtime/openclaw-foundation-sandbox`
- Docker Compose project from `docker-compose.yml`
- Local-only Gateway publish: `127.0.0.1:18789`
- Local-only bridge publish: `127.0.0.1:18790`

## Apply Command

Run from the VM as `openclaw` with sudo available:

```sh
set -eu
cd /home/openclaw/foundation-source

STATE_ROOT=/opt/openclaw-data/runtime/openclaw-foundation-sandbox
sudo install -d -m 0750 -o openclaw -g openclaw "$STATE_ROOT"
sudo install -d -m 0770 -o 1000 -g 1000 \
  "$STATE_ROOT/config" \
  "$STATE_ROOT/workspace" \
  "$STATE_ROOT/auth-profile-secrets"

umask 077
TOKEN="$(openssl rand -hex 32)"
cat > "$STATE_ROOT/compose.env" <<EOF
OPENCLAW_CONFIG_DIR=$STATE_ROOT/config
OPENCLAW_WORKSPACE_DIR=$STATE_ROOT/workspace
OPENCLAW_AUTH_PROFILE_SECRET_DIR=$STATE_ROOT/auth-profile-secrets
OPENCLAW_GATEWAY_PORT=127.0.0.1:18789
OPENCLAW_BRIDGE_PORT=127.0.0.1:18790
OPENCLAW_GATEWAY_BIND=lan
OPENCLAW_DISABLE_BONJOUR=1
OPENCLAW_GATEWAY_TOKEN=$TOKEN
OPENCLAW_IMAGE=ghcr.io/openclaw/openclaw:latest
OPENCLAW_SKIP_ONBOARDING=1
EOF

docker compose --env-file "$STATE_ROOT/compose.env" pull openclaw-gateway openclaw-cli
docker compose --env-file "$STATE_ROOT/compose.env" run --rm --no-deps --entrypoint node openclaw-gateway \
  dist/index.js config set --batch-json '[{"path":"gateway.mode","value":"local"},{"path":"gateway.bind","value":"lan"},{"path":"gateway.controlUi.allowedOrigins","value":["http://localhost:18789","http://127.0.0.1:18789"]}]'
docker compose --env-file "$STATE_ROOT/compose.env" up -d openclaw-gateway
```

## Validation Command

```sh
set -eu
cd /home/openclaw/foundation-source
STATE_ROOT=/opt/openclaw-data/runtime/openclaw-foundation-sandbox
. "$STATE_ROOT/compose.env"

docker compose --env-file "$STATE_ROOT/compose.env" ps
curl -fsS http://127.0.0.1:18789/healthz
curl -fsS http://127.0.0.1:18789/readyz
ss -ltnp | grep -E '127[.]0[.]0[.]1:18789|127[.]0[.]0[.]1:18790'
docker compose --env-file "$STATE_ROOT/compose.env" exec -T openclaw-gateway \
  node dist/index.js health --token "$OPENCLAW_GATEWAY_TOKEN"
```

Expected result:

- container is running and healthy,
- `/healthz` and `/readyz` pass,
- `18789` and `18790` bind only to `127.0.0.1`,
- authenticated health returns successfully,
- no public admin surface is exposed.

## Rollback Command

```sh
set -eu
cd /home/openclaw/foundation-source
STATE_ROOT=/opt/openclaw-data/runtime/openclaw-foundation-sandbox

docker compose --env-file "$STATE_ROOT/compose.env" down
ss -ltnp | grep -E '18789|18790' && exit 1 || true
```

Rollback intentionally keeps `$STATE_ROOT` in place for forensic review. Delete or archive that state only under a separate cleanup approval.

## Stop Conditions

Stop immediately if any of these occur:

- Docker tries to publish `18789` or `18790` on `0.0.0.0`.
- The gateway fails `/healthz` or `/readyz`.
- The image pull/build pulls an unexpected repository.
- The validation command cannot prove local-only exposure.
- The setup asks for an interactive secret or external account login.
- Any command attempts to mutate production OpenClaw runtime state.

## Risk

Primary risk is accidental exposure of the Control UI or bridge if Docker port bindings are wrong. The proposed command binds both published ports to `127.0.0.1` and validates with `ss` before any promotion claim.

Secondary risk is incomplete model proof. The source `.env` key list did not include a model provider API key. If no provider auth profile is available in the isolated runtime state, P4 remains blocked after health/readiness/exposure proof and moves to a separate model-auth approval packet.
