#!/usr/bin/env bash
set -euo pipefail

cd /app/docker/orchestrator

echo "Starting reconstruction orchestrator"

if [[ "${DEBUG:-}" == "true" ]]; then
  echo "Debug mode enabled"
  DEBUG_WAIT_FLAG=()
  if [[ "${DEBUG_WAIT:-}" == "true" ]]; then
    echo "Waiting for debugger to attach"
    DEBUG_WAIT_FLAG+=( "--wait-for-client" )
  fi
  exec uv run --no-sync python -Xfrozen_modules=off -m debugpy --listen 0.0.0.0:5678 "${DEBUG_WAIT_FLAG[@]}" -m src.main
else
  exec uv run --no-sync -m src.main
fi