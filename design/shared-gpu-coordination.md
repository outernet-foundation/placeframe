---
updated: 2026-10-30
---

# Shared-GPU coordination — localizer / reconstructor mutual exclusion

Design for single-GPU hosts (desktops, air-gap LAN boxes) where the localizer
and reconstructor share one GPU and cannot both hold VRAM. Pre-implementation;
nothing here is built. Code references describe the tree as of 2026-10-30
(branch `compose-bundles`, `6d867c4f`) and will drift.

## Status and session protocol

This document is the entry point for a fixed sequence of sessions. A session
that opens by reading this doc must check this section first.

1. **Decision session (next).** First point of order: close **all six** open
   questions in [Open questions](#open-questions) with the operator. Record
   each decision in place (fill the `Decision:` line), update the frontmatter
   date, and commit. When all six are closed, this document **is** the
   finished ADR. Close the session — do not proceed to planning in it.
2. **Plan session.** Turn the ADR into a plan document in `design/` (phased
   implementation units, per-unit verification, codegen/regen sequencing).
   Close the session — do not begin implementation in it.
3. **Execution session(s).** Execute the plan. On completion, fold whatever
   hardened into the co-located `AGENTS.md` files per `design/AGENTS.md`
   promotion conventions; this note then stops being load-bearing.

Do not reorder the sequence. Each session ends deliberately.

## Problem

On a single-GPU host the localizer's resident models (DIR + ALIKED + LightGlue)
and the reconstructor's pipeline (same three models batched + FAISS + pycolmap
BA) cannot coexist in VRAM. Today this fails silently and obtusely:

- The localizer loads models at module import and holds VRAM for the
  container's lifetime (`workloads/localizer/src/main.py:59-66`,
  `workloads/localizer/src/localize.py:57`). Nothing ever stops it — the
  container has no shutdown hook, and even with zero clients it keeps
  squatting VRAM.
- A reconstruction started while the localizer is resident OOMs inside the
  pipeline and lands as a `FAILED` row with a CUDA traceback buried in
  `docker logs`.
- A localization attempted while a reconstruction is running surfaces as an
  opaque `502 Localization session backend error` — the API proxy collapses
  every non-422 localizer failure into that generic 502
  (`workloads/api/src/routers/localization.py:109-113`).
- The standing operator workaround — stop the localizer container, run the
  reconstruction, restart it — is manual, slow, and its failure mode is the
  silent one above.

The reconstructor also holds all three models from startup onward while
idle-polling (`workloads/reconstructor/src/reconstructor/main.py:128`), so an
*idle* reconstructor taxes VRAM too.

## Non-goals and rejected alternatives

- **No preemption.** Automatically evicting the localizer when a
  reconstruction is queued breaks an active AR session's tracking — worst UX
  of any option. The human is the preemption mechanism, surfaced legibly.
  (An explicit *manual* yield control is open question 1.)
- **`docker pause` / cgroup freezer** — freezes processes, releases no VRAM.
- **MIG partitioning** — data-center GPUs only; not desktops.
- **CUDA MPS** — shares a context, enforces no memory cap.
- **cgroup / device-plugin VRAM limits** — no enforceable VRAM limit exists
  for compose desktops; `nvidia.com/gpu` counts devices, not bytes.
- **Localizer on CPU** — ~700 ms/query becomes multi-second; kills AR use.
- **Two services polling each other (no single mutex owner)** — check-then-act
  races: localizer checks "no claimed row" → reconstructor claims in the gap →
  both allocate → the silent OOM returns, now rare instead of routine. A rare
  race that resurrects the failure discredits the feature. Rejected.

## Design

### The keystone

"GPU busy because a reconstruction is running" is not new state — it is
`EXISTS (claimed reconstruction row)`, which the lease-server already owns
(the row's status column *is* the lease; 30-min reaper at
`workloads/lease-server/src/routers/leases.py:21`). The only missing fact is
"localizer holds VRAM". Add one thing — a **localization session** — and the
GPU becomes a leased resource with the same Postgres-backed TTL-and-reaper
discipline the reconstruction queue already has.

### Mechanism

- **Localization session**: a single small row (holder, `expires_at`) in the
  lease-server's Postgres. Acquired *before* models load; heartbeat-renewed
  while loaded; released *after* models unload; TTL-reaped if the localizer
  dies. **Invariant: session exists ⟺ localizer holds or is acquiring VRAM.**
