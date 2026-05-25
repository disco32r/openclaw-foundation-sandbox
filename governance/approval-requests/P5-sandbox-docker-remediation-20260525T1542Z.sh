#!/usr/bin/env sh
set -eu

REPO_ROOT="${REPO_ROOT:-/opt/openclaw}"
STATE_ROOT="${STATE_ROOT:-/opt/openclaw-data/runtime/oc}"
COMPOSE_ENV="$STATE_ROOT/compose.env"
COMPOSE_OVERRIDE="$STATE_ROOT/compose.override.yml"
SANDBOX_COMPOSE="$STATE_ROOT/compose.p5-sandbox.yml"
RENDERED_COMPOSE="$STATE_ROOT/rendered-compose-p5-sandbox.json"
BACKUP_DIR="$STATE_ROOT/backups/p5-sandbox-remediation-20260525T1542Z"
GATEWAY_IMAGE="${GATEWAY_IMAGE:-openclaw:p5-sandbox-cli-f74f1e25af}"
SANDBOX_IMAGE="${SANDBOX_IMAGE:-openclaw-sandbox:bookworm-slim}"
DOCKER_SOCKET="${DOCKER_SOCKET:-/var/run/docker.sock}"

compose_base() {
  docker compose --env-file "$COMPOSE_ENV" -f docker-compose.yml -f "$COMPOSE_OVERRIDE" "$@"
}

compose_p5() {
  docker compose --env-file "$COMPOSE_ENV" -f docker-compose.yml -f "$COMPOSE_OVERRIDE" -f "$SANDBOX_COMPOSE" "$@"
}

require_approval() {
  if [ "${P5_SANDBOX_APPROVED:-}" != "1" ]; then
    echo "P5_SANDBOX_APPROVED=1 is required for protected Docker/runtime work." >&2
    exit 20
  fi
}

ensure_backup_dir() {
  sudo install -d -m 0750 -o openclaw -g openclaw "$STATE_ROOT/backups" "$BACKUP_DIR"
}

preflight() {
  cd "$REPO_ROOT"
  test -f "$COMPOSE_ENV"
  test -f "$COMPOSE_OVERRIDE"
  command -v docker >/dev/null 2>&1
  docker --version
  docker compose version
  test -S "$DOCKER_SOCKET"
  docker ps --filter name=openclaw-gateway --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
  curl -fsS http://127.0.0.1:18789/healthz
  curl -fsS http://127.0.0.1:18789/readyz
  free -h
  df -h /
  docker exec openclaw-gateway sh -lc 'id; command -v docker || true; ls -l /var/run/docker.sock 2>/dev/null || true'
}

write_sandbox_compose() {
  docker_gid="$(stat -c '%g' "$DOCKER_SOCKET")"
  umask 077
  cat > "$SANDBOX_COMPOSE" <<EOF
services:
  openclaw-gateway:
    image: $GATEWAY_IMAGE
    volumes:
      - $DOCKER_SOCKET:/var/run/docker.sock
    group_add:
      - "$docker_gid"
  openclaw-cli:
    image: $GATEWAY_IMAGE
EOF
}

render_and_validate() {
  cd "$REPO_ROOT"
  compose_p5 config --format json > "$RENDERED_COMPOSE"
  python3 - "$RENDERED_COMPOSE" "$GATEWAY_IMAGE" "$STATE_ROOT" <<'PYVALIDATE'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
expected_image = sys.argv[2]
state_root = sys.argv[3]
data = json.loads(path.read_text())
text = path.read_text()
gateway = data["services"]["openclaw-gateway"]
cli = data["services"]["openclaw-cli"]
for service_name, service in [("openclaw-gateway", gateway), ("openclaw-cli", cli)]:
    image = service.get("image")
    if image != expected_image:
        raise SystemExit(f"{service_name} image is not expected P5 sandbox image: {image}")
ports = sorted((p.get("host_ip"), str(p.get("published")), p.get("target")) for p in gateway.get("ports", []))
expected_ports = [("127.0.0.1", "18789", 18789), ("127.0.0.1", "18790", 18790)]
if ports != expected_ports:
    raise SystemExit(f"unexpected published ports: {ports}")
volumes = gateway.get("volumes", [])
socket_mounts = [v for v in volumes if v.get("target") == "/var/run/docker.sock"]
if len(socket_mounts) != 1 or socket_mounts[0].get("source") != "/var/run/docker.sock":
    raise SystemExit(f"expected exactly one Docker socket mount, got {socket_mounts}")
if not gateway.get("group_add"):
    raise SystemExit("expected Docker group_add for gateway socket access")
if "/opt/openclaw-data/workspace/openclaw-foundation-sandbox/runtime" in text:
    raise SystemExit("old runtime path leaked into rendered compose")
if state_root not in text:
    raise SystemExit("current runtime root missing from rendered compose")
PYVALIDATE
}

