---
updated: 2026-10-31
---

# Shared-GPU coordination — execution plan

Execution plan for [shared-gpu-coordination.md](shared-gpu-coordination.md)
(the ADR; all decisions of record live there). The ADR describes the what and
why; this doc sequences the how. Mechanism references below are grounded at
branch `compose-bundles`, `7138eb6d` and will drift.

## Execution protocol

One phase per session. A session: read this plan and the ADR, implement the
one phase, verify, commit, stop at the phase boundary. Do not bleed into the
next phase; do not "improve" adjacent code. Every phase closes with:

1. `uv run ruff check . && uv run ruff format . && uv run basedpyright`
   and the phase's tests (`uv run pytest <paths>`).
2. `uv run --locked scripts/preflight.py` — the full battery (spins its own
   throwaway postgres on :55432; needs Docker). A phase is not done until
   this passes.
3. Commits per repo discipline: prose and code separate; regenerated
   artifacts in dedicated canonical commits (`Run generate-clients`,
   `Run generate-datamodels`, `Run generate-clients and generate-datamodels`,
   `Run generate-score`).

Preflight's `generate-clients --check` makes client staleness a hard error,
so every phase that changes an OpenAPI surface regenerates clients at its
boundary. That is why regens appear inside phases rather than once at the
end.

## End state

Once the last phase lands, all of the following hold. Each phase cites the
subset it delivers.

- A `gpu_sessions` row in Postgres is the GPU mutex: session exists ⟺ the
  localizer holds or is acquiring VRAM. TTL 60 s, heartbeat 15 s, renewal
  grace 3 heartbeats.
- `POST /leases/request` refuses with a typed 409 while a live session
  exists; `POST /gpu-sessions/acquire` refuses with a typed 409 while any
  reconstruction row is claimed. Both refusals serialize through the same
  Postgres advisory lock — no check-then-act window.
- The reconstructor loads models per-job (after grant) and unloads before
  the terminal `succeed`/`fail` PUT, in every deployment mode. Idle VRAM
  cost while lease-less: zero.
- The localizer selects shared mode by a non-empty `LOCALIZER_LEASE_SERVER_URL`.
  Shared mode: acquire-at-boot or start unloaded; heartbeat-renew; unload and
  release on idle (`LOCALIZER_IDLE_TIMEOUT`, default 300 s, `0` = never),
  on operator yield, and on renewal failure past grace (fail-safe to the
  mutex); demand-loads inline on the next request. Refusals are typed 503s
  carrying `code` only: `gpu_busy_reconstruction_active` or
  `coordinator_unreachable`. Unreachable coordinator at boot is a loud boot
  failure, never a silent fallback to exclusive.
- Exclusive mode (URL absent/empty, and always on k8s) is byte-for-byte
  today's behavior.
- The API passes the typed localizer 503 through (no 502 collapse) and
  derives `blocked_by: localizer_active` on a queued reconstruction's status
  while a session is live (poll-derived; no push channel; omitted, never
  errored, when the lease-server is unreachable).
- `uv run localizer yield` asks the lease-server to flag the live session;
  the localizer unloads and releases at its next heartbeat.
- Compose core bundles wire the URL and timeout with defaults on
  (`.env` empty-override = exclusive; k8s config emits empty = never);
  `.env.sample` documents both knobs.

## Phases

### 1. Reconstructor per-job model lifecycle

Smallest independent unit; halves the VRAM problem on every host before any
coordination exists. No schema, no OpenAPI, no other service touched.

- `workloads/reconstructor/src/reconstructor/main.py`: drop the boot-time
  `load_models()` call at `main()` (`main.py:128`); call `load_models()`
  inside `_run_and_report` after the lease is acquired, before dispatching
  `run_reconstruction`.
- `workloads/reconstructor/src/reconstructor/run_reconstruction.py`: add
  `unload_models()` — clear the module-level model globals, `gc.collect()`,
  `cuda.empty_cache()` (mirrors `load_models` at `run_reconstruction.py:79`).
  `_run_and_report` calls it after the pipeline returns and before both the
  `succeed_lease` and `fail_lease` PUTs (success path and exception path) —
  unload-before-terminal-PUT is the correctness requirement that closes the
  overlap window.
