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

The safe-local preflight is complete in `governance/evidence/p4-runtime-preflight-20260524T2340Z.json`, the Compose dry run is captured in `governance/evidence/p4-compose-dry-run-20260524T2347Z.json`, and model/provider preflight is captured in `governance/evidence/p4-provider-preflight-20260524T2350Z.json`. Docker is available, no foundation containers are running, and ports `18789`/`18790` are unused. The dry run also found that the repo-root `.env` would leak old values through `env_file` unless explicitly reset, so the apply command below uses a Compose override before any pull, config write, or start.

## Affected Systems

- VM host: `openclaw@192.168.2.242`
- Source tree: `/opt/openclaw`
- Runtime state root: `/opt/openclaw-data/runtime/openclaw-foundation-sandbox`
- Docker Compose project from `docker-compose.yml`
- Local-only Gateway publish: `127.0.0.1:18789`
- Local-only bridge publish: `127.0.0.1:18790`

## Apply Command

Run from the VM as `openclaw` with sudo available:

Preferred reviewed script:

```sh
cd /opt/openclaw
P4_APPROVED=1 P4_OPENAI_CODEX_API_KEY="${P4_OPENAI_CODEX_API_KEY:-}" \
  sh governance/approval-requests/P4-private-sandbox-runtime-20260524T2345Z.sh apply
P4_APPROVED=1 sh governance/approval-requests/P4-private-sandbox-runtime-20260524T2345Z.sh validate
```

Equivalent expanded command:

```sh
set -eu
cd /opt/openclaw

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
OPENCLAW_IMAGE=ghcr.io/openclaw/openclaw@sha256:d35b8b681c223a85027502c7a82999aa772d6a09e1b28903951cac7fc27efed5
OPENCLAW_SKIP_ONBOARDING=1
EOF

cat > "$STATE_ROOT/docker-compose.p4.override.yml" <<EOF
services:
  openclaw-gateway:
    env_file: !reset []
  openclaw-cli:
    env_file: !reset []
EOF

docker compose --env-file "$STATE_ROOT/compose.env" \
  -f docker-compose.yml \
  -f "$STATE_ROOT/docker-compose.p4.override.yml" \
  config --format json > "$STATE_ROOT/rendered-compose-validation.json"
python3 - "$STATE_ROOT/rendered-compose-validation.json" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
text = path.read_text()
data = json.loads(text)
gateway = data["services"]["openclaw-gateway"]
ports = sorted((p.get("host_ip"), str(p.get("published")), p.get("target")) for p in gateway.get("ports", []))
expected_ports = [("127.0.0.1", "18789", 18789), ("127.0.0.1", "18790", 18790)]
if ports != expected_ports:
    raise SystemExit(f"unexpected published ports: {ports}")
expected_image = "ghcr.io/openclaw/openclaw@sha256:d35b8b681c223a85027502c7a82999aa772d6a09e1b28903951cac7fc27efed5"
for service_name in ["openclaw-gateway", "openclaw-cli"]:
    image = data["services"][service_name].get("image")
    if image != expected_image:
        raise SystemExit(f"{service_name} image is not pinned: {image}")
if "/opt/openclaw-data/workspace/openclaw-foundation-sandbox/runtime" in text:
    raise SystemExit("old source .env runtime path leaked into rendered Compose config")
PY

docker compose --env-file "$STATE_ROOT/compose.env" \
  -f docker-compose.yml \
  -f "$STATE_ROOT/docker-compose.p4.override.yml" \
  pull openclaw-gateway openclaw-cli
docker compose --env-file "$STATE_ROOT/compose.env" \
  -f docker-compose.yml \
  -f "$STATE_ROOT/docker-compose.p4.override.yml" \
  run --rm --pull never --no-deps --entrypoint node openclaw-gateway \
  dist/index.js config set --batch-json '[{"path":"gateway.mode","value":"local"},{"path":"gateway.bind","value":"lan"},{"path":"gateway.controlUi.allowedOrigins","value":["http://localhost:18789","http://127.0.0.1:18789"]}]'
docker compose --env-file "$STATE_ROOT/compose.env" \
  -f docker-compose.yml \
  -f "$STATE_ROOT/docker-compose.p4.override.yml" \
  up -d --no-build openclaw-gateway

if [ -n "${P4_OPENAI_CODEX_API_KEY:-}" ]; then
  printf "%s\n" "$P4_OPENAI_CODEX_API_KEY" | docker compose --env-file "$STATE_ROOT/compose.env" \
    -f docker-compose.yml \
    -f "$STATE_ROOT/docker-compose.p4.override.yml" \
    run --rm --pull never -T openclaw-cli \
    models auth paste-api-key --provider openai-codex --profile-id openai-codex:foundation-sandbox
fi
```

## Validation Command

```sh
cd /opt/openclaw
P4_APPROVED=1 sh governance/approval-requests/P4-private-sandbox-runtime-20260524T2345Z.sh validate
```

Equivalent expanded command:

