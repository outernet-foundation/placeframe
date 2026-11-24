---
updated: 2026-11-23
---

# Reconstruction job lifecycle execution plan

Linear execution plan for `reconstruction-job-lifecycle.md` (the ADR, same directory). The ADR is the design authority; this file is the sequencing authority and the progress record. Where this plan spells out a concrete choice the ADR leaves open (wire field names, shard layout, env var names, batch sizes), the choice is made here and is not to be re-deliberated during execution.

## Session mechanics

1. **Entry.** A session executing this plan reads this file first, then the ADR sections each phase cites. The first action after reading is `git status` on the repo root (`/workspace/placeframe`, branch `job-lifecycle`); the tree must be clean before starting a phase. If it is not, stop and report.
2. **Execute exactly one phase.** Phases run in numbered order. Never start a phase whose status is `done`, never run two phases in one session, never reorder. Each phase is sized for one session's fresh context.
3. **Partial phases.** If a phase cannot finish in the session, stop at a clean commit boundary, set its status to `in progress`, append a one-line resume note under the phase heading stating the last completed step, commit the plan update, and yield. The next session resumes from that step.
4. **Commits.** Commit as you go, one logical step per commit. Prose (`.md`) and code never share a commit. Codegen commits are always standalone with canonical messages: `Run generate-datamodels`, `Run generate-clients`, `Run generate-score`. Subjects under 72 characters, no body, no trailers. Never push — the operator pushes. Never rewrite history.
5. **Yield.** At phase end: run the phase's Verification block, set the phase status to `done` with the date and the last commit SHA, commit the plan update as its own prose commit, then yield to the operator with a summary that lists every error encountered and how it was resolved. The operator closes the session and points the next one at this file.
6. **Ambiguity rule.** If the code contradicts the ADR in a way this plan does not anticipate, or a step cannot be executed as written, stop and surface it in the yield. Do not improvise design decisions.

## Environment facts for every session

- Repo root `/workspace/placeframe`, branch `job-lifecycle`. Sandbox: uv on PATH (install from `https://astral.sh/uv/install.sh` if missing), GPU passthrough, `boatyard.values.yaml` pre-configured — never overwrite it.
- Sync before Python work: `uv sync --all-packages --extra cuda` from the repo root (never inside a service directory).
- Postgres for `generate-datamodels`: the preflight container pattern in phase 1 step 3 (throwaway postgres on host port 55432). Never run bare `docker compose`.
- Lint/type/format: `uv run ruff check .`, `uv run ruff format .`, `uv run basedpyright`.
- Tests: `uv run pytest <path>` scoped per phase; full battery only where the plan says so.

## Coherence brackets

The wire and schema change before every consumer does, so the tree deliberately does not typecheck or collect cleanly at every intermediate commit:

- **Bracket A (phases 1–3).** After phase 1's datamodels regen, `workloads/api` (references `ReconstructionStatus.CANCELLED`) and `workloads/lease-server` (references `requeue_count`) fail basedpyright and pytest collection. This is expected. Phases 2 and 3 rewrite those sources. Do not run basedpyright or unscoped pytest inside bracket A; run only the scoped checks each phase lists.
- **Bracket B (phase 4).** After the reconstructor source shim lands but before `Run generate-clients`, the reconstructor references client methods that do not exist yet. The regen commit closes the bracket; the full battery runs after it.

Outside these brackets the tree is green at every phase boundary.

## Status

| # | Phase | Status | Completed |
|---|---|---|---|
| 1 | Database schema and datamodels regen | done | 2026-11-24, 9b6f8076db38150d9fee8e8300bc76e2066f256c |
| 2 | Lease-server lifecycle rewrite | done | 2026-11-24, 1f73841845e0f983439dfe81fd5783d5b3985f79 |
| 3 | API pause, resume, and route removal | done | 2026-11-24, f35c12f61ff6af04adadd5793158d4740bcbb820 |
| 4 | Reconstructor wire migration and client regen | done | 2026-11-24, fc02fa30f7b98890f98f2ac67eb6131514cb338e |
| 5 | Artifact uploader and marker layer | done | 2026-11-24, 9ad947712930e34555f0802ce97bb48758040966 |
| 6 | Shard-as-you-go checkpointing | done | 2026-11-24, 8f1c353cff63b280de98110611bd0a5cc4b1a358 |
| 7 | Verification shard choreography | done | 2026-11-24, e729ddfbad4ecce3aae1691d6594675299139d64 |
| 8 | Score-tier config valve | done | 2026-11-24, 0cefd75fedcd2faa727dfeca188f5380c0a1b0ff |
| 9 | Agent-doc hardening | done | 2026-11-24, 5c1adf3342b704eb89ab7cea82c817d56dddbb87 |
| 10 | Endgame verification and handoff | done | 2026-11-24, 6e65f9a6952f9fec6d5a283aea7c6499971e680c |

