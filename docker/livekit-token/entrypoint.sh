#!/usr/bin/env bash
set -euo pipefail

cd /app/docker/livekit-token

exec uv run --no-sync uvicorn src.main:app --host 0.0.0.0 --port 8000
