#!/usr/bin/env bash
# Resolve OpenClaw Gateway ports/URL from repo openclaw.json + optional .env + docker-compose.
# Usage (from repo root or any cwd):
#   scripts/openclaw-gateway.sh listen-port       # openclaw.json gateway.port
#   scripts/openclaw-gateway.sh host-port         # 本机浏览器/curl 连网关（见下方优先级）
#   scripts/openclaw-gateway.sh docker-host-port # 仅 compose 映射（给 docker compose up 后的健康检查）
#   scripts/openclaw-gateway.sh base-url         # http://127.0.0.1:<host-port>
#
# host-port 优先级:
#   1) OPENCLAW_GATEWAY_HOST_PORT
#   2) .env 里 OPENCLAW_GATEWAY_URL / OPENCLAW_GATEWAY_HTTP 的端口
#   3) docker-compose.yml 中 127.0.0.1:<host>:<listen>（listen = gateway.port）
#   4) listen-port
# 若同时用 Docker 网关又在本机 .env 写了直连 18889，请显式设置 OPENCLAW_GATEWAY_HOST_PORT=宿主机映射端口。

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CFG="$ROOT/openclaw.json"

listen_port() {
  if [ ! -f "$CFG" ]; then
    echo "18889"
    return
  fi
  jq -r '.gateway.port // 18889' "$CFG"
}

env_host_port_from_file() {
  local f="$ROOT/.env"
  [ -f "$f" ] || return 1
  local line key val
  while IFS= read -r line || [ -n "$line" ]; do
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ "$line" =~ ^[[:space:]]*$ ]] && continue
    [[ "$line" =~ ^OPENCLAW_GATEWAY_(URL|HTTP)= ]] || continue
    key="${line%%=*}"
    val="${line#*=}"
    val="${val%\"}"
    val="${val#\"}"
    val="${val%\'}"
    val="${val#\'}"
    if [[ "$val" =~ :([0-9]+) ]]; then
      echo "${BASH_REMATCH[1]}"
      return 0
    fi
  done <"$f"
  return 1
}

compose_host_for_listen() {
  local lp="$1"
  local dc="$ROOT/docker-compose.yml"
  [ -f "$dc" ] || return 1
  sed -n 's/.*"127\.0\.0\.1:\([0-9][0-9]*\):'"$lp"'".*/\1/p' "$dc" | head -1
}

host_port() {
  local lp
  lp="$(listen_port)"
  if [ -n "${OPENCLAW_GATEWAY_HOST_PORT:-}" ]; then
    echo "$OPENCLAW_GATEWAY_HOST_PORT"
    return
  fi
  local ep
  if ep="$(env_host_port_from_file)"; then
    echo "$ep"
    return
  fi
  local hp
  hp="$(compose_host_for_listen "$lp" || true)"
  if [ -n "$hp" ]; then
    echo "$hp"
    return
  fi
  echo "$lp"
}

base_url() {
  echo "http://127.0.0.1:$(host_port)"
}

docker_host_port() {
  local lp hp
  lp="$(listen_port)"
  hp="$(compose_host_for_listen "$lp" || true)"
  if [ -n "$hp" ]; then
    echo "$hp"
  else
    echo "$lp"
  fi
}

case "${1:-}" in
listen-port) listen_port ;;
host-port) host_port ;;
docker-host-port) docker_host_port ;;
base-url) base_url ;;
health-url) base_url ;;
-h | --help)
  sed -n '1,18p' "$0" | tail -n +2
  ;;
*)
  echo "Usage: $0 listen-port|host-port|docker-host-port|base-url|health-url" >&2
  exit 1
  ;;
esac
