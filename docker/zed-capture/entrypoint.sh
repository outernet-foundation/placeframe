#!/usr/bin/env bash
set -euo pipefail

cd /app/zed

echo "Starting ZED Capture"

exec uv run --no-sync uvicorn src.main:app --host 127.0.0.1 --port 9001