- **Grant gate inside `request_lease`**: the grant transaction refuses while a
  live session exists, and returns a *third* response — "GPU busy: localizer
  session active" — distinct from 404-no-work, so the reconstructor (and
  operators) can distinguish idle from blocked. Because the gate lives inside
  the grant, the reconstructor structurally cannot claim a lease it cannot
  run (no stuck-claimed-rows until the 30-min reaper).
- **Session acquire refuses while any row is claimed.** Both refusals execute
  in lease-server transactions over the same tables, so mutual exclusion is
  serialized by row locks. Single owner, real compare-and-swap, no races.
- **Localizer lifecycle** (shared mode):
  - Boot: load models as today, acquire session at boot (stack comes up
    ready to localize; no cold first request).
  - Idle: no `/localization` requests for N minutes ⇒ unload models
    (`del` globals, `gc.collect()`, `torch.cuda.empty_cache()`), release
    session. Weights are baked into the image (`neural-networks-base`
    preload, `TORCH_HOME`), so reload is disk-local seconds. Idle is measured
    on `/localization` only — the 5 s compose healthcheck pings `/version`
    (`stack/generated/compose/compose.cuda.yaml:182-191`) and must never
    count as activity; the container stays "healthy" while unloaded.
  - Demand: a request arriving while unloaded acquires the session, loads
    inline (~seconds, single uvicorn worker ⇒ requests serialize; no
    half-states), serves. If acquisition is refused ⇒ structured 503.
  - Refusal body is typed schema: `code=gpu_busy_reconstruction_active`,
  active reconstruction id, phase, progress fraction, `retryable: true`.
    The lease-server already has phase/progress — the 503 is rich for free.
- **Reconstructor lifecycle**: models load per-job (after grant) and unload
  **before** the terminal `succeed`/`fail` PUT — the terminal PUT releases
  the lock, so unload-first closes the last overlap window. This is a
  *correctness requirement*, not politeness: the "GPU free ⟺ no claimed row
  AND no live session" derivation requires the reconstructor to hold zero
  VRAM while lease-less (today's idle-resident models at `main.py:128` would
  break the invariant). SIGTERM's `os._exit(0)` is safe — process death
  frees CUDA memory near-instantly and the lease is requeued first.
- **Client surfacing**:
  - API localize proxy recognizes the typed 503 and passes it through
    (instead of the 502 collapse at `localization.py:109-113`); python + C#
    clients regenerate against the localizer OpenAPI change.
  - Reconstruction status gains a derived `blocked_by: localizer_active`
    (queued row + live session) so the capture tool can render
    "VRAM in use — stop localizing to unblock". Message wording is open
    question 5.
- **Gating**: lease-server URL present in the localizer's env selects shared
  mode (presence-selected, mirroring `AUTH_ISSUER_URL`); absent ⇒ boot-load
  and hold forever, exactly today's behavior, no lease-server dependency.
  Kubernetes never wires it (dedicated GPU nodes; a session row would wrongly
  gate a fleet; KEDA scale-to-zero makes per-job load moot there anyway).

### State sketch

```
localizer:   UNLOADED ──acquire ok──► LOADED ──idle / yield──► UNLOADED
                 │  ▲                     │
                 │  └ refused while       └ renewal failure past grace ⇒ unload
                 │    any row claimed
                 ▼
          503 gpu_busy_reconstruction_active

reconstructor: idle-poll ──grant (only while no live session)──► running
               running ──unload models──► terminal PUT ──► idle-poll
```

### Failure-mode policy

- **Lease-server unreachable at localizer boot** ⇒ loud refusal to serve.
  Never silently fall back to exclusive mode.
- **Heartbeat renewal fails past a grace period** (lease-server outage
  mid-session) ⇒ localizer unloads. Holding VRAM on an expired session is
  the one state that resurrects the OOM race; fail safe to the mutex.
- **Dead localizer** ⇒ no heartbeats ⇒ session TTL-reaped ⇒ reconstructions
  unblock. Same reaper pattern as leases.

## Locked defaults

Decided in design discussion; reopen only with cause.

- Boot-load + acquire-at-boot (not lazy-from-first-request).
- Idle clock counts `/localization` requests only; healthchecks excluded.
- Fail-safe unload on renewal failure; loud refusal when the coordinator is
  unreachable at boot.
