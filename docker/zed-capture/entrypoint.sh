#!/usr/bin/env bash
set -euo pipefail

cd /app/zed

echo "Starting ZED Capture"

exec uv run --no-sync uvicorn src.main:app --host 0.0.0.0 --port 9000