- SIGTERM handling is unchanged: `_requeue_and_exit`'s `os._exit(0)` frees
  CUDA memory via process death; the lease is requeued first.

Verification: ruff/pyright/pytest; existing `tests/test_rig.py` untouched and
green. Optional manual check with a live stack: `nvidia-smi` shows no
reconstructor VRAM while it idle-polls.

Commit: one code commit.

### 2. Lease-server GPU session resource

The foundation both consumers build on. Adds the table, five endpoints, the
grant gate, and regen #1.

- `database/31_gpu_sessions.sql`: `gpu_sessions` (the name
  `localization_sessions` is taken by an unrelated, unconsumed table in
  `30_localization_sessions.sql`):
  `id uuid PK default gen_random_uuid`, `holder text not null`,
  `expires_at timestamptz not null`, `yield_requested boolean not null
  default false`, `updated_at timestamptz not null default now()`; a partial
  unique index enforcing a single row; `GRANT` to
  `placeframe_orchestration_user` following the pattern at
  `database/21_reconstructions.sql:60`. No tenant columns — this is
  control-plane state, same as the lease the grant gate lives in.
- `workloads/lease-server/src/routers/gpu_sessions.py` (new), mounted in
  `main.py`:
  - `POST /gpu-sessions/acquire` `{holder}` → 201 session, or typed 409
    `{code: "reconstruction_active"}` while any row is claimed
    (non-QUEUED, non-terminal). Reaps expired sessions first; acquire
    replaces any existing row in one transaction.
  - `POST /gpu-sessions/{id}/heartbeat` → 200 `{yield_requested}` and
    extends `expires_at = now() + 60 s`; 404 when the session was reaped
    (client treats as renewal failure).
  - `POST /gpu-sessions/{id}/release` → 204, deletes the row.
  - `POST /gpu-sessions/yield` → 204 sets `yield_requested` on the live
    row; 404 when none.
  - `GET /gpu-state` → `{live, holder, expires_at}`.
- Grant gate in `request_lease` (`routers/leases.py:46`): after the existing
  reaper block, take `pg_advisory_xact_lock` on a fixed key shared with
  `acquire`; reap expired sessions; live session ⇒ typed 409
  `{code: "localizer_session_active"}` instead of granting. The advisory
  lock is the serializer — a plain EXISTS check races a concurrent
  QUEUED→active flip in a way row locks on existing rows cannot close.
- Reconstructor poll loop (`main.py:56-65`): handle the 409 distinctly —
  Info log "GPU busy: localizer session active", sleep, continue (the
  current fallthrough would log it as a Critical Worker Error).
- Tests: new `workloads/lease-server/tests/` following the DB-fixture
  pattern of `workloads/api/tests/conftest.py`: acquire-vs-claim mutual
  exclusion both directions, heartbeat renew + yield flag, reaper, release
  re-enables grant.

Regen sequencing inside this phase (order is load-bearing): postgres up →
`uv run generate-datamodels` (new table models) → `uv sync --all-packages`
→ `uv run lock-python` → `uv run generate-clients --config
openapi-client-codegen.yaml` (lease-server client gains the endpoints).
Commits: source code commit(s), then canonical `Run generate-clients and
generate-datamodels`.

### 3. Localizer shared-mode core

Session lifecycle without the idle timer — at the end of this phase the
localizer acquires, heartbeats, honors yield, and fail-safes, but never
voluntarily unloads (behavior of `LOCALIZER_IDLE_TIMEOUT=0`).

- `workloads/localizer/pyproject.toml`: add `placeframe-lease-server-client`.
  Then `uv sync --all-packages` + `uv run lock-python`.
- `workloads/localizer/src/settings.py`: `lease_server_url: str | None`
  (empty string normalizes to None — the off switch),
  `heartbeat_interval_seconds: int = 15`, `renewal_grace_heartbeats: int =
  3`. CODEGEN-aware like the existing fields.
