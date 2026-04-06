#!/bin/bash
set -euo pipefail

ROOT_DIR="/Users/mac/Documents/龙虾相关/my_openclaw"
OPENCLAW_CONFIG_PATH="${ROOT_DIR}/openclaw.json"
OPENCLAW_WORKSPACE_HOST="${ROOT_DIR}/workspace"
OPENCLAW_AGENTS_ROOT_HOST="${ROOT_DIR}/agents"
OPENCLAW_STATE_DIR_HOST="${ROOT_DIR}/openclaw_state"

# Make sure we can always cd even if launchd started us weirdly.
cd "$ROOT_DIR"

COMPOSE_FILES=(
  "-f" "$ROOT_DIR/docker-compose.yml"
  "-f" "$ROOT_DIR/docker-compose.openclaw-secure.yml"
)

log() { echo "[openclaw-boot] $*"; }

require_path() {
  local path="$1"
  local label="$2"
  if [ ! -e "$path" ]; then
    log "Missing ${label}: $path"
    exit 1
  fi
}

require_writable_dir() {
  local path="$1"
  local label="$2"
  mkdir -p "$path"
  if [ ! -w "$path" ]; then
    log "${label} is not writable: $path"
    exit 1
  fi
}

log "Checking stable host paths..."
require_path "$OPENCLAW_CONFIG_PATH" "config file"
require_writable_dir "$OPENCLAW_WORKSPACE_HOST" "workspace directory"
require_path "$OPENCLAW_AGENTS_ROOT_HOST" "agents root"
require_writable_dir "$OPENCLAW_STATE_DIR_HOST" "state directory"

log "Starting stack..."
/usr/local/bin/docker compose "${COMPOSE_FILES[@]}" up -d --build openclaw

# wait for gateway (宿主机端口来自 compose 映射，见 scripts/openclaw-gateway.sh docker-host-port)
GW_DOCKER_HOST="$("$ROOT_DIR/scripts/openclaw-gateway.sh" docker-host-port)"
log "Waiting for gateway health on 127.0.0.1:${GW_DOCKER_HOST} ..."
for i in {1..40}; do
  if curl -s -m 2 "http://127.0.0.1:${GW_DOCKER_HOST}/health" >/dev/null 2>&1; then
    break
  fi
  sleep 2
  if [ "$i" -eq 40 ]; then
    log "Gateway did not become healthy (host port ${GW_DOCKER_HOST})."
    exit 1
  fi
done

log "Running Feishu/Bot & agent connectivity tests..."

# Best-effort tests; keep the service running even if tests fail.
bash "$ROOT_DIR/test_feishu_connection.sh" || true
bash "$ROOT_DIR/scripts/test-agent-collaboration.sh" || true

log "Done."
