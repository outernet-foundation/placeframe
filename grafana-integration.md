# Grafana Observability Stack Integration

This document captures the full plan for adding Loki (log aggregation) and Prometheus (metrics) to Placeframe, with Grafana as the unified dashboard UI.

## Current State

### Logging

**C# (Unity) apps have full Serilog + Loki logging**, currently pointed at Grafana Cloud:
- `legacy/Outernet.Client/Assets/OuternetClient/Logging/` — Serilog.Sinks.Grafana.Loki
- `legacy/Outernet.Server/src/Logging/` — same pattern
- `apps/MapRegistrationTool/Assets/Logging/` — same pattern
- All use hardcoded endpoint `https://logs-prod-006.grafana.net` with embedded credentials (user ID `961726`)
- Labels: `app=outernet-client`, `platform={editor|magic-leap|android-mobile|unknown}`
- Custom JSON formatter with ordered properties (level, logGroup, messageTemplate, message, stackTrace, exception)
- Enrichment: device name, method signatures, file/line numbers, stack traces
- Captures Unity Debug.unityLogger, uncaught exceptions, UniTask/R3 errors

**Python services have minimal logging:**
- `api` and `localizer` use `logging.getLogger("uvicorn.error")` via `packages/python/common/src/common/litestar.py`
- `reconstructor`, `database-manager`, `auth-initializer` use raw `print()` statements
- No structured logging, no JSON formatting, no centralized aggregation

### Metrics

No metrics collection exists. No Prometheus, no instrumentation.

### Observability Infrastructure

None. The only monitoring is a `minio-logger` service that tails MinIO trace logs via `mc admin trace`.

## Architecture Decisions

### Loki: Monolithic Mode

Loki has three deployment modes: monolithic (one container), simple scalable (read/write/backend split + nginx), and microservices (every component separate). Monolithic handles up to ~20 GB/day and is appropriate for Placeframe.

**Migration path**: Monolithic → Simple Scalable is low-effort because it's the same binary with different `-target` flags. The stored data format is identical across modes. The forcing function is log volume (~20 GB/day threshold). Using MinIO from day one means no data migration when switching modes — all containers just point at the same bucket.

### Storage: MinIO (not filesystem)

Loki supports local filesystem or S3-compatible backends. **Use MinIO from day one** because:
- Placeframe already runs MinIO
- Avoids the filesystem→S3 data migration that would be required when switching from monolithic to simple scalable mode
- A dedicated `loki` bucket in the existing MinIO instance is ~5 extra lines of config