## Phase 1 — Database schema and datamodels regen

Goal: the schema directory expresses the new row, the generated ORM follows, and the tool limit is recorded.

ADR cites: settled designs 1, 2, 5, 9, 13, 14, 21.

Steps:

1. Edit `database/21_reconstructions.sql`:
   - Enum `reconstruction_status`: add `'paused'`, drop `'cancelled'` and `'verifying_rig_geometry'`.
   - Rename column `requeue_count` to `error_count` (same type/default: `integer NOT NULL DEFAULT 0`).
   - Add `lease_attempt integer NOT NULL DEFAULT 0`.
   - Add `lease_heartbeat_at timestamptz` (nullable; set on grant and on every accepted progress write).
2. Edit `database/AGENTS.md`: add a short paragraph recording the tool limit per settled design 14 — Postgres cannot drop an enum value, and pg-schema-diff plans a removed value as `DROP TYPE` + `CREATE TYPE`, which fails while a table still uses the type; schema changes that remove enum values therefore require rebuilding the database from this directory, and no migration path exists.
3. Rebuild the local database so `generate-datamodels` introspects the new schema, using the preflight pattern from `scripts/preflight.py`. A plain `boatyard up` cannot work here: this phase's own schema edit remints the `.dockerignore`-derived tree tags for every placeframe image, which are unpublished in ghcr, and the compose postgres publishes no host port. Instead: `uv run boatyard build --targets 'postgres database-manager database-migrator'` (timeout 600000; resolves the tree tags locally with no registry push), remove the standing `pf-preflight-postgres` container if present, run a fresh throwaway postgres container on host port 55432, bootstrap the schema with the database-manager create image, and run the migrator hazard gate. The create image executes the schema directory directly — the same bootstrap path the compose provisioner runs.
4. `uv run generate-datamodels`. Confirm the diff under `packages/generated/python/datamodels/` shows: `error_count`, `lease_attempt`, `lease_heartbeat_at`, `paused` in the enum, `cancelled` and `verifying_rig_geometry` gone.
5. Commit the SQL change (code commit), the `database/AGENTS.md` change (prose commit), and the regen (standalone commit, message exactly `Run generate-datamodels`).

Verification: regen diff matches step 4; `git status` clean. Bracket A now open — do not run basedpyright.

## Phase 2 — Lease-server lifecycle rewrite

Goal: the lease-server implements lease identity, fencing, the refusal channel, heartbeats, the new timeout/budget rules, and `error`/`preempt`.

ADR cites: settled designs 1, 2, 3, 4, 5, 6, 8, 9, 17; problem statement defects 1–3.

Rewrite `workloads/lease-server/src/lease_server/routers/leases.py` (and `settings.py`, `main.py`, `routers/queue_state.py`, tests) as follows:

1. `settings.py`: add `lease_timeout_s: int = 1800` and `lease_heartbeat_cadence_s: int = 60`, with a pydantic model validator that raises when `lease_timeout_s < 3 * lease_heartbeat_cadence_s` (boot-time invariant, settled design 5). `LEASE_TIMEOUT`/`MAX_REQUEUE_ATTEMPTS` module constants move to settings (cap stays a constant, `MAX_ERROR_ATTEMPTS = 5`).
2. Models: `Lease` gains `lease_attempt: int`. `ProgressUpdate` gains `lease_attempt: int`. New `ErrorRequest(error: str)`. New `PreemptRequest(lease_attempt: int)`. `FailLeaseRequest` unchanged. All five fenced routes carry the echoed attempt.
3. Refusal channel: one shared 409 whose body carries a `reason` field with values `superseded` and `paused`, documented in the OpenAPI schema via `raises=` on the route handlers (implement with a dedicated `HTTPException` subclass; make the rendered body and the documented schema agree — the generated client is the contract test). Missing row stays a 404 (that is `not-found`).
4. Fencing predicate, applied to `progress`, `succeed`, `fail`, `error`, `preempt`, checked in this order:
   1. row missing → 404;
   2. row `PAUSED` → 409 `paused`;
   3. row terminal (`SUCCEEDED`/`FAILED`) → 409 `superseded`;
   4. echoed attempt ≠ `row.lease_attempt` → 409 `superseded`;
   5. row `QUEUED` (attempt matches) → 409 `superseded`;
   6. otherwise accept (row is in the WORKING family).