build_images() {
  cd "$REPO_ROOT"
  DOCKER_BUILDKIT=1 docker build \
    --build-arg OPENCLAW_INSTALL_DOCKER_CLI=1 \
    -t "$GATEWAY_IMAGE" \
    -f Dockerfile \
    "$REPO_ROOT"
  DOCKER_BUILDKIT=1 docker build \
    -t "$SANDBOX_IMAGE" \
    -f scripts/docker/sandbox/Dockerfile \
    "$REPO_ROOT"
}

apply_runtime() {
  require_approval
  cd "$REPO_ROOT"
  ensure_backup_dir
  cp -p "$COMPOSE_ENV" "$BACKUP_DIR/compose.env"
  cp -p "$COMPOSE_OVERRIDE" "$BACKUP_DIR/compose.override.yml"
  [ ! -f "$SANDBOX_COMPOSE" ] || cp -p "$SANDBOX_COMPOSE" "$BACKUP_DIR/compose.p5-sandbox.yml.preexisting"
  preflight
  build_images
  write_sandbox_compose
  render_and_validate
  compose_p5 up -d --no-build openclaw-gateway
}

validate_runtime() {
  cd "$REPO_ROOT"
  render_and_validate
  compose_p5 ps
  curl -fsS http://127.0.0.1:18789/healthz
  curl -fsS http://127.0.0.1:18789/readyz
  ss -H -ltn | grep -q '127[.]0[.]0[.]1:18789'
  ss -H -ltn | grep -q '127[.]0[.]0[.]1:18790'
  if ss -H -ltn | grep -Eq '(^|[[:space:]])(0[.]0[.]0[.]0|\[::\]|\*:)(:18789|:18790)'; then
    echo "unexpected broad listener on 18789 or 18790" >&2
    exit 1
  fi
  docker exec openclaw-gateway sh -lc 'command -v docker && docker --version && test -S /var/run/docker.sock && docker ps --format "{{.Names}}" | head'
  docker exec openclaw-gateway openclaw sandbox explain --json
  docker exec openclaw-gateway openclaw approvals get --json
}

rollback_runtime() {
  require_approval
  cd "$REPO_ROOT"
  if [ -f "$SANDBOX_COMPOSE" ]; then
    ensure_backup_dir
    cp -p "$SANDBOX_COMPOSE" "$BACKUP_DIR/compose.p5-sandbox.yml.rollback-copy"
    rm -f "$SANDBOX_COMPOSE"
  fi
  compose_base up -d --no-build openclaw-gateway
  curl -fsS http://127.0.0.1:18789/healthz
  curl -fsS http://127.0.0.1:18789/readyz
  docker exec openclaw-gateway sh -lc 'if command -v docker >/dev/null 2>&1 || [ -S /var/run/docker.sock ]; then echo "docker access still present after rollback" >&2; exit 1; fi'
}

case "${1:-}" in
  preflight) preflight ;;
  render) require_approval; write_sandbox_compose; render_and_validate ;;
  apply) apply_runtime ;;
  validate) validate_runtime ;;
  rollback) rollback_runtime ;;
  *) echo "usage: $0 preflight|render|apply|validate|rollback" >&2; exit 2 ;;
esac
