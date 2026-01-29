#!/usr/bin/env bash
set -euo pipefail

cd /opt/plerion
exec uv run --package zed --no-sync \
  uvicorn src.main:app \
  --app-dir capture-app/zed \
  --host 0.0.0.0 --port 9000