```sh
set -eu
cd /opt/openclaw
STATE_ROOT=/opt/openclaw-data/runtime/openclaw-foundation-sandbox
. "$STATE_ROOT/compose.env"

docker compose --env-file "$STATE_ROOT/compose.env" \
  -f docker-compose.yml \
  -f "$STATE_ROOT/docker-compose.p4.override.yml" \
  config --format json > "$STATE_ROOT/rendered-compose-validation.json"
python3 - "$STATE_ROOT/rendered-compose-validation.json" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
text = path.read_text()
data = json.loads(text)
gateway = data["services"]["openclaw-gateway"]
ports = sorted((p.get("host_ip"), str(p.get("published")), p.get("target")) for p in gateway.get("ports", []))
expected_ports = [("127.0.0.1", "18789", 18789), ("127.0.0.1", "18790", 18790)]
if ports != expected_ports:
    raise SystemExit(f"unexpected published ports: {ports}")
expected_image = "ghcr.io/openclaw/openclaw@sha256:d35b8b681c223a85027502c7a82999aa772d6a09e1b28903951cac7fc27efed5"
for service_name in ["openclaw-gateway", "openclaw-cli"]:
    image = data["services"][service_name].get("image")
    if image != expected_image:
        raise SystemExit(f"{service_name} image is not pinned: {image}")
if "/opt/openclaw-data/workspace/openclaw-foundation-sandbox/runtime" in text:
    raise SystemExit("old source .env runtime path leaked into rendered Compose config")
PY
docker compose --env-file "$STATE_ROOT/compose.env" \
  -f docker-compose.yml \
  -f "$STATE_ROOT/docker-compose.p4.override.yml" \
  ps
curl -fsS http://127.0.0.1:18789/healthz
curl -fsS http://127.0.0.1:18789/readyz
ss -ltnp | grep -E '127[.]0[.]0[.]1:18789|127[.]0[.]0[.]1:18790'
docker compose --env-file "$STATE_ROOT/compose.env" \
  -f docker-compose.yml \
  -f "$STATE_ROOT/docker-compose.p4.override.yml" \
  exec -T openclaw-gateway \
  node dist/index.js health --token "$OPENCLAW_GATEWAY_TOKEN"
docker compose --env-file "$STATE_ROOT/compose.env" \
  -f docker-compose.yml \
  -f "$STATE_ROOT/docker-compose.p4.override.yml" \
  run --rm --pull never -T openclaw-cli \
  models status --check
```

Expected result:

- container is running and healthy,
- `/healthz` and `/readyz` pass,
- `18789` and `18790` bind only to `127.0.0.1`,
- rendered Compose config uses pinned image digest `sha256:d35b8b681c223a85027502c7a82999aa772d6a09e1b28903951cac7fc27efed5`,
- rendered Compose config does not inject old repo-root `.env` runtime paths,
- authenticated health returns successfully,
- model auth status passes when `P4_OPENAI_CODEX_API_KEY` is provided,
- no public admin surface is exposed.

If `P4_OPENAI_CODEX_API_KEY` is not provided, stop after health/readiness/exposure proof and record P4 as still blocked on model-auth input. Do not invent a fallback local-model route.

## Rollback Command

```sh
cd /opt/openclaw
P4_APPROVED=1 sh governance/approval-requests/P4-private-sandbox-runtime-20260524T2345Z.sh rollback
```

Equivalent expanded command:

```sh
set -eu
cd /opt/openclaw
STATE_ROOT=/opt/openclaw-data/runtime/openclaw-foundation-sandbox

docker compose --env-file "$STATE_ROOT/compose.env" \
  -f docker-compose.yml \
  -f "$STATE_ROOT/docker-compose.p4.override.yml" \
  down
ss -ltnp | grep -E '18789|18790' && exit 1 || true
```

Rollback intentionally keeps `$STATE_ROOT` in place for forensic review. Delete or archive that state only under a separate cleanup approval.

## Stop Conditions

Stop immediately if any of these occur:

- Docker tries to publish `18789` or `18790` on `0.0.0.0`.
- Rendered Compose config includes old source `.env` runtime paths.
- Rendered Compose config uses an unpinned image or a digest other than `sha256:d35b8b681c223a85027502c7a82999aa772d6a09e1b28903951cac7fc27efed5`.
- The gateway fails `/healthz` or `/readyz`.
- The image pull/build pulls an unexpected repository.
- The validation command cannot prove local-only exposure.
- `P4_OPENAI_CODEX_API_KEY` is absent and the run attempts to claim the hosted-model criterion anyway.
- The setup asks for an interactive secret or external account login.
- Any command attempts to mutate production OpenClaw runtime state.

## Risk

Primary risk is accidental exposure of the Control UI or bridge if Docker port bindings are wrong. The proposed command binds both published ports to `127.0.0.1` and validates with `ss` before any promotion claim.

Secondary risk is incomplete model proof. The source `.env` key list did not include a model provider API key. If no provider auth profile is available in the isolated runtime state, P4 remains blocked after health/readiness/exposure proof and moves to a separate model-auth approval packet.
