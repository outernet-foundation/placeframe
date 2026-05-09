# Loki Log Aggregation

This document captures the plan for adding Loki (log aggregation) to Placeframe, with Grafana as the query UI and Alloy as the log collector.

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

### Log Collection: Grafana Alloy (not Promtail)

Promtail hit end-of-life March 2026. Grafana Alloy is the official successor.

Alloy connects to the Docker socket, auto-discovers containers, and tails their stdout/stderr. No per-service configuration needed — new services added to compose.yml are picked up automatically.

**How auto-discovery works**: Alloy mounts `/var/run/docker.sock` into its container and calls the Docker Engine API to list running containers and watch for start/stop events. When a container appears, Alloy begins tailing its stdout/stderr. It pulls metadata from Docker labels (like `com.docker.compose.service`) to tag each log stream.

**Kubernetes migration path**: The Docker socket doesn't exist in most K8s clusters (they run containerd). Alloy has a native `discovery.kubernetes` component that watches the Kubernetes API server instead, with richer metadata (namespace, pod name, deployment, labels, annotations). The migration is swapping the discovery block in Alloy's config — the Loki push endpoint, label structure, and Grafana dashboards all stay the same.

### Unity Log Routing: Gateway (not direct port)

Unity clients can't reach `loki:3100` — that's a Docker-internal hostname. Two options: expose Loki's port directly, or route through the existing gateway.

**Route through the gateway** because:
- Unity apps already talk to the public domain for API calls — no new endpoint to configure
- Keeps all external traffic through one entrypoint (ngrok → gateway)
- Avoids exposing another port

The gateway adds a `/loki/` path that proxies to `http://loki:3100`.

### Loki Auth: Keycloak via Gateway (not Loki-native)

Loki runs with `auth_enabled: false` internally — only Docker-internal services (Alloy) talk to it directly. For external clients (Unity), the gateway enforces Keycloak OAuth on `/loki/` routes, same as it does for `/api/`.

Considered alternatives:
- **Loki's `auth_enabled: true`**: Only provides tenant isolation via `X-Scope-OrgID` header. No actual credential validation — anyone who knows the org ID can read/write.
- **Reverse proxy with basic auth in front of Loki**: Adds a container for something Keycloak already does.

The Unity app already holds a Keycloak OAuth token, so the existing `BearerTokenAuthenticatedHttpClient` stays but the token becomes the Keycloak token instead of a hardcoded Grafana Cloud credential.

### Scope: Outernet.Client Only

Three C# projects have Loki logging (Outernet.Client, Outernet.Server, MapRegistrationTool). The logging code is duplicated across all three with near-identical structure but meaningful per-project differences (Unity vs plain .NET enrichment, different log groups, platform-specific error suppression).

Only Outernet.Client is being repointed. The other two are dormant — not worth the effort to touch. If they become active again, the same pattern applies.

## New Services

Three new containers in `compose.yml`:

| Service | Image | RAM | Role |
|---|---|---|---|
| `loki` | `grafana/loki:3.5.0` | ~256-512 MB | Log storage + query engine (monolithic mode) |
| `alloy` | `grafana/alloy:v1.9.0` | ~64-128 MB | Docker log collection via socket |
| `grafana` | `grafana/grafana:11.6.0` | ~128-256 MB | Dashboard UI for querying logs |

Total overhead: ~0.5-1 GB RAM.

### Configuration Files

- `docker/loki/config.yaml` — Loki config (monolithic mode, MinIO storage, retention policy)
- `docker/alloy/config.alloy` — Alloy config (Docker log discovery + Loki forwarding)
- `docker/grafana/provisioning/datasources/datasources.yaml` — auto-provision Loki datasource

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

### Phase 1: Deploy Loki + Alloy + Grafana ✅

Add three containers to `compose.yml` with their config files. Wire up:
- Loki → MinIO (create `loki` bucket in MinIO init)
- Alloy → Docker socket + Loki push endpoint
- Grafana → provisioned Loki datasource

After this phase: all container stdout/stderr is queryable in Grafana via Loki. No application code changes.

### Phase 2: Point Outernet.Client at Self-Hosted Loki

**Gateway changes:**
- Add `/loki/` route to the gateway, proxying to `http://loki:3100`
- Enforce Keycloak OAuth on the `/loki/` route (same mechanism as `/api/`)

**Outernet.Client changes** (`legacy/Outernet.Client/Assets/OuternetClient/Logging/LokiLoggerConfiguration.cs`):
- Replace hardcoded Grafana Cloud endpoint (`https://logs-prod-006.grafana.net`) with the self-hosted URL via the gateway (`https://<PUBLIC_DOMAIN>/loki`)
- Switch `BearerTokenAuthenticatedHttpClient` from hardcoded Grafana Cloud credentials to the Keycloak OAuth token the app already holds
- Remove embedded Grafana Cloud user ID (`961726`) and access token

Loki push API format (`POST /loki/api/v1/push`) is the same whether Cloud or self-hosted — no formatter or label changes needed.

## Operational Notes

### Label Cardinality

Loki indexes labels, not log content. High-cardinality labels (like `user_id` or `request_id`) degrade performance. Keep labels low-cardinality: `service`, `level`, `environment`. Everything else goes in the log line and is queried with LogQL pattern matching.

### Retention

Configure `limits_config.retention_period` in Loki config. Without this, the MinIO bucket grows forever. 30 days (`720h`) is a reasonable starting point.

### Version Pinning

Pin all image tags to specific versions (not `latest`). Loki has breaking changes between major versions — the 2.x → 3.x migration changed the default storage format. Schema config uses a `from` date field; upgrades sometimes require adding a new entry.

### Grafana Datasource Provisioning

Configure the Loki datasource via provisioning YAML (not the UI) so it survives container recreation.

### Alloy Auto-Discovery

New services added to `compose.yml` are automatically discovered by Alloy via the Docker socket. No Alloy config changes needed. Custom per-service labels require relabeling rules if desired.

### Backup

Loki data in MinIO is covered by whatever MinIO backup strategy exists.
