# Localizer service has no Docker healthcheck

**Severity**: medium — startup wedges surface as 502s from the API, not as a failing container.

**Location**: `compose.cuda.yml:24-41` and `compose.rocm.yml` (corresponding `localizer-rocm:` block).

**Symptom**: A startup failure — calibration mismatch (`CalibrationLoadError` from pipeline_version skew), GPU OOM during `load_models()`, missing `LOCALIZER_SHA` (see `localizer-empty-sha-no-buildtime-guard.md`) — leaves the container "running" (the Python process exits, Docker restarts it on the next request) or stuck in an init loop. The API sees `connection refused` on `http://localizer:8000` and surfaces a 502 to the caller. There is no Docker-level health signal, so `docker ps` / orchestrator dashboards show "Up" / "running" indefinitely.

**Mechanism**: Neither `compose.cuda.yml` nor `compose.rocm.yml` declares a `healthcheck:` for the localizer service. There is also no `depends_on: { condition: service_healthy }` from the API onto the localizer, so the API starts accepting requests before the localizer is ready.

**Fix sketch**: Add `healthcheck:` to both `localizer-cuda` and `localizer-rocm` blocks: `test: ["CMD", "curl", "-fsS", "http://localhost:8000/version"]` with a generous `start_period` (model load can take 30-60s on cold start). Then add `depends_on: { localizer-cuda: { condition: service_healthy } }` on the API block in the matching compose overlay.

**Verification**: Stop the global calibration config, restart `localizer-cuda`; assert `docker ps` shows `(unhealthy)` rather than `Up`.