- `workloads/localizer/src/gpu_session.py` (new): a `GpuSessionManager`
  owning acquire / heartbeat loop / release / yield handling / renewal
  failure handling, parameterized by load/unload callbacks so it is testable
  without a GPU. Semantics:
  - Boot (shared mode): acquire before models load. Granted ⇒ load, serve.
    Refused (reconstruction active) ⇒ start unloaded. Coordinator
    unreachable ⇒ raise at boot (loud; container restarts) — never fall
    back to exclusive.
  - Heartbeat task (asyncio, started from the app lifespan — extend the
    `create_litestar_app` wiring in `placeframe_common` if it lacks a
    startup-hook parameter): renew every 15 s. Renewal failure within grace
    ⇒ keep retrying; past grace ⇒ unload + attempt reacquire; reap-404 ⇒
    unload immediately + attempt reacquire (holding VRAM session-less is
    the one forbidden state). Reacquire refused ⇒ stay unloaded and refuse
    requests.
  - `yield_requested` observed on any heartbeat response ⇒ unload +
    release.
  - `ensure_for_request()`: loaded ⇒ proceed; unloaded ⇒ acquire (refused ⇒
    503, provisional `detail` string this phase) then load inline. One
    uvicorn worker serializes requests; no half-states.
- `workloads/localizer/src/localize.py`: add `unload_models()` clearing the
  three model globals, `gc.collect()`, `cuda.empty_cache()`; `load_models`
  unchanged (still CODEGEN-guarded).
- `workloads/localizer/src/main.py`: shared mode routes boot and the
  `/localization` handler through the manager; exclusive mode (URL absent)
  keeps today's import-time load exactly. All new code paths stay
  CODEGEN-safe (`dump_openapi` must not need the lease-server or torch).
- Tests: `workloads/localizer/tests/test_gpu_session.py` against a stubbed
  client — state transitions for boot-refused, demand-load, yield, grace
  expiry, reap-404, coordinator-down-at-boot.

Verification: full battery + preflight (no OpenAPI change yet — the
provisional 503 is an undeclared detail string, so clients stay current).

Commits: code commit; lock-file changes ride the phase's regen commit in
phase 4? No — `uv.lock`/`pylock.toml` changes are source-adjacent, commit
them with the code in this phase; phase 4's regen is client-only.

### 4. Localizer idle unload + typed refusals

- Idle clock: manager records the last `/localization` completion; the
  heartbeat task unloads + releases when `now - last_activity >
  LOCALIZER_IDLE_TIMEOUT` (default 300 s, `0` disables). `/version` and
  healthchecks never touch the clock. `_maps` cache survives all unload
  cycles — model weights only.
- Typed refusals: declare a 503 response schema on `/localization` in the
  OpenAPI config — `{code: "gpu_busy_reconstruction_active" |
  "coordinator_unreachable"}`. Replace the provisional detail strings.
  Coordinator-unreachable mid-session (post-grace) and at request time uses
  the second code.
- Regen: `uv run generate-clients --config openapi-client-codegen.yaml`
  (localizer client now carries the 503 schema). Canonical
  `Run generate-clients`.

Verification: battery + preflight (clients current again). Manual optional:
`nvidia-smi` shows VRAM drop after the idle timeout.

### 5. Operator yield verb

- `scripts/src/scripts/localizer_cli.py` (new): typer app, `yield` command.
  The lease-server has no host port (network isolation is the security
  boundary), so the verb uses the Docker SDK (per `placeframe_common`'s
  docker utilities) to find the running lease-server container and exec
  `curl -X POST localhost:8000/gpu-sessions/yield` inside it. Prints the
  outcome: no live session, or session holder + "yield flagged; localizer
  unloads within one heartbeat (≤15 s)". Exit non-zero only on
  infrastructure failure (no container, exec failure), not on "no session".
- `scripts/pyproject.toml`: `localizer = "scripts.localizer_cli:app"`
  (typer entry point uses `:app`).

Verification: `uv run localizer --help`, unit test of the command against a
stubbed docker client, battery + preflight. Manual against a live stack
with a session held.

Commit: code commit.

### 6. API surfacing

