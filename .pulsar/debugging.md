# Placeframe debugging quick paths

Operational commands for investigating "what did the system actually do?" — log queries, blob inspection, DB inspection. The constraints that govern *why* the stack is shaped the way it is live in `docker/SPEC.md`; this file is the runbook.

## Postgres

The application user is `placeframe_owner` (RLS policies are scoped to it). Not `postgres`:

```bash
docker exec placeframe-postgres-1 psql -U placeframe_owner -d placeframe -c "<query>"
```

A bare `psql -U postgres` lands in a default schema with no app tables visible.

## MinIO

Configure the `mc` alias inside the MinIO container using the credentials from `.env` (`MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` — `admin` / `password` in dev):

```bash
docker exec placeframe-minio-1 mc alias set local http://localhost:9000 admin password
docker exec placeframe-minio-1 mc ls --recursive local/dev-captures/
docker exec placeframe-minio-1 mc ls --recursive local/dev-reconstructions/
```

Bucket schema and what each prefix contains is in `docker/SPEC.md` (`## Constraints`, MinIO bucket layout). The operationally relevant gotcha: presence of `sfm_model/` under `dev-reconstructions/<id>/` means SfM completed, regardless of what the DB says — the final `/succeed` PUT can fail and orphan a reconstruction at `uploading`.

## Loki

Loki holds logs from every service plus the phone-side capture-tool relay. Available `service_name` values:

```
alloy api capture-tool cloudbeaver gateway grafana keycloak loki
minio minio-logger ngrok postgres reconstructor-cuda zed-capture
```

Query template (LogQL via the HTTP API; run from the loki container so you don't have to plumb auth):

```bash
docker exec placeframe-loki-1 wget -qO- \
  'http://localhost:3100/loki/api/v1/query_range?query=%7Bservice_name%3D%22<svc>%22%7D&limit=200&direction=backward'
```

Useful filters appended to the query:

- `|= "<literal>"` — line filter, exact substring.
- `|~ "(?i)error|fail"` — regex filter, case-insensitive.

Scope to an incident with `&start=<unix-nanos>&end=<unix-nanos>`. Date-to-nanos: `date -d '13:11:00 UTC' +%s%N`.

List current label values: `wget -qO- 'http://localhost:3100/loki/api/v1/label/service_name/values'`.

For repeated queries, use `uv run loki-query` (`scripts/SPEC.md`) — it handles the URL encoding and formats output as `HH:MM:SS LEVEL [logGroup] message`.

## Where each service logs

- **api** → Loki `service_name="api"`. Every HTTP request, including `/internal/leases/<id>/{progress,succeed,fail}` from the reconstructor.
- **reconstructor-cuda** → Loki `service_name="reconstructor-cuda"` and `docker logs`. Per-image progress, MinIO put markers, lease lifecycle (`Acquired lease`, `Reconstruction succeeded`, `Reconstruction failed: …`). To observe end-to-end lease activity from the API side, query the **api** logs for `/internal/leases/` traffic — lease-request 404s mean "no work available", lease-progress 200s mean an active job is reporting in.
- **capture-tool** (phone) → Loki `service_name="capture-tool"`, pushed directly from the Unity app via the gateway. See `apps/CaptureTool/CLAUDE.md` for relay details.