Prometheus uses local volume storage (it doesn't support S3 natively; that requires Thanos or Mimir).

### Log Collection: Grafana Alloy (not Promtail)

Promtail hit end-of-life March 2026. Grafana Alloy is the official successor. Alloy also handles metrics and traces, so it's the right choice for a new deployment.

Alloy connects to the Docker socket, auto-discovers containers, and tails their stdout/stderr. No per-service configuration needed — new services added to compose.yml are picked up automatically.

### Client Metrics: API Endpoint (not Pushgateway)

Prometheus is pull-based (scrapes endpoints). Unity clients are on the internet and can't be scraped. Options considered:
- **Pushgateway** — designed for batch jobs, not long-lived clients. Metrics persist after disconnect. Prometheus team discourages this pattern.
- **OTLP through Alloy** — architecturally clean but adds OpenTelemetry to the Unity client, which is heavy.
- **API endpoint** (chosen) — add `POST /telemetry` to the Placeframe API. Client posts metric batches. API records them as Prometheus metrics internally. Prometheus scrapes the API's `/metrics`. No new infrastructure.

### Profiling: Out of Scope

Prometheus is for aggregated time-series metrics, not fine-grained profiling. Grafana has Pyroscope for continuous profiling but that's a separate initiative. Prometheus histogram buckets can capture latency distributions (e.g., "what percentage of localization requests take >500ms"), which covers the most useful profiling-adjacent use case.

## New Services

Five new containers in `compose.yml`:

| Service | Image | RAM | Role |
|---|---|---|---|
| `loki` | `grafana/loki:3.x` | ~256-512 MB | Log storage + query engine (monolithic mode) |
| `alloy` | `grafana/alloy:latest` | ~64-128 MB | Docker log collection via socket, Prometheus scraping |
| `grafana` | `grafana/grafana:latest` | ~128-256 MB | Unified dashboard UI (logs + metrics) |
| `prometheus` | `prom/prometheus:latest` | ~256-512 MB | Metrics storage, scrapes /metrics endpoints |
| `cadvisor` | `gcr.io/cadvisor/cadvisor` | ~64-128 MB | Per-container CPU/memory/network metrics |

Total overhead: ~1-1.5 GB RAM.

### Configuration Files Needed

- `docker/loki/config.yaml` — Loki config (monolithic mode, MinIO storage, retention policy)
- `docker/alloy/config.alloy` — Alloy config (Docker log discovery + Loki forwarding)
- `docker/prometheus/prometheus.yml` — Prometheus scrape targets (api, localizer, cadvisor)
- `docker/grafana/provisioning/datasources/datasources.yaml` — auto-provision Loki + Prometheus datasources

### Loki Config Sketch (MinIO-backed)

```yaml
auth_enabled: false
server:
  http_listen_port: 3100
common:
  ring:
    instance_addr: 127.0.0.1
    kvstore:
      store: inmemory
    replication_factor: 1
  path_prefix: /loki
storage_config:
  aws:
    endpoint: minio:9000
    bucketnames: loki
    access_key_id: ${MINIO_ACCESS_KEY}
    secret_access_key: ${MINIO_SECRET_KEY}
    s3forcepathstyle: true
    insecure: true
schema_config:
  configs:
    - from: "2024-01-01"
      store: tsdb
      object_store: s3
      schema: v13
      index:
        prefix: index_
        period: 24h
limits_config:
  retention_period: 720h  # 30 days
```

### Alloy Config Sketch

```alloy
// Discover Docker containers
discovery.docker "containers" {
  host = "unix:///var/run/docker.sock"
}

// Extract container name and service labels
discovery.relabel "containers" {
  targets = discovery.docker.containers.targets
  rule {
    source_labels = ["__meta_docker_container_name"]
    target_label  = "container"
  }
  rule {
    source_labels = ["__meta_docker_container_label_com_docker_compose_service"]
    target_label  = "service"
  }
}

// Tail container logs and forward to Loki
loki.source.docker "containers" {
  host    = "unix:///var/run/docker.sock"
  targets = discovery.relabel.containers.output
  forward_to = [loki.write.default.receiver]
}

loki.write "default" {
  endpoint {
    url = "http://loki:3100/loki/api/v1/push"
  }
}
```

## Implementation Phases

### Phase 1: Deploy the Observability Stack

Add all five containers to `compose.yml` with their config files. Wire up:
- Loki → MinIO (create `loki` bucket in MinIO init)
- Alloy → Docker socket + Loki push endpoint
- Prometheus → scrape targets (api, localizer, cadvisor)
- Grafana → provisioned Loki + Prometheus datasources
- cAdvisor → Docker socket + cgroups

After this phase: all container stdout/stderr is queryable in Grafana via Loki. Container resource metrics visible via Prometheus + cAdvisor. No application code changes yet.

### Phase 2: Backend Prometheus Instrumentation

Add Prometheus metrics middleware to the Litestar services (`api` and `localizer`). Litestar has native support via `litestar.contrib.prometheus` / `litestar.plugins.prometheus` (already available, version >=2.19.0). This gives:
- Request count by endpoint/method/status code
- Request latency histograms
- In-flight request gauges

Instrument localization-specific metrics in the localizer. The localizer already computes these values (defined as a Pydantic model in the codebase with fields `inlier_ratio`, `reprojection_error_median`, `num_inliers`, `num_correspondences`, `num_matches`, `inlier_coverage`). Expose as Prometheus histograms/counters:
- `localization_requests_total` (counter, by status: success/failure)
- `localization_duration_seconds` (histogram)
- `localization_inlier_ratio` (histogram)
- `localization_match_count` (histogram)
- `localization_reprojection_error` (histogram)
- `localization_inlier_coverage` (histogram)

### Phase 3: Point Unity Clients at Self-Hosted Loki

The C# apps already have a working Serilog → Loki pipeline. Changes needed:
- Make the Loki endpoint URL configurable (environment variable or config file) instead of hardcoded Grafana Cloud
- Remove embedded Grafana Cloud credentials (user ID `961726`, bearer token)
- Point at `http://<placeframe-host>:3100` (or route through the gateway)
- Loki push API format is the same whether cloud or self-hosted — `POST /loki/api/v1/push`

Files to modify:
- `legacy/Outernet.Client/Assets/OuternetClient/Logging/LokiLoggerConfiguration.cs`
- `legacy/Outernet.Server/src/Logging/LokiLoggerConfiguration.cs`
- `apps/MapRegistrationTool/Assets/Logging/LokiLoggerConfiguration.cs`

### Phase 4: Client Telemetry Endpoint

Add `POST /telemetry` to the Placeframe API for Unity clients to push metrics (framerate, memory usage, battery, etc.). The API records these as Prometheus metrics. Prometheus scrapes them from the API's `/metrics` endpoint.

### Phase 5: Migrate Python Print Statements to Logging

Replace `print()` with `logging.getLogger(__name__)` in:
- `docker/reconstructor/src/reconstructor/main.py`
- `docker/database-manager/src/main.py`
- `docker/auth-initializer/src/auth_initializer/main.py`
- `docker/localizer/src/localize.py`

Optionally add structured JSON formatting (`python-json-logger`) so Loki can parse fields. Not strictly necessary since Alloy already captures raw stdout — this just makes log queries richer.

## Operational Notes

### Label Cardinality

Loki indexes labels, not log content. High-cardinality labels (like `user_id` or `request_id`) degrade performance. Keep labels low-cardinality: `service`, `level`, `environment`. Everything else goes in the log line and is queried with LogQL pattern matching.

### Retention

Configure `limits_config.retention_period` in Loki config. Without this, the MinIO bucket grows forever. 30 days (`720h`) is a reasonable starting point.

### Version Pinning

Pin all image tags to specific versions (not `latest`). Loki has breaking changes between major versions — the 2.x → 3.x migration changed the default storage format. Schema config uses a `from` date field; upgrades sometimes require adding a new entry.

### Grafana Datasource Provisioning

Configure Loki and Prometheus datasources via provisioning YAML (not the UI) so they survive container recreation.

### Alloy Auto-Discovery

New services added to `compose.yml` are automatically discovered by Alloy via the Docker socket. No Alloy config changes needed. Custom per-service labels require relabeling rules if desired.

### Backup

Loki data in MinIO is covered by whatever MinIO backup strategy exists. Prometheus data in its local volume should be backed up separately if retention matters (though Prometheus data is less critical — you can always re-scrape).
