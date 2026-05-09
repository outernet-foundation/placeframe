# Operational debugging

Commands and access patterns for investigating "what did the system actually do?" — Loki queries, database queries, MinIO inspection, and which services log where. CLAUDE.md has a short signposted summary; this file is the full reference.

## Postgres

The application user is `placeframe_owner` (not `postgres`); RLS policies are scoped to it. Connect with:

```bash
docker exec placeframe-postgres-1 psql -U placeframe_owner -d placeframe -c "<query>"
```

A bare `psql -U postgres` will land in a default schema with none of the app tables visible.

## MinIO

Configure the `mc` alias inside the MinIO container using the credentials from `.env` (`MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` — `admin` / `password` in dev):

```bash
docker exec placeframe-minio-1 mc alias set local http://localhost:9000 admin password
docker exec placeframe-minio-1 mc ls --recursive local/dev-captures/
docker exec placeframe-minio-1 mc ls --recursive local/dev-reconstructions/
```

Bucket layout:

| Bucket | Key pattern | Notes |
|---|---|---|
| `dev-captures` | `<capture_session_id>.tar` | Single tarball per capture, not an unpacked tree. |
| `dev-reconstructions` | `<reconstruction_id>/{features.h5, global_descriptors.h5, opq_matrix.tf, pq_quantizer.pq, pairs.txt, sfm_model/*}` | One directory per reconstruction. `sfm_model/` is the final SfM output (frames.txt, points3D.npz, images.txt, etc.). Presence of `sfm_model/` means SfM completed, regardless of what the DB says about status. |
| `loki` | (Loki internal) | Don't touch. |

## Loki

Loki holds logs from every service plus the phone-side capture-tool relay. Available `service_name` values:

```
alloy api capture-tool cloudbeaver gateway grafana keycloak loki
minio minio-logger ngrok postgres reconstructor-cuda state-sync zed-capture
```

Query template (LogQL via the HTTP API, run from the loki container so you don't have to plumb auth):

```bash
docker exec placeframe-loki-1 wget -qO- \
  'http://localhost:3100/loki/api/v1/query_range?query=%7Bservice_name%3D%22<svc>%22%7D&limit=200&direction=backward'
```

Useful filters appended to the query:
- `|= "<literal>"` — line filter, exact substring.
- `|~ "(?i)error|fail"` — regex filter, case-insensitive.

Time-window with `&start=<unix-nanos>&end=<unix-nanos>` to scope to an incident. Date-to-nanos: `date -d '13:11:00 UTC' +%s%N`.

To list current label values: `wget -qO- 'http://localhost:3100/loki/api/v1/label/service_name/values'`.

## Where each service logs

- **api** → Loki `service_name="api"`. Every HTTP request lands here including `/internal/leases/<id>/{progress,succeed,fail}` from the orchestrator and reconstructor.
- **reconstructor-cuda** → Loki `service_name="reconstructor-cuda"` and also `docker logs`. Per-image progress, MinIO put markers, lease lifecycle (`Acquired lease`, `Reconstruction succeeded`, `Reconstruction failed: …`).
- **state-sync** → almost silent. The `dotnet` worker only emits the Kestrel startup banner to stdout/Loki — no per-job logs. To observe orchestrator activity, query the **api** logs for `/internal/leases/` traffic (lease-request 404s mean "no work available", lease-progress 200s mean an active job is reporting in).
- **capture-tool** (phone) → Loki `service_name="capture-tool"`, pushed directly from the Unity app via the gateway. See `apps/AndroidMobile/CLAUDE.md` for the relay details and prerequisites.

## Reconstructor lease lifecycle

The reconstructor is a worker that pulls work via the API:

1. `POST /internal/leases/request` — claim the next queued reconstruction (404 = no work).
2. Download `dev-captures/<capture_session_id>.tar` from MinIO.
3. Run pipeline (extract features → match → train OPQ/PQ → verify geometry → SfM).
4. Upload outputs to `dev-reconstructions/<reconstruction_id>/`.
5. `PUT /internal/leases/<reconstruction_id>/succeed` (or `/fail` on error).

Status updates between phases go through `PUT /internal/leases/<id>/progress`. If the final `/succeed` PUT fails, MinIO has the outputs but the DB still shows the in-progress status.
