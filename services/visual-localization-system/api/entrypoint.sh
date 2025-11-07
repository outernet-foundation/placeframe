#!/usr/bin/env bash
set -euo pipefail

cd /app/services/visual-localization-system/api

UVICORN_ARGS=( "src.main:app" "--host" "0.0.0.0" "--port" "8000" )

echo "Starting API"

if [[ "${RELOAD:-}" == "true" ]]; then
  echo "Reload mode enabled"
  UVICORN_ARGS+=( "--reload" "--reload-dir" "/app/services/visual-localization-system/api/src" "--reload-dir" "/app/services/visual-localization-system/models/src" "--reload-dir" "/app/services/visual-localization-system/common/src" "--reload-dir" "/app/services/visual-localization-system/localize/src" )
fi

if [[ "${DEBUG:-}" == "true" ]]; then
  echo "Debug mode enabled"
  DEBUG_WAIT_FLAG=()
  if [[ "${DEBUG_WAIT:-}" == "true" ]]; then
    echo "Waiting for debugger to attach"
    DEBUG_WAIT_FLAG+=( "--wait-for-client" )
  fi
  exec uv run --no-sync python -Xfrozen_modules=off -m debugpy --listen 0.0.0.0:5678 "${DEBUG_WAIT_FLAG[@]}" -m uvicorn "${UVICORN_ARGS[@]}"
else
  exec uv run --no-sync uvicorn "${UVICORN_ARGS[@]}"
fi