- Reconstructor per-job load/unload applies in **all** modes (uniform code).
- Session TTL 60 s, heartbeat 15 s, renewal grace ~3 heartbeats — mechanical,
  tunable later.
- `_maps` cache (CPU-side numpy/pycolmap/faiss — descriptors copy to GPU per
  request at `workloads/localizer/src/localize.py:114`) survives unload
  cycles; only model weights load/unload.

## Open questions

Six decisions for the operator. The decision session closes all six, fills
the `Decision:` lines, and this doc becomes the ADR.

### 1. Deadlock escape — and is multi-user contention in scope?

Localizer active + reconstruction queued is a deadlock whose only escapes are
the idle timeout or a human stopping. Single-user desktop: "stop localizing"
works. Anonymous-LAN: *anyone's* app can be the localizer; the capture-tool
operator can't make another person stop.

- (a) Single-user only; the blocked message says "stop localizing" and that
  is the whole story.
- (b) Ship an explicit operator escape — a `uv run localizer yield` verb or
  admin control that manually unloads. Preemption exists, but only as a
  deliberate human act, never automatic.
- (c) Scope to compose/desktop now; LAN multi-user explicitly out of scope
  for this feature.

Decision:

### 2. Idle-unload policy — always, or only under contention?

- (a) *Always* — after N idle minutes the localizer releases VRAM even with
  nothing queued (desktop citizenship; the GPU is free for anything else;
  cost = seconds reload on next use).
- (b) *Only while a reconstruction is queued* — zero thrash when
  uncontended, fully invisible; but the localizer squats VRAM forever on an
  otherwise-idle machine.

Sub-fork: when work *is* queued, does the idle timeout shorten (5 min → 30 s
"expedited yield")?

Decision:

### 3. Queue continuity — batch-drain or strict alternation?

With multiple captures queued and job 1 finishing:

- (a) Reconstructor keeps the GPU until the queue drains (best throughput;
  localizer locked out for the batch — matches queue-and-walk-away).
- (b) Localizer gets a shot after every job (interleaves; but a localize
  burst between jobs re-blocks the queue and adds reload cycles).

Decision:

### 4. Wiring scope

- (a) Default-on for all compose core bundles (every compose host presumed
  shared-GPU).
- (b) Opt-in `shared-gpu` bundle option in `BUNDLES=`.

Confirm k8s is never. If (a): support `LOCALIZER_IDLE_TIMEOUT=0` =
never-unload as the LAN-server escape hatch?

Decision:

### 5. Client UX on refusal — retry or surface-and-stop?

- (a) SDK auto-retries with backoff (user sees nothing until the
  reconstruction ends — but AR tracking is silently dead the whole time).
- (b) Typed error surfaces immediately; the app decides (banner / freeze
  content / keep-last-pose).

Also: is poll-derived status good enough for the capture tool's blocked
state, or does it need to be live? Wording of both user-facing messages
belongs to the operator.

Decision:

### 6. Calibration coupling — accept the refit tax?

The localizer OpenAPI/boot changes bump `LOCALIZER_SHA`. Free while the
calibration is the placeholder sentinel; after the first real calibration,
*every* iteration on this feature pays a refit. Alternative is narrowing the
SHA scope to pipeline-affecting files only — contradicts the documented
"coarse hash on purpose" doctrine (env-var/path bypasses silently
invalidating calibration).

- (a) Accept the tax (bundle this feature's localizer changes with other
  refit-driving changes where possible).
- (b) Narrow the hash scope (doctrine change, needs its own justification).

Decision:

## Carrying costs

- The localizer gives up its dependency-free status in shared mode (gains
  `placeframe_lease_server_client` + a heartbeat task) — env-gated, so
  exclusive-mode deployments are unchanged.
- The lease-server grows ~3 endpoints (acquire/heartbeat-release, gpu-state)
  and the grant gate.
- Client regen cascade (python + C#) on the localizer OpenAPI change; the
  Unity SDK and capture-tool UI changes ride their own releases
  (placeframe-capture-tool repo for the app).
- One tuning knob (idle threshold) and one watch-metric (reloads/hour) once
  deployed.

## See also

- `workloads/lease-server/src/routers/leases.py` — the lease state machine
  this design extends.
- `workloads/localizer/AGENTS.md`, `workloads/reconstructor/AGENTS.md` —
  present truth for the two GPU services.
- `workloads/AGENTS.md` — stack data flow and the worker-pull architecture
  the session resource joins.
