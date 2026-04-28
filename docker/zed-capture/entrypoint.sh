#!/usr/bin/env bash
set -euo pipefail

cd /app/zed

echo "Starting ZED Capture"

# Logging is configured in Python by src/__init__.py importing src.logging_config,
# which calls dictConfig before any other module is imported. We deliberately do
# NOT pass --log-config here: Litestar's default LoggingConfig (called when the
# app is constructed) would clobber our handlers, and the way we work around
# that in main.py (logging_config=None) only works if Python owns the config.
exec uv run --no-sync uvicorn src.main:app --host 0.0.0.0 --port 9000
