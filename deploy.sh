#!/usr/bin/env bash
set -euo pipefail

echo "========================================="
echo "Travis Ops Center — Hardened Deploy"
echo "========================================="

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env."
  echo "Set AUTH_USER and AUTH_PASS in .env, then run this command again."
  exit 0
fi

env_value() {
  local key="$1" value
  value="$(grep -E "^${key}=" .env | tail -n1 | cut -d= -f2- || true)"
  value="${value%\"}"; value="${value#\"}"
  value="${value%\'}"; value="${value#\'}"
  printf '%s' "$value"
}

AUTH_USER_VALUE="$(env_value AUTH_USER)"
AUTH_PASS_VALUE="$(env_value AUTH_PASS)"
SERVER_PORT_VALUE="$(env_value SERVER_PORT)"
PUBLIC_BIND_HOST_VALUE="$(env_value PUBLIC_BIND_HOST)"

SERVER_PORT_VALUE="${SERVER_PORT_VALUE:-8080}"
PUBLIC_BIND_HOST_VALUE="${PUBLIC_BIND_HOST_VALUE:-127.0.0.1}"

if [ -z "$AUTH_USER_VALUE" ] || [ -z "$AUTH_PASS_VALUE" ]; then
  echo "ERROR: Docker/server deployment requires AUTH_USER and AUTH_PASS in .env."
  exit 1
fi

case "$AUTH_PASS_VALUE" in
  password|changeme|change_me|change_me_to_a_strong_password)
    echo "ERROR: Replace the placeholder AUTH_PASS before deployment."
    exit 1
    ;;
esac

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: Docker is not installed."
  exit 1
fi

if docker compose version >/dev/null 2>&1; then
  COMPOSE=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE=(docker-compose)
else
  echo "ERROR: Docker Compose is not available."
  exit 1
fi

"${COMPOSE[@]}" --env-file .env up -d --build

HEALTH_HOST="$PUBLIC_BIND_HOST_VALUE"
if [ "$HEALTH_HOST" = "0.0.0.0" ] || [ "$HEALTH_HOST" = "::" ]; then
  HEALTH_HOST="127.0.0.1"
fi

if command -v curl >/dev/null 2>&1; then
  for _ in $(seq 1 20); do
    if curl -fsS "http://${HEALTH_HOST}:${SERVER_PORT_VALUE}/health" >/dev/null 2>&1; then
      echo "Service healthy: http://${PUBLIC_BIND_HOST_VALUE}:${SERVER_PORT_VALUE}"
      break
    fi
    sleep 1
  done
fi

echo
echo "Deployment started."
echo "Bind: ${PUBLIC_BIND_HOST_VALUE}:${SERVER_PORT_VALUE}"
echo "User: ${AUTH_USER_VALUE}"
echo "Logs: ${COMPOSE[*]} logs -f"
echo "Stop: ${COMPOSE[*]} down"
