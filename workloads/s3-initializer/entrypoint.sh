#!/usr/bin/env bash
set -euo pipefail

exec uv run --no-sync s3-initializer