5. `request_lease` grant path: under the existing `FOR UPDATE SKIP LOCKED` selection, also set `lease_attempt = lease_attempt + 1` and `lease_heartbeat_at = now()` when flipping out of `QUEUED`; the response carries the post-increment attempt.
6. Reaper (still runs inside `request_lease`, own transaction): stale filter becomes status not in (`QUEUED`, `PAUSED`, terminal) and `lease_heartbeat_at < now() - timeout`. `PAUSED` is excluded — this is the one trap (settled design 9). Below cap: `status=QUEUED`, `error_count + 1`, `error='lease timed out'`, progress cleared. At/above cap: `status=FAILED`, `error_count` unchanged, `error` left as-is when non-null else `'lease timed out'`. Delete the stale-filter comment asserting `updated_at` refreshes on every write — that belief is defect 2.
7. `progress`: fenced, then a single `UPDATE ... SET status=..., progress_current=..., progress_total=..., progress_attempt=..., error=..., lease_heartbeat_at=now() WHERE id=... AND lease_attempt=... AND status NOT IN (queued, paused, succeeded, failed)` — a core update that always executes, so no-op writes persist the heartbeat (settled design 5). Refuse `data.status` values outside the WORKING family with 422.
8. `error` route (replaces `requeue`): fenced, then below cap `status=QUEUED`, `error_count + 1`, `error=data.error`, progress cleared; at/above cap `status=FAILED`, `error_count` unchanged, `error=data.error`. Both branches answer 200 identically (settled design 17).
9. `preempt` route: fenced, then `status=QUEUED`, `error_count` unchanged, `error=None`, progress cleared. Never fails the job.
10. `succeed`: fenced, then today's terminal flip plus metrics-merge into the manifest, `error=None`. `fail`: fenced, then today's flip plus error string and optional metrics merge. Neither counts.
11. `queue_state.py`: `NON_ACTIVE_STATUSES` gains `PAUSED` (queued count still counts only `QUEUED`; PAUSED lands in neither bucket).
12. `main.py`: no app wiring changes expected; if the boot invariant fits better as a startup hook than a settings validator, put it there. Either way a misconfigured pair must crash the server at startup, not at first reap.
13. Tests: extend the stub-session harness in `workloads/lease-server/tests/` (style of `test_queue_state.py`; add a new `test_leases.py`). Cover at minimum: fencing rejection on all five writes (each refusal reason, including late-succeed-on-FAILED and matching-attempt-on-QUEUED), heartbeat persistence across no-op progress writes (assert the rendered UPDATE touches `lease_heartbeat_at` unconditionally), budget counting rules (error counts, preempt never counts, reap counts, exhaustion flips to FAILED), and the reaper's PAUSED exclusion.

Commits: source and tests as code commits; nothing prose.

Verification: `uv run ruff check .`, `uv run ruff format .`, `uv run basedpyright workloads/lease-server`, `uv run pytest workloads/lease-server`. Bracket A still open for the api.

## Phase 3 — API pause, resume, and route removal

Goal: the api exposes `pause`/`resume`, drops `retry`, and the tar export filters shards.

ADR cites: settled designs 4, 9, 13, 15, 16, 19.

Steps on `workloads/api/src/routers/reconstructions.py`:

1. Remove `retry_reconstruction` and its router entry.
2. `POST /{id:uuid}/pause` → `ReconstructionReadWithQueue`: non-terminal (anything except `SUCCEEDED`/`FAILED`) → `PAUSED`; already `PAUSED` → no-op returning the row; terminal → 409 with the existing detail style. Clears nothing but the status.
3. `POST /{id:uuid}/resume` → `ReconstructionReadWithQueue`: `PAUSED` or `FAILED` → `QUEUED`, `error_count = 0`, `error = None`, progress fields cleared (`lease_attempt` stays — it is monotonic identity, never reset); already `QUEUED` → no-op returning the row; `SUCCEEDED` → 409 ("a finished job is not resumed — build a new row"); WORKING-family → 409.
4. `delete_reconstruction`: behavior unchanged; extend the route's OpenAPI description with the delete-during-flight semantics — deleting a row mid-flight cascades the artifact prefix, and a still-running worker learns of the deletion as a 404 on its next write and stops.
5. `iter_reconstruction_tar`: skip keys under `shards/` in addition to the existing `database.db` exclusion (settled design 19).
6. Update `workloads/api/tests/` coverage: pause/resume/delete transitions including the late-succeed-on-FAILED race surface (the api-side share: pause on terminal 409, resume idempotence, resume-on-SUCCEEDED 409, retry gone). Follow the existing api test harness style.

