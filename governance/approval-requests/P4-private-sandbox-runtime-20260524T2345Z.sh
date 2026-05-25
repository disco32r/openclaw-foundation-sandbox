#!/usr/bin/env sh
set -eu

REPO_ROOT="${REPO_ROOT:-/home/openclaw/foundation-source}"
STATE_ROOT="${STATE_ROOT:-/opt/openclaw-data/runtime/openclaw-foundation-sandbox}"
COMPOSE_ENV="$STATE_ROOT/compose.env"
COMPOSE_OVERRIDE="$STATE_ROOT/docker-compose.p4.override.yml"
RENDERED_COMPOSE="$STATE_ROOT/rendered-compose-validation.json"
PINNED_IMAGE="ghcr.io/openclaw/openclaw@sha256:d35b8b681c223a85027502c7a82999aa772d6a09e1b28903951cac7fc27efed5"
OLD_RUNTIME_PATH="/opt/openclaw-data/workspace/openclaw-foundation-sandbox/runtime"

compose() {
  docker compose --env-file "$COMPOSE_ENV" -f docker-compose.yml -f "$COMPOSE_OVERRIDE" "$@"
}

require_runtime_approval() {
  if [ "${P4_APPROVED:-}" != "1" ]; then
    echo "P4_APPROVED=1 is required for protected Docker/runtime work." >&2
    exit 20
  fi
}

write_compose_files() {
  sudo install -d -m 0750 -o openclaw -g openclaw "$STATE_ROOT"
  sudo install -d -m 0770 -o 1000 -g 1000 \
    "$STATE_ROOT/config" \
    "$STATE_ROOT/workspace" \
    "$STATE_ROOT/auth-profile-secrets"

  token=""
  if [ -f "$COMPOSE_ENV" ]; then
    token="$(awk -F= '$1 == "OPENCLAW_GATEWAY_TOKEN" {print substr($0, index($0, $2)); exit}' "$COMPOSE_ENV" || true)"
  fi
  if [ -z "$token" ]; then
    token="$(openssl rand -hex 32)"
  fi

  umask 077
  cat > "$COMPOSE_ENV" <<EOF
OPENCLAW_CONFIG_DIR=$STATE_ROOT/config
OPENCLAW_WORKSPACE_DIR=$STATE_ROOT/workspace
OPENCLAW_AUTH_PROFILE_SECRET_DIR=$STATE_ROOT/auth-profile-secrets
OPENCLAW_GATEWAY_PORT=127.0.0.1:18789
OPENCLAW_BRIDGE_PORT=127.0.0.1:18790
OPENCLAW_GATEWAY_BIND=lan
OPENCLAW_DISABLE_BONJOUR=1
OPENCLAW_GATEWAY_TOKEN=$token
OPENCLAW_IMAGE=$PINNED_IMAGE
OPENCLAW_SKIP_ONBOARDING=1
EOF

  cat > "$COMPOSE_OVERRIDE" <<'EOF'
services:
  openclaw-gateway:
    env_file: !reset []
  openclaw-cli:
    env_file: !reset []
EOF
}

render_and_validate_compose() {
  cd "$REPO_ROOT"
  compose config --format json > "$RENDERED_COMPOSE"
  python3 - "$RENDERED_COMPOSE" "$PINNED_IMAGE" "$OLD_RUNTIME_PATH" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
expected_image = sys.argv[2]
old_runtime_path = sys.argv[3]
text = path.read_text()
data = json.loads(text)
gateway = data["services"]["openclaw-gateway"]
ports = sorted((p.get("host_ip"), str(p.get("published")), p.get("target")) for p in gateway.get("ports", []))
expected_ports = [("127.0.0.1", "18789", 18789), ("127.0.0.1", "18790", 18790)]
if ports != expected_ports:
    raise SystemExit(f"unexpected published ports: {ports}")
for service_name in ["openclaw-gateway", "openclaw-cli"]:
    image = data["services"][service_name].get("image")
    if image != expected_image:
        raise SystemExit(f"{service_name} image is not pinned: {image}")
if old_runtime_path in text:
    raise SystemExit("old source .env runtime path leaked into rendered Compose config")
PY
}

apply_runtime() {
  cd "$REPO_ROOT"
  write_compose_files
  render_and_validate_compose

  compose pull openclaw-gateway openclaw-cli
  compose run --rm --no-build --no-deps --entrypoint node openclaw-gateway \
    dist/index.js config set --batch-json '[{"path":"gateway.mode","value":"local"},{"path":"gateway.bind","value":"lan"},{"path":"gateway.controlUi.allowedOrigins","value":["http://localhost:18789","http://127.0.0.1:18789"]}]'
  compose up -d --no-build openclaw-gateway

  if [ -n "${P4_OPENAI_CODEX_API_KEY:-}" ]; then
    printf "%s\n" "$P4_OPENAI_CODEX_API_KEY" | compose run --rm --no-build -T openclaw-cli \
      models auth paste-api-key --provider openai-codex --profile-id openai-codex:foundation-sandbox
  fi
}

validate_core() {
  cd "$REPO_ROOT"
  render_and_validate_compose
  compose ps
  curl -fsS http://127.0.0.1:18789/healthz
  curl -fsS http://127.0.0.1:18789/readyz
  ss -H -ltn | grep -q '127[.]0[.]0[.]1:18789'
  ss -H -ltn | grep -q '127[.]0[.]0[.]1:18790'
  if ss -H -ltn | grep -Eq '(^|[[:space:]])(0[.]0[.]0[.]0|\[::\]|\*:)(:18789|:18790)'; then
    echo "unexpected broad listener on 18789 or 18790" >&2
    exit 1
  fi
  # shellcheck disable=SC1090
  . "$COMPOSE_ENV"
  compose exec -T openclaw-gateway node dist/index.js health --token "$OPENCLAW_GATEWAY_TOKEN"
}

validate_model() {
  cd "$REPO_ROOT"
  compose run --rm --no-build -T openclaw-cli models status --check
}

rollback_runtime() {
  cd "$REPO_ROOT"
  compose down
  if ss -H -ltn | grep -Eq '(:18789|:18790)'; then
    echo "listener remains on 18789 or 18790" >&2
    exit 1
  fi
}

case "${1:-}" in
  render)
    require_runtime_approval
    write_compose_files
    render_and_validate_compose
    ;;
  apply)
    require_runtime_approval
    apply_runtime
    ;;
  validate-core)
    require_runtime_approval
    validate_core
    ;;
  validate-model)
    require_runtime_approval
    validate_model
    ;;
  validate)
    require_runtime_approval
    validate_core
    validate_model
    ;;
  rollback)
    require_runtime_approval
    rollback_runtime
    ;;
  *)
    echo "usage: $0 render|apply|validate-core|validate-model|validate|rollback" >&2
    exit 2
    ;;
esac
