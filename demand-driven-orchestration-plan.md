---
updated: 2026-11-21
---

# Demand-driven GPU orchestration — execution plan

Execution plan for [demand-driven-orchestration.md](demand-driven-orchestration.md)
(the ADR; all decisions of record live there — S1-S12, Q1-Q8, the planning-review
settlements). The ADR describes the what and why; this doc sequences the how. It
implements the ADR exactly; where instinct disagrees, the ADR wins. Mechanism
references are grounded at branch `gpu-orchestration`, `7003f7ce` and will drift.

## Execution protocol

Progress: **all four phases complete** (2026-11-21); the initiative is closed.
Three settlements landed during execution (detail in the ADR's status section): the `/gpu-mode/*` claim carries an explicit `, strip` under the
boatyard 0.9.3 claims grammar, the lease-server was restructured into an
installable `src/lease_server` package (flat `src` collides with the api's in
the combined test battery), and the plan's `extra_headers` spelling for
litestar's exception-carried response headers is starlette vocabulary —
litestar's kwarg/attribute is `headers`, so the shared handler forwards
`exception.headers` (same mechanism, corrected spelling).

One phase per session. A session: read this plan and the ADR, implement the one
phase, verify, commit, stop at the phase boundary. Do not bleed into the next
phase; do not "improve" adjacent code. Every phase closes with:

1. `uv run ruff check . && uv run ruff format . && uv run basedpyright` and the
   phase's tests (`uv run pytest <paths>`).
2. `uv run --locked scripts/preflight.py` — the full battery (spins its own
   throwaway postgres on :55432; needs Docker). No phase skips preflight; a
   phase is not done until this passes.
3. Commits per repo discipline: prose and code separate; regenerated artifacts
   in dedicated canonical commits carrying exactly `Run generate-clients`,
   `Run generate-datamodels`, `Run generate-clients and generate-datamodels`,
   or `Run generate-score` — no body, no trailers, no reference to the source
   change. One subject line under 72 characters on every commit.

Preflight's `generate-clients --check` makes client staleness a hard error, and
CI's build-docker getter runs `generate-score --check` against a clean checkout
— which is why regens land inside phases, never once at the end:

- **Score regens run from a clean clone of the branch tip.** This checkout
  carries ignored dirt under the `.dockerignore` allowlist and dirt hashes: a
  regeneration from the working tree mints tags only this machine can
  reproduce, and CI's `generate-score --check` fails against them. The order
  is: commit the source change, then `git clone --branch gpu-orchestration .
  /tmp/clean && cd /tmp/clean` (a fresh directory), run
  `uv run boatyard generate-score` there, copy `stack/generated/**` back, and
  commit the artifacts as the canonical `Run generate-score` commit. A
  regeneration from the dirty tree is for local `up` only.
- **Client regens may target the changed project.**
  `uv run generate-clients --config openapi-client-codegen.yaml --project
  workloads/<service>` regenerates only that service's clients (the config
  lives at the repo root; the lease-server client is
  `packages/generated/python/lease-server-client`, consumed only by the
  reconstructor, the api's by python/C#/TypeScript consumers). Run
  `uv sync --all-packages` then `uv run lock-python` first whenever any
  `pyproject.toml` changed; targeted regens avoid the localizer spec dump and
  its PyTorch requirement.
- **Image rebuilds are targeted.** `uv run boatyard build --targets <service>`
  after any change inside a service's build context — the no-targets form
  mints a divergent tag set that `up`'s working-tree hashes refuse (the
  predecessor plan's phase 5 lesson). On the GPU sandbox use
  `uv run boatyard up --quiet-pull` and generous timeouts.

This plan lives at the repo root beside the ADR until closeout. Moving either
under `design/` is the operator's call at closeout and requires an open Linear
ticket linking the blob (the `design/AGENTS.md` no-orphan rule) — an execution
session does not move them on its own initiative.

## External dependencies

- **Reconstructor checkpoint/resume (declared external dependency, not a
  phase).** Preemptible resumable reconstruction jobs — checkpoint on SIGTERM,
  resume on next start — are an independently planned feature. The Q4 policy
  and the converger are correct without it: preemption then costs a
  requeue-and-restart (exactly the shipped v1 behavior — the reconstructor's
  SIGTERM requeue), strictly-bounded degradation capped by the idle window.
  Nothing in the orchestrator changes when it lands. Interface contract handed
  to that feature:
  1. A checkpointed, paused job presents as claimable resumable work in
     `GET /queue-state`, counting in `queued` (nothing holds its lease while
     paused).
  2. The orchestrator stops the reconstructor with an explicit stop timeout
     (~60 s placeholder) — docker's 10 s default SIGKILLs mid-checkpoint, so
     the checkpoint must fit the negotiated budget. The orchestrator side of
     this contract is baked in this plan's rewrite phase (phase 3), so the
     feature landing changes nothing orchestrator-side.
  3. With it landed, localization-wins is hardwired behavior with no knob (S3,
     S11): preempting a reconstruction costs a checkpoint cycle, not minutes of
     redone SfM.
- **Capture-tool handoff (cross-repo, external, not blocking).** The capture
  tool (placeframe-capture-tool) removes its mode UI and any
  `gpu_mode_managed` read — removal, not replacement. The `/server-info` field
  is dropped on this unmerged branch before any release, so no released client
  ever reads it; the field's absence is itself the capability-off signal. The
  client contract is purely the API plus the 503/`Retry-After` behavior.

## End state

Once the last phase lands, all of the following hold. Each item cites the
phase that delivers it.

- The service is named `gpu-orchestrator` everywhere — directory
  (`workloads/gpu-orchestrator/`), package (`gpu_orchestrator`), compose
  service, image — while the score resource type stays `localizer-router`
  (provisioner filenames unchanged). [1]
- The lease-server answers `GET /queue-state` with `{queued: int, in_flight:
  int}` — a dumb attribute read; the demand predicate (`queued > 0 OR
  in_flight > 0`) is computed orchestrator-side. The generated lease client
  carries the endpoint (the reconstructor is its consumer). [2]
- The orchestrator hardcodes its managed set: `localizer` and
  `reconstructor` are constants in its code, matched at runtime by the
  automatic `com.docker.compose.service` label (the v1 switcher's proven
  plumbing). No `GPU_MANAGED_SERVICES` env, no class symbols, no
  annotation transport — config that can only be changed by also changing
  code is indirection, not config (ADR Q2's final form). [3]
- The orchestrator is a reconcile loop: one background task, pure desired-state
  function (Q4 semantics under `GPU_CONTENDED`, both-run otherwise), converger
  actuation via the Docker SDK, boot repair as the first tick, poke via
  asyncio event (never load-bearing), queue-state polled on
  `GPU_POLL_INTERVAL_S` via plain httpx with hold-last-sample on failure, and
  the demand-hint log line once per rising edge under contention. [3]
- Its surface is `GET /localizer-address` (address plus
  `retry_after_seconds` on the null answer), `GET /state` (state report +
  healthcheck, `last_pass_at`, open object), and `PATCH
  /policy` (the two timers, floors window ≥ 60 s / poll ≥ 5 s, 400 below,
  old→new logged). `GET /mode` and `POST /mode` are deleted; nothing about
  the orchestrator is reachable through the gateway — the `/gpu-mode/*`
  route is gone. [3]
- The operator surface is the loopback publish (boatyard.yml root config
  `ports:` record, host 127.0.0.1:5687 → target 8000, committed artifact
  port-free) and `uv run gpu-policy {status|set}`; `uv run gpu-mode` is
  retired. [3]
- The API renames `GPU_MODE_MANAGED` → `LOCALIZER_ROUTER_MANAGED` atomically
  across score files, api settings, and the k8s generation test; drops
  `gpu_mode_managed` from `/server-info` (one api client regen); and the null
  address 503 carries `Retry-After` echoed from the orchestrator —
  `placeframe_common`'s shared exception handler forwards `extra_headers`
  (it drops them today). [3]
- The values grammar gains `GPU_CONTENDED` (default "true"), `GPU_IDLE_WINDOW_S`
  (600), `GPU_POLL_INTERVAL_S` (15), `GPU_RETRY_AFTER_SECONDS` (60). [3]
- Every behavior above is verified live on the GPU sandbox: boot under default
  contention, demand-driven swap both directions, 503+Retry-After mid-transition,
  idle-window semantics both ways, live tuning + floor rejection +
  evaporate-on-restart, both-run at `GPU_CONTENDED: false`, drift repair, the
  hint line, loopback reachability/refusal, and no `/gpu-mode/*` at the edge. [4]
- Hardened truth is folded into the co-located `AGENTS.md` files; the ADR's
  status marks execution complete. [4]

## Phases

### 1. Rename mode-switcher → gpu-orchestrator (pure rename, zero behavior change) — complete

A pure rename before the rewrite keeps the rewrite diff free of move noise.
`/mode` (GET and POST), the `/gpu-mode/*` route, the `gpu-mode` verb, and
`GPU_MODE_MANAGED` all stay alive and untouched this phase — the stack must
behave identically before and after.

- `git mv workloads/mode-switcher workloads/gpu-orchestrator`; inside it
  `git mv src/mode_switcher src/gpu_orchestrator` and
  `tests/test_mode_switcher.py tests/test_gpu_orchestrator.py`. Update every
  internal spelling: package imports in tests, the `configure_logging` service
  name, the OpenAPI title/servers (`Placeframe GPU Orchestrator`,
  `http://gpu-orchestrator:8000`).
- `workloads/gpu-orchestrator/pyproject.toml` — name
  `placeframe-gpu-orchestrator`, description, hatch package
  `src/gpu_orchestrator`.
- `workloads/gpu-orchestrator/Dockerfile` — `WORKDIR` and all
  `workloads/mode-switcher` path spellings (the three `COPY` lines, the
  dev-stage `-e` targets); `entrypoint.sh` — the `cd` path, the
  uvicorn target `gpu_orchestrator.main:app`, the reload dir, and the debug
  toggles `DEBUG_MODE_SWITCHER`/`DEBUG_WAIT_MODE_SWITCHER` →
  `DEBUG_GPU_ORCHESTRATOR`/`DEBUG_WAIT_GPU_ORCHESTRATOR`.
- Root `pyproject.toml` — `[tool.uv.workspace].members` entry and the pytest
  `testpaths` entry both repoint to `workloads/gpu-orchestrator`. Then
  `uv sync --all-packages && uv run lock-python`; the lock files ride this
  phase's code commit (they are not canonical-codegen artifacts).
- `stack/score/compose/localizer-router.yaml` — the service key and image
  `dockerfile:` path become `gpu-orchestrator`; `outputs.address` becomes
  `http://gpu-orchestrator:8000`. The file's own name, the resource type, the
  `/gpu-mode/*` route claim, the `/mode` healthcheck, and the k8s twin are
  untouched (the k8s twin references no mode-switcher spelling today).
- `scripts/tests/test_score_compose_generation.py` — `CORE_SERVICES` and the
  scoped bind assertion rename `mode-switcher` → `gpu-orchestrator`; the
  mode-switcher test function renames with its assertions unchanged in
  substance (route, port annotation, `LOCALIZER_URL`, bind, barrier gate).
- `stack/score/localizer.yaml` and `stack/score/reconstructor.yaml` — the
  autostart annotation comments still say "let the mode switcher start it";
  reword to name the gpu-orchestrator (comment-only, both files).
- Regen: `uv run boatyard generate-score` from a clean clone of the branch
  tip. The artifact diff is the service rename, the image stem, and the tag
  slot (`..._MODE_SWITCHER_SHA` → `..._GPU_ORCHESTRATOR_SHA`). Canonical
  `Run generate-score`.
- Prose commit (name-level edits only; semantic rewrites are phase 4):
  `workloads/gpu-orchestrator/AGENTS.md` (moved with the directory),
  `workloads/AGENTS.md` (service-table row, data-flow diagram),
  `stack/AGENTS.md` (the scoped-bind and localizer-router bullets that name
  the service), `scripts/AGENTS.md` (the `gpu-mode` row's target name).

Verification: battery + preflight; targeted tests
`uv run pytest workloads/gpu-orchestrator/tests scripts/tests/test_score_compose_generation.py`.
Manual smoke (the rename's failure mode — a missed DNS/image reference — is
exactly what static checks miss): `uv run boatyard build --targets
gpu-orchestrator`, `uv run boatyard up --quiet-pull`, then `curl
localhost:8443/gpu-mode/mode` → `{"mode":"localizer"}` (v1's mode values
are the compose service names) and one
`uv run gpu-mode reconstructor` / toggle-back cycle.

Commits: code commit (rename sweep), canonical `Run generate-score`, prose
commit (name-level doc updates).

### 2. Lease-server queue-state endpoint — complete

`GET /queue-state` on the lease-server (S6): two integer counts, a dumb
attribute read — no policy inside the endpoint.

- `workloads/lease-server/src/routers/queue_state.py` (new) — a `GET
  /queue-state` handler returning `QueueState{queued: int, in_flight: int}`,
  following the `leases.py` session-dependency pattern.
  `queued` counts rows at `status == QUEUED`; `in_flight` counts rows at any
  non-terminal, non-queued status (the active-lease population — the same
  classification the stale-lease reaper's filter encodes at
  `workloads/lease-server/src/routers/leases.py:54-62`). Counts via
  `select(func.count())`.
- `workloads/lease-server/src/main.py` — mount the new router beside the
  leases router.
- `workloads/lease-server/tests/test_queue_state.py` (new) — the handler
  against a stubbed `AsyncSession` (count queries, zero-state); root
  `pyproject.toml` `testpaths` gains `workloads/lease-server/tests` (the
  s3-initializer/mode-switcher precedent).
- Regen: `uv run generate-clients --config openapi-client-codegen.yaml
  --project workloads/lease-server` — the generated
  `packages/generated/python/lease-server-client` gains the endpoint and
  `workloads/lease-server/openapi.json` refreshes. Canonical
  `Run generate-clients`. No score regen (compose slots re-stale nothing on
  source changes inside a build context).

Verification: battery + preflight; targeted `uv run pytest
workloads/lease-server/tests`. Manual: `uv run boatyard build --targets
lease-server`, `up`, then probe in-container — the lease-server's HTTP port
is compose-internal, and its only host publish targets the debugpy listener
(`boatyard.yml`'s 5683→5678, DEBUG-gated), so the host cannot curl the
endpoint:
`docker exec placeframe-lease-server-1 python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/queue-state').read())"`
→ `{"queued":0,"in_flight":0}`; queue a rerun via the
`workloads/AGENTS.md` rerun SQL and watch `queued` flip.

Commits: code commit, canonical `Run generate-clients`.

### 3. Orchestrator rewrite + atomic mode-surface removal — complete

The demand-driven core lands and every mode surface dies in the same phase —
killing `POST /mode` breaks the route, the verb, and the healthcheck at once,
so they move together or not at all.

The orchestrator package (`workloads/gpu-orchestrator/src/gpu_orchestrator/`)
grows from one module into:

- `settings.py` — pydantic-settings: `gpu_contended` (env `GPU_CONTENDED`,
  default true), `idle_window_s` (`GPU_IDLE_WINDOW_S`, 600),
  `poll_interval_s` (`GPU_POLL_INTERVAL_S`, 15), `retry_after_s`
  (`GPU_RETRY_AFTER_SECONDS`, 60), `lease_server_url`,
  `localizer_url`. Boot
  values below the floors clamp to the floor with an Error log (window ≥ 60,
  poll ≥ 5; Q5 — a bad timer must not brick the GPU, Q8).
- `policy.py` — the pure desired-state function, the unit-test surface.
  Inputs: `gpu_contended`, localization-demand activity (a heartbeat within
  the idle window), queue counts, the managed set. Q4 truth table:
  contended → localizer iff localization demand active, else reconstructor
  iff `queued > 0 OR in_flight > 0`, else localizer (warm front door);
  uncontended → all managed (S2 — the no-op is emergent, drift repair still
  runs). Localization always wins, hardwired (S3).
- the loop — one `while True` background task started at boot (the
  `on_startup` hook): gather inputs (heartbeat clock, latest queue sample,
  capacity, container states), compute desired, converge the diff. Boot
  repair is the first tick — `initialize()`'s separate repair path
  dissolves. The wait between passes is an `asyncio.Event` with timeout at
  the poll interval. The queue-state poll runs on `GPU_POLL_INTERVAL_S` via
  plain `httpx` (S6 — not the generated lease client; the api's
  router-query seam in `localizer_router.py` is the precedent); poll failure
  holds the last successful sample with an Info log. Poke-triggered passes
  reuse the cached sample — pokes are never load-bearing. Under contention,
  held-out demand logs the one-line hint naming `GPU_CONTENDED` once per
  rising edge. `last_pass_at` updates every pass.
- the converger — Docker SDK actuation. The managed pair is hardcoded:
  `localizer` and `reconstructor` constants, containers matched by the
  automatic `com.docker.compose.service` label within the compose project
  discovered from the orchestrator's own container labels (both the v1
  mechanism, unchanged). The localizer carries the interactive behaviors
  (heartbeat-mapped demand, preemption, warm rest, ~700 ms drain before
  stop); the reconstructor the batch behaviors (queue-mapped demand,
  immediate stop with the lease requeue absorbing it).
  Transitions serialize and run to completion inside their pass; a pass that
  finds a transition in flight skips actuation. Transition semantics carry
  from the predecessor ADR Q2: drain ~700 ms before stopping the
  interactive class; the batch class stops with an explicit
  `stop(timeout=60)` — the S11 contract (b) side, baked now so the
  checkpoint/resume feature changes nothing orchestrator-side.
- the HTTP surface — `GET /localizer-address` → `{address: str | null,
  retry_after_seconds: int}` (the field is meaningful —
  `GPU_RETRY_AFTER_SECONDS` — on the null answer, 0 otherwise); it records
  the heartbeat, sets the poke event, and answers from interactive-container
  state (S5: reserved to the API's localize path; nothing else may poll it).
  `GET /state` → open object: running set, managed set, both demand signals'
  activity, `queued`/`in_flight` (the cached sample), `gpu_contended`,
  `idle_window_seconds`, `poll_interval_seconds`, `last_pass_at` —
  and it is the healthcheck. `PATCH /policy` →
  `{idle_window_seconds?, poll_interval_seconds?}`, floors enforced (400
  below), every mutation logged old→new (S9/Q5: in-memory only, values is
  truth at boot; contention is values-only — `status` reports it, `set`
  cannot touch it). `GET /mode` and `POST /mode` are deleted.
- tests — the package's tests are rewritten against fakes: policy fixtures
  under a fake clock (the Q4 truth table plus window expiry),
  poke-passes-reuse-the-sample, poll-failure-holds-sample, boot clamping,
  PATCH floor 400s, hint rising-edge-once, converger ordering (drain before
  interactive stop, `timeout=60` on batch stop), transition serialization,
  and the `/localizer-address` null/non-null contract.
- `workloads/gpu-orchestrator/pyproject.toml` — add `httpx` (the
  queue-state poll's import; transitive-only today, declared per the
  imports-match-dependencies rule). Then `uv sync --all-packages && uv run
  lock-python`; lock files ride the code commit.

Around it, the mode vocabulary dies everywhere:

- `stack/score/compose/localizer-router.yaml` — the service's `route:`/`port:`
  claim is deleted (zero gateway surface, Q7); the healthcheck probes
  `/state`; `environment:` gains `LEASE_SERVER_URL` (templated from a
  `lease_server_spec: include-yaml: stack/score/lease-server.yaml` state
  entry — the `LOCALIZER_URL` no-copied-port pattern) and the four values
  slots `${GPU_CONTENDED:-true}`, `${GPU_IDLE_WINDOW_S:-600}`,
  `${GPU_POLL_INTERVAL_S:-15}`, `${GPU_RETRY_AFTER_SECONDS:-60}` (the
  seaweedfs `${VAR:-default}` precedent).
- `boatyard.yml` — the `core` group's `ports:` list gains `{service:
  gpu-orchestrator, host_ip: 127.0.0.1, published: 5687, target: 8000}` (the
  api/lease-server debug-port precedent; materialized at `up`, the committed
  artifact stays port-free, the zero-published-ports test invariant stands).
- `boatyard.values.sample.yml` — document the four optional `GPU_*` keys with
  their defaults in the flat ALL_CAPS values list.
- `stack/score/api.yaml` — `GPU_MODE_MANAGED` → `LOCALIZER_ROUTER_MANAGED`
  (atomic rename with the code below).
- `workloads/api/src/settings.py` — `gpu_mode_managed` →
  `localizer_router_managed` (env `LOCALIZER_ROUTER_MANAGED`).
- `workloads/api/src/routers/server_info.py` — drop the `gpu_mode_managed`
  field from `ServerInfo` and both return paths (unmerged branch, no released
  reader; the absence is the capability-off signal).
- `workloads/api/src/routers/localizer_router.py` — the branch follows the
  renamed setting; the response model gains `retry_after_seconds`; the null
  path raises the 503 with `extra_headers={"Retry-After": str(seconds)}`.
- `packages/python/common/src/placeframe_common/litestar.py` —
  `log_http_exception` (lines 43-67) builds its own `Response` in both
  branches and **drops `exception.extra_headers` today**; fix it to forward
  them (`Response(..., headers=exception.extra_headers)`), leaving the ≥500
  detail masking unchanged (the status code is the wire contract). Test in
  `packages/python/common/tests/`: a 503 raised with `extra_headers` through
  the Litestar TestClient carries the header.
- api tests — `test_settings.py` (env rename), `test_server_info.py` (field
  drop), `test_localization_router.py` (rename plus new assertions: null +
  `retry_after_seconds` ⇒ 503 with the `Retry-After` header; non-null ⇒ no
  header).
- `scripts/src/scripts/gpu_policy.py` (new) — typer app (`:app` entry point):
  `status` pretty-prints `GET /state`; `set --idle-window/--poll-interval`
  accepts duration spellings (`30m`, `45s`, bare = seconds), normalizes to
  int seconds, PATCHes `/policy`. Base URL defaults to
  `http://127.0.0.1:5687`, overridable via `GPU_ORCHESTRATOR_URL`.
  `scripts/src/scripts/gpu_mode.py` and `scripts/tests/test_gpu_mode.py` are
  deleted; `scripts/tests/test_gpu_policy.py` lands (duration
  normalization, PATCH payload, non-zero exit on unreachable orchestrator);
  `scripts/pyproject.toml` swaps the entry points (`gpu-policy` in,
  `gpu-mode` out); `scripts/AGENTS.md` table row (prose commit).
- `scripts/tests/test_score_compose_generation.py` — the orchestrator test
  asserts: no `boatyard/route` annotation, the four `GPU_*` env slots, the
  `LEASE_SERVER_URL` derivation, the `/state` healthcheck (bind + barrier
  assertions unchanged). `scripts/tests/test_score_k8s_generation.py:53` —
  `GPU_MODE_MANAGED` → `LOCALIZER_ROUTER_MANAGED`.
- Regens: clean-clone `Run generate-score` (provisioner rewrite + api env
  rename); `uv run generate-clients --config openapi-client-codegen.yaml
  --project workloads/api` for the `ServerInfo` drop → canonical
  `Run generate-clients` (python, C#, TypeScript).

Verification: battery + preflight; targeted tests (`uv run pytest
workloads/gpu-orchestrator/tests workloads/api/tests
packages/python/common/tests scripts/tests`). Manual smoke (the full battery
is phase 4): `uv run boatyard build --targets 'api localizer lease-server
reconstructor database-manager gpu-orchestrator'` (all six images whose
build context consumes the changed `placeframe-common`
— missing one leaves its tree tag unbuilt and `up` fails image-not-found —
plus the orchestrator), `up`, then **recreate the gateway** — the known
compose limitation: the caddy gateway does not recreate on
configs-content-only change, so route removal needs it (`docker rm -f` the
`boatyard-gateway` container, then `uv run boatyard up --quiet-pull`); smoke
`curl 127.0.0.1:5687/state`, `curl localhost:8443/gpu-mode/mode` → 404, and
one localize request → 200 or 503-with-`Retry-After`.

Commits: code commits (orchestrator rewrite; api + common + score + config +
scripts), canonical `Run generate-score`, canonical `Run generate-clients`,
prose commit (`scripts/AGENTS.md`).

### 4. Live acceptance, docs promotion, closeout — complete

The full acceptance battery on the GPU sandbox, then the docs fold and the
closeout. No new mechanism lands.

Acceptance — in order, each with the orchestrator's logs alongside
(`docker logs` / `uv run loki-query`):

1. **Boot under default contention.** With values at defaults
   (`GPU_CONTENDED` unset ⇒ true), `uv run boatyard up --quiet-pull`:
   both GPU containers created, exactly one running — the localizer,
   started by the orchestrator's first tick, not by `up`.
2. **Shrink the window first.** `uv run gpu-policy set --idle-window 60s` —
   the 600 s default makes transition observation slow; every following step
   assumes the floor.
3. **Batch demand swaps to reconstruction.** Queue work via the
   `workloads/AGENTS.md` rerun SQL; within ~a poll interval the
   reconstructor starts and the localizer stops.
4. **Localization wins.** With reconstruction running, issue localize
   traffic (`curl .../localize/version` through the gateway): the
   reconstructor stops (requeue-and-restart — the bounded degradation until
   checkpoint/resume lands) and the localizer starts.
5. **503 + Retry-After mid-transition.** Fire `/localize/version` during the
   swap window: 503 with a `Retry-After` header echoing
   `GPU_RETRY_AFTER_SECONDS`.
6. **Idle-window semantics both ways.** (a) Localizer running, no
   localization traffic for the window, queued work present ⇒ swaps to the
   reconstructor. (b) `in_flight > 0` keeps the reconstructor running past
   the window; when the queue drains and nothing is in flight, the resting
   state (localizer) returns.
7. **Live tuning, floors, evaporation.** `gpu-policy set --idle-window 30s`
   ⇒ 400 (floor 60); `--poll-interval 1s` ⇒ 400 (floor 5); valid sets ⇒ 200
   with old→new in the logs; restart the orchestrator container ⇒ `/state`
   shows the values-file values again (overrides die at restart).
8. **Both-run.** Set `GPU_CONTENDED: "false"` in `boatyard.values.yaml`,
   `up`: both GPU containers run; localize and reconstruct simultaneously.
9. **Drift repair.** `docker stop` the running GPU container: a later tick
    restarts it (S2 — repair runs in both contention modes).
10. **Restore contention.** Remove `GPU_CONTENDED` from
    `boatyard.values.yaml` (or set `"true"`), `uv run boatyard up
    --quiet-pull`, and wait for the swap back to exactly one running GPU
    container — step 8 left the stack in both-run mode, and the hint test
    requires arbitration active.
11. **The hint.** Under contention with localization traffic kept alive,
    queue reconstruction work: the held-out-demand hint naming
    `GPU_CONTENDED` logs exactly once per rising edge (grep it; assert no
    per-tick spam).
12. **Loopback.** `curl 127.0.0.1:5687/state` answers from the host;
    the same request against the host's LAN address is refused.
13. **No mode route.** `curl localhost:8443/gpu-mode/mode` → 404 at the
    edge.

Docs promotion (prose commits; fold hardened truth, delete what died):

- `stack/AGENTS.md` — the orchestrator as the
  compose-only emitted service (renamed bullets), the loopback `ports:`
  record, the zero-gateway-surface posture, the demand-driven selective-start
  behavior; the Cross-workload URLs constraint bullet's `GPU_MODE_MANAGED`
  mention renames to `LOCALIZER_ROUTER_MANAGED`, and the gateway paragraph's
  mode-switcher route claim is deleted with the route.
- `workloads/AGENTS.md` — the orchestrator row and the data-flow diagram's
  demand-driven localization step (queue seam + router seam), the 503 +
  `Retry-After` failure mode.
- `workloads/gpu-orchestrator/AGENTS.md` — rewritten for the loop, policy,
  endpoints, hardcoded managed pair, values knobs, loopback surface (the phase 1
  rename left it v1-shaped).
- Root `AGENTS.md` — the server-stack paragraph still says "there is no
  separate orchestrator service"; it predates even the mode switcher —
  bring it to present truth.
- ADR status (`demand-driven-orchestration.md`) — mark execution complete;
  the ADR stops being load-bearing; repoint its `See also` link to
  `workloads/gpu-orchestrator/AGENTS.md` (phase 1's rename broke the
  mode-switcher path). Moving the ADR and this plan under
  `design/` is the operator's call, requires an open Linear ticket per the
  no-orphan rule, and happens only on that direction.

Verification: the battery + a final full preflight. Prose-only beyond the
acceptance run; no regen.

Commits: prose commit(s). If the acceptance run surfaces code defects, the
fixes are code commits in this phase, each closing with the full battery +
preflight before the prose lands.

## Regens at a glance

| Phase | Regen | Canonical commit |
|---|---|---|
| 1 | score artifacts (service rename, image stem, tag slot) | `Run generate-score` |
| 2 | lease-server client + `openapi.json` (`/queue-state`) | `Run generate-clients` |
| 3 | score artifacts (provisioner rewrite, api env rename) + api clients (`ServerInfo` drop) | `Run generate-score`, `Run generate-clients` |
| 4 | — (prose-only closeout) | — |
