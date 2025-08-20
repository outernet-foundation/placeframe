#!/usr/bin/env bash
set -euo pipefail
cd /app/services/api 
uv run uvicorn src.main:app --no-sync --host 0.0.0.0 --port 8000