- `workloads/api/src/routers/localization.py:109-113`: on `ApiException`
  status 503 from the localizer, re-raise a 503 carrying the same `code`
  (pass the body through); 422 unchanged; everything else stays the 502.
- `workloads/api/src/routers/reconstructions.py`: `get_reconstruction`
  (`:240`) — when the row is QUEUED, ask the lease-server `GET /gpu-state`;
  live session ⇒ `blocked_by="localizer_active"` on the
  `ReconstructionReadWithQueue` response. Lease-server unreachable or URL
  unset ⇒ field omitted/None — the derived field fails open, a status
  endpoint must not 500 because a sidecar is down.
- `workloads/api/src/settings.py`: `lease_server_url: str | None = None`
  (wired in phase 7; None ⇒ blocked_by never set).
- `workloads/api/pyproject.toml`: add `placeframe-lease-server-client`;
  `uv sync --all-packages` + `uv run lock-python`.
- Tests: proxy 503 pass-through (stub client), blocked_by derivation with a
  stubbed gpu-state (live / none / unreachable).
- Regen: `generate-clients` (api python + C# gain the 503 + `blocked_by`).
  Canonical `Run generate-clients`.

Verification: battery + preflight.

### 7. Stack wiring

- `stack/score/compose/config.yaml`: config-provisioner outputs
  `localizer_lease_server_url: ${LOCALIZER_LEASE_SERVER_URL:-http://lease-server:8000}`
  and `localizer_idle_timeout: ${LOCALIZER_IDLE_TIMEOUT:-300}` — the
  soft-passthrough pattern the AUTH_* block uses, but default-on: unset ⇒
  default; set-to-empty ⇒ empty ⇒ localizer treats as absent ⇒ exclusive.
- `stack/score/k8s/config.yaml`: same outputs, empty defaults — k8s never
  wires shared mode (dedicated GPU nodes; a session row would gate a fleet).
- `stack/score/localizer.yaml`: consume both outputs as container
  variables `LOCALIZER_LEASE_SERVER_URL` / `LOCALIZER_IDLE_TIMEOUT`.
- `stack/score/api.yaml`: `LEASE_SERVER_URL: http://lease-server:8000`
  (fixed literal in both renderings; on k8s sessions never exist so
  gpu-state is always idle and blocked_by never fires).
- `.env.sample`: document both knobs — default-on, empty = exclusive
  (disjoint-GPU boxes), `LOCALIZER_IDLE_TIMEOUT=0` = never-unload
  (AR-supremacy; reconstructions run only after `uv run localizer yield`).
- Regen: `uv run generate-score`. Canonical `Run generate-score`
  (`stack/generated/` compose + k8s artifacts).

Verification: `uv run up --quiet-pull`, then observe: localizer acquires at
boot (`docker exec` psql: one `gpu_sessions` row), localize works,
reconstruction queued while localizing ⇒ grant 409 + `blocked_by`, idle
timeout drops VRAM in `nvidia-smi`, `uv run localizer yield` unblocks.
This phase's verification is the one mandatory end-to-end pass.

### 8. Promotion and closeout

- Fold hardened truth into co-located docs: `workloads/localizer/AGENTS.md`
  (boot lifecycle, shared mode, idle/yield/fail-safe), new small
  `workloads/lease-server/AGENTS.md` (session endpoints, grant gate,
  advisory-lock rationale), `workloads/reconstructor/AGENTS.md` (per-job
  lifecycle), `workloads/AGENTS.md` (session resource + blocked_by + yield
  in the data-flow section), `scripts/AGENTS.md` (the verb),
  `stack/AGENTS.md` (the two knobs). Prose commits, separate from any code.
- ADR status section: mark execution complete; both design docs stop being
  load-bearing (files remain).

## Regens at a glance

| Phase | Regen | Canonical commit |
|---|---|---|
| 2 | datamodels + all clients | `Run generate-clients and generate-datamodels` |
| 4 | clients (localizer 503 schema) | `Run generate-clients` |
| 6 | clients (api 503 + blocked_by) | `Run generate-clients` |
| 7 | score artifacts | `Run generate-score` |