Commits: code commits.

Verification: `uv run ruff check .`, `uv run ruff format .`, `uv run basedpyright`, `uv run pytest workloads/api workloads/lease-server`. basedpyright is now green workspace-wide (bracket A closed); `generate-clients --check` is still stale by design and is not run until phase 4.

## Phase 4 — Reconstructor wire migration and client regen

Goal: the reconstructor speaks the new wire, the generated clients match both specs, and the whole battery is green.

ADR cites: settled designs 2, 3, 5, 7, 8, 17.

Steps:

1. `workloads/reconstructor/src/reconstructor/main.py`:
   - `worker_loop`: after the executor run, a `LeaseLostError` escaping `run_reconstruction` (see below) is caught here — log it and continue the poll loop with no route call (the job is no longer this worker's).
   - Result reporting per settled design 8: completed-but-unsuccessful → `fail` (metrics + error string); any other exception → the `error` route with `str(e)`; success → `succeed`.
   - SIGTERM path: `_requeue_and_exit` becomes `_preempt_and_exit` — call `preempt_lease` with the echoed attempt (transport failure is logged, not retried past the stop budget), then `os._exit(0)`. A refused preempt (409) proceeds to exit.
   - Per-lease heartbeat task on the event loop: every `settings.lease_heartbeat_cadence_s` seconds, re-dispatch the publisher's last update (settled design 5 — the floor cadence). Create it when the lease starts, cancel it when the lease ends.
2. `workloads/reconstructor/src/reconstructor/settings.py`: add `lease_heartbeat_cadence_s: int = 60`.
3. `workloads/reconstructor/src/reconstructor/progress_publisher.py`:
   - `ReconstructionPublisher` is constructed with the granted `lease_attempt` and includes it in every `ProgressUpdate`.
   - The flusher's failure callback distinguishes a 409/404 refusal from transport failure: refusal sets a lost-flag on the publisher (reason recorded); transport failures stay log-only.
   - Add `raise_if_lease_lost()` raising `LeaseLostError` (defined here, the refusal translation site) when the flag is set. Call sites: `set_phase`, each shard-loop iteration (phases 6–7 add these), immediately after `run_colmap_reconstruction` returns, and before reporting the result in `main.py`. A lost lease must never trigger `fail`/`error`.
4. Regen: from the repo root, `uv sync --all-packages --extra cuda`, then `uv run generate-clients --config openapi-client-codegen.yaml` (full run — both specs changed). Confirm `packages/generated/python/lease-server-client/` gains `error_lease`/`preempt_lease`/`lease_attempt` and loses `requeue_lease`; `packages/generated/python/api-client/` gains pause/resume and loses retry; the C# and typescript-fetch outputs follow.
5. Commit the reconstructor source (code commit), then the regen (standalone commit, message exactly `Run generate-clients`).

Verification: full battery — `uv run ruff check .`, `uv run ruff format .`, `uv run basedpyright`, `uv run pytest`, then `uv run --locked scripts/preflight.py` (timeout 600000). All green; both brackets closed. Report any preflight database-battery findings in the yield.

## Phase 5 — Artifact uploader and marker layer

Goal: all artifact writes flow through the bounded async uploader; markers are the commit point; GC-at-success exists.

ADR cites: settled designs 10 (write path), 12, 19.

Steps:

1. New `workloads/reconstructor/src/reconstructor/uploader.py`:
   - `ArtifactUploader(s3_client, bucket, reconstruction_id, pipeline_version, options_hash)` with a bounded `queue.Queue` (maxsize 64) drained by one background thread. Full queue blocks the producer — backpressure, never drop.
   - `put_artifact(key, body)`; `put_shard(prefix, files: dict[str, bytes], marker_extra)` enqueues the data objects then the marker last — the marker is written by the uploader thread only after that shard's PUTs have all succeeded (marker-last is the atomicity story).
   - PUTs retry in place with exponential backoff 1 s → 60 s, unbounded retries (the blip-absorption layer).
   - `drain(timeout_seconds)`: wait until queue empty and no in-flight PUT; returns whether it completed. Used before `succeed` (no timeout) and on SIGTERM (timeout 55).
   - Marker JSON schema, written as `<prefix>/marker.json`: `{ "options_hash": ..., "pipeline_version": ..., "files": {<relative name>: <sha256 hex>}, "shard_index": ..., "shard_count": ... }`. `options_hash` = sha256 of `json.dumps(reconstruction_options.model_dump(mode="json"), sort_keys=True)`. `pipeline_version` = `RECONSTRUCTOR_SHA` (already the env source of `metrics.pipeline_version`).
   - `delete_shard_prefix()`: paginate `list_objects_v2` under `shards/` and batch `delete_objects` (mirror `delete_reconstruction` in the api).
2. `run_reconstruction.py` and `colmap.py`: replace every `_put_artifact` call with uploader submits; delete `_put_artifact`. The `database.db` upload stays last (its presence implies SfM ran). `run_reconstruction` does not return metrics until `uploader.drain(...)` completes.
3. GC at success (settled design 19): in `main.py`, after an accepted `succeed_lease` (2xx), call `uploader.delete_shard_prefix()`; after a refused `succeed` (409), skip deletion — the job is no longer this worker's. A `FAILED` job keeps everything.
4. SIGTERM: `_preempt_and_exit` drains the uploader first (`loop.run_in_executor(None, uploader.drain, 55.0)`), then calls `preempt`, then exits. A drain timeout proceeds to exit anyway — the unwritten marker is the crash detector.
5. Tests `workloads/reconstructor/tests/test_uploader.py`: bounded-queue backpressure (put blocks when full), marker written only after shard PUTs succeed (inject a failing PUT, assert no marker), drain completes/quits on timeout, marker schema round-trip.

Commits: code commits.

Verification: `uv run ruff check .`, `uv run ruff format .`, `uv run basedpyright`, `uv run pytest workloads/reconstructor`.

## Phase 6 — Shard-as-you-go checkpointing

Goal: extraction and matching upload incrementally with markers; resume skips completed shards; descriptors persist at float16.

ADR cites: settled designs 10 (granularity table, resume semantics, descriptor shards), 12.

Shard layout under `reconstructions/<id>/` (fixed; the api's tar filter from phase 3 already skips it):

```
shards/features/<index:05d>/keypoints.h5  descriptors.h5  global_descriptors.h5  sizes.json  marker.json
shards/matches/<index:05d>/pairs.json  matches.npz  marker.json
shards/verification/<index:05d>/pairs.json  two_view_geometries.npz  marker.json   (phase 7)
shards/training/opq.marker.json  pq.marker.json
```

Constants: `FEATURE_SHARD_SIZE = 64` images, `MATCH_SHARD_SIZE = 512` pairs.

Steps:

1. `packages/python/core` `placeframe_core/h5.py`: add `write_descriptors`/`read_descriptors` (float16 on disk; the working precision cast happens on load). The existing `write_features`/`write_global_descriptors`/`write_opq_matrix`/`write_pq_quantizer` are reused for shards by passing per-shard subset dicts; add read counterparts where missing (`read_opq_matrix`, `read_pq_quantizer`) for the resume path.
2. `matches.npz` layout: arrays `pair_first` (int64) and `pair_second` (int64) giving row → pair, plus concatenated `match_a`/`match_b` (uint32) with `match_offsets` boundaries; `pairs.json` lists the `[image_a, image_b]` names in the same order.
3. Extraction loop: chunk `image_list` into feature shards; after each shard completes, `uploader.put_shard("shards/features/<index>", ...)` with keypoints/descriptors(float16)/global-descriptors/sizes. The consolidated final artifacts (`global_descriptors.h5`, and `features.h5` after encode) still upload once at their stage ends as today — shards are the resume record, deleted at success.
4. Training stages: unchanged single files plus stage markers `shards/training/opq.marker.json` / `pq.marker.json` (marker checksums the artifact bytes). Encode/`features.h5`: unchanged, one file.
5. Matching: chunk the pair list into match shards; upload each as it completes, with per-shard progress. (If `local_feature_matcher` cannot be driven per-batch, run it as today and shard the upload of its outputs — the marker granularity is the upload, and per-pair progress already exists.)
6. Resume path at the top of `run_reconstruction`: always download and extract the capture tar; always re-canonicalize every image to disk (SfM needs the processed files); then list `shards/**/marker.json`, validate `options_hash` and `pipeline_version` against the current lease (mismatch ⇒ ignore and overwrite — a re-run with different options must not reuse stale outputs), and rebuild in-RAM state from valid shards: keypoints, descriptors (cast to working precision), global descriptors, sizes. Pairs recompute in memory. Each shard loop starts at the first unmarked shard. SfM always re-runs whole.
7. Tests `workloads/reconstructor/tests/test_shards.py`: marker validation (hash/version mismatch ⇒ overwrite; match ⇒ skip), resume-skip logic (first unmarked index selection), float16 round-trip fidelity tolerance.

Commits: code commits; `placeframe_core` changes may share the phase's code commits (same repo).

Verification: `uv run ruff check .`, `uv run ruff format .`, `uv run basedpyright`, `uv run pytest workloads/reconstructor packages/python/core` (if core has tests; otherwise reconstructor only).

## Phase 7 — Verification shard choreography

Goal: verification drives the stock kernel per frame-pair-grouped shard; the poller is deleted; one status; resume replays.

ADR cites: settled designs 11, 21; the kernel constraint (no skip of already-verified pairs).

Steps on `workloads/reconstructor/src/reconstructor/colmap.py`:

1. Delete `_VerificationProgressPoller` and `_poll_verification` (and their imports: `subprocess`, `sys`, `inspect`, `sqlite3` where now unused).
2. Partition function (new, unit-tested): group the sorted pair list by frame-pair key — `(rig_id, frame_id)` of each side, order-normalized — then pack groups into shards up to `VERIFY_SHARD_MAX_PAIRS = 4096` pairs, never splitting a frame-pair group (an arbitrary split breaks rig aggregation, settled design 11).
3. Shard loop, replacing the single whole-stage `geometric_verification` call:
   1. write the shard's match rows (`database.write_matches`);
   2. close the handle, run `geometric_verification(database_path=..., verifier_options=GeometricVerifierOptions(rig_verification=True), two_view_geometry_options=...)` — the stock kernel, unmodified;
   3. harvest the shard's two-view geometries (`database.read_two_view_geometry` per pair) into `shards/verification/<index>/` (`two_view_geometries.npz` per-pair: config, `cam2_from_cam1` qvec/tvec, E/F/H matrices, inlier indices; `pairs.json` alongside), via the uploader with marker-last;
   4. delete the shard's match rows from the matches table (plain `sqlite3` DELETE on the database file between kernel calls — the table is scratch, the shards are the record);
   5. `publisher.on_progress(shards_done, shard_count)` under `VERIFYING_GEOMETRY` for the whole stage, and `publisher.raise_if_lease_lost()` per iteration.
4. After the last shard: final parity rewrite — write all matches back (from the match shards in RAM, re-downloading nothing) so the uploaded `database.db` keeps today's shape; then `_apply_vio_em_check`, then metrics, then SfM as today.
   5. Resume: after the DB build (cameras/images/keypoints/priors/rig config), replay completed verification shards — reconstruct `TwoViewGeometry` objects from npz and `database.write_two_view_geometry` per pair (the pinned pycolmap's `update_two_view_geometry` is a silent no-op on a missing row, and resume always rebuilds the DB, so rows never pre-exist) — then enter the loop at the first unmarked shard. The VIO essential-matrix check and metrics run on the complete DB exactly as on a fresh pass.
6. Tests `workloads/reconstructor/tests/test_verification_shards.py`: the partition function (frame-pair grouping never split; cap respected; deterministic), and a sqlite-level choreography test — build a tiny COLMAP database via the pycolmap `Database` API, drive one shard through write/kernel/harvest/delete, assert the matches table is empty and the shard artifact round-trips (pycolmap is in the venv with `--extra cuda`).

Commits: code commits.

Verification: `uv run ruff check .`, `uv run ruff format .`, `uv run basedpyright`, `uv run pytest workloads/reconstructor`.

## Phase 8 — Score-tier config valve

Goal: the lease timeout and heartbeat cadence are deployment settings in both renderings.

ADR cites: settled design 6.

Steps:

1. `stack/score/compose/config.yaml` and `stack/score/k8s/config.yaml` (the placeframe-config twins): add outputs `lease_timeout_s: ${LEASE_TIMEOUT_S:-1800}` and `lease_heartbeat_cadence_s: ${LEASE_HEARTBEAT_CADENCE_S:-60}`.
2. `stack/score/lease-server.yaml`: add variables `LEASE_TIMEOUT_S: ${resources.config.lease_timeout_s}` and `LEASE_HEARTBEAT_CADENCE_S: ${resources.config.lease_heartbeat_cadence_s}` (the cadence rides the lease-server for the boot invariant).
3. `stack/score/reconstructor.yaml`: add variable `LEASE_HEARTBEAT_CADENCE_S: ${resources.config.lease_heartbeat_cadence_s}` — one valve feeds both consumers, so the pair cannot diverge per deployment.
4. Regenerate the score artifacts from a clean clone of the branch tip (the working tree carries ignored dirt that would mint unreproducible tags): `git clone --branch job-lifecycle . /tmp/opencode/clean && cd /tmp/opencode/clean`, run `uv run boatyard generate-score` there, copy `stack/generated/**` back. Commit as a standalone canonical commit, message exactly `Run generate-score`.

Verification: the four compose artifacts and `k8s/manifests.yaml` diff shows only the new config passthroughs and variables; `uv run pytest scripts/tests` (the score generation structure tests) still passes; `git status` clean.

## Phase 9 — Agent-doc hardening

Goal: the co-located agent docs describe the shipped truth; the stale verifier description is corrected.

ADR cites: settled design 13, and the §11 note that `workloads/reconstructor/AGENTS.md` describes the pre-June verifier as shipped.

Steps (prose commits; keep each doc to what a reader cannot derive from code, per the AGENTS-SHARED doc rules):

1. Create `workloads/lease-server/AGENTS.md` (+ its one-line `@AGENTS.md` `CLAUDE.md` import): the lifecycle law — states, the five fenced writes and the refusal channel, heartbeat/timeout/budget rules, the reaper's PAUSED exclusion, the no-migration rebuild rule.
2. `workloads/reconstructor/AGENTS.md`: replace the thread-pool verifier narrative with the shard-loop choreography; add the refusal channel and abandon behavior, the shard layout, the GC-at-success rule, the uploader's marker-last commit point, float16 descriptor storage, and the resume path.
3. `workloads/gpu-orchestrator/AGENTS.md`: flip the S11 paragraph from reservation to description — preemption now costs a checkpoint cycle inside the 60 s stop budget, the orchestrator still only stops containers and reads `queue-state`, PAUSED counts in neither bucket.
4. `workloads/AGENTS.md`: update the data-flow section and the lease-server row (endpoint list: `request`, `progress`, `succeed`, `fail`, `error`, `preempt`; PAUSED in the state list).

Verification: prose only; `git status` clean after commits.

## Phase 10 — Endgame verification and handoff

Goal: prove the branch, close PR #172, hand off.

Steps:

1. `uv run --locked scripts/preflight.py` (timeout 600000) — full battery including the database container and codegen staleness. Fix anything it raises (fix, commit, rerun).
2. Close PR #172 with a pointer: `GH_TOKEN=$(uv run mint-github-app-token) gh pr close 172 --comment "Superseded by the job-lifecycle branch (reconstruction-job-lifecycle.md and its execution plan at the repo root)."` — if `gh` is unavailable or the token lacks scope, record it as an operator action instead.
3. Update this plan: all phases `done`.
4. Yield with the handoff summary. It must list, explicitly:
   - the branch (`job-lifecycle`) and its HEAD SHA for the operator to push — the sandbox cannot push;
   - the capture-tool companion change (its repo, mounted at `/placeframe-capture-tool`): drop `Cancelled` arms, handle `Paused` in status mapping/label/polling, call `resume` where it called `retry` — lands when it bumps its api-client pin;
   - PR #172's fate as executed in step 2;
   - the ADR's and this plan's fate: the operator's decision, not further agent work;
   - every error encountered across the phase and its resolution.

Verification: preflight green; `git log --oneline` shows canonical codegen commits standing alone.

## Out of scope (do not do)

- The gpu-orchestrator's code (only its agent doc changes, phase 9).
- The localizer, including request threading and replica orchestration.
- The capture-tool repo's code (handoff item only).
- Earn-back accounting, retry backoff/parking, orphan-shard cleanup (ADR "Deliberately deferred").
- Any migration path for pre-existing databases (settled design 14).
