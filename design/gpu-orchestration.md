---
updated: 2026-11-17
---

# GPU orchestration — mode switcher and localization router

Design for single-GPU hosts (desktops, air-gap LAN boxes) where the localizer
and reconstructor share one GPU and cannot both hold VRAM. Pre-implementation;
nothing here is built. Code references describe the tree as of 2026-11-16
and will drift.

Supersedes [`shared-gpu-coordination.md`](shared-gpu-coordination.md), which
explored a Postgres-backed mutual exclusion layer (gpu_sessions table, grant
gate, heartbeat, TTL reaper) bolted onto the lease-server. That approach was
rejected because it pollutes the lease-server with compose-specific dead code
on k8s and because the coordination machinery (heartbeat, idle timeout, yield,
typed errors) is heavyweight for a single-GPU deployment. See [Rejected
alternatives](#rejected-alternatives) for the full derivation.

## Status and session protocol

This document is the entry point for a fixed sequence of sessions. A session
that opens by reading this doc must check this section first.

1. **Design session (complete, 2026-11-16).** Identified the mode-switcher
   approach and the localization router abstraction. Open questions recorded
   below; none are closed.
2. **Open-questions session (complete, 2026-11-16).** Worked through each
   question in [Open questions](#open-questions), one at a time. Each carries
   a `Decision:` line. Q3 was revised mid-session after Q12 exposed a
   profiles-vs-selective-start tradeoff (profiles dropped in favor of
   boatyard `up` `--no-start` + selective start); Q5 was amended to name the
   `managed`-branch refinement from Q10. All twelve questions closed.
3. **Code-verification session (complete, 2026-11-16).** Verified the locked
   design against the current `dev` tree. No implementation gaps — every code
   reference matches the tree, and all pre-implementation artifacts are
   correctly absent. One external dependency was flagged for confirmation
   during execution: the pre-amendment Q3 (`boatyard/gpu: "true"` →
   `managed` as an annotation *value*) would have required boatyard's gpu
   device-reservation templates to recognize `managed`/`always` as
   GPU-carrying.    Q3's post-execution amendment dissolved that dependency —
   the templates are untouched and selective-start keys on a separate
   `boatyard/autostart` annotation.
4. **Plan session (complete, 2026-11-16).** The plan lives in
   [gpu-orchestration-plan.md](gpu-orchestration-plan.md).
 5. **Execution session(s).** One phase per session, per the plan's execution
    protocol. Phase 1 (boatyard) complete, 2026-11-17: branch `gpu-managed`
    off the released line (World A — the `boatyard/*` namespace kept), local
    at `4618681`, unpushed (the sandbox token cannot push; the operator
    pushes). Re-executed the same day on Q3's split-annotation amendment —
    the first pass made `managed` a gpu-annotation value and widened the
    template guards; the redo leaves the templates byte-identical to the
    released line and keys selective-start on a separate annotation,
    renamed once to the behavior-named `boatyard/autostart: "false"`
    ("managed" named a motivation boatyard cannot see). A
    pinned-compose-binary cache also landed on that branch —
    boatyard's preflight was re-downloading the ~32MB binary every run.
    Next: phase 2 (mode switcher workload), which runs against released
    boatyard per the plan.
6. **Promotion.** Fold hardened truth into co-located `AGENTS.md` files per
   `design/AGENTS.md` promotion conventions; this note stops being
   load-bearing.

Do not reorder the sequence. Each session ends deliberately.

## Problem

On a single-GPU host the localizer's resident models (DIR + ALIKED + LightGlue)
and the reconstructor's pipeline (same three models + FAISS + pycolmap BA)
cannot coexist in VRAM. Today this fails silently and obtusely:

- The localizer loads models at module import and holds VRAM for the
  container's lifetime (`workloads/localizer/src/main.py:62-68`). Nothing
  ever stops it.
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
idle-polling (`workloads/reconstructor/src/reconstructor/main.py:144`), so an
idle reconstructor taxes VRAM too.

## The reframe

The previous design treated the **GPU** as the contentious resource — both
containers run simultaneously and fight over VRAM, requiring a mutual
exclusion layer (table, grant gate, heartbeat, TTL) to prevent OOM.

This design treats the **GPU container slot** as the contentious resource.
Only one GPU container runs at a time. An external piece of infrastructure
(the mode switcher) decides which one. You cannot have an OOM race between
two containers if only one container is ever running.

The user explicitly chooses which mode to be in — "localization" or
"reconstruction" — via a simple toggle. No mutual exclusion mechanism, no
race, no coordination layer bolted onto existing services.

## Mechanism

### Mode switcher (compose-only)

A small, always-on container that exists only in the compose stack. Its job:

- Track the current mode: `localization` or `reconstruction`.
- Expose `GET /mode`, `POST /mode`, and `GET /localizer-address`.
- On mode switch: stop the current GPU container → wait for exit → start
  the other. Uses the Docker SDK to manage containers by name.
- Default mode at boot: localization (AR tracking is the primary use case;
  reconstructions queue and wait for the user to toggle).

`GET /localizer-address` returns `{"address": "http://localizer:8000"}` when
the localizer is running, or `{"address": null}` when it is not. This is the
single endpoint the API queries.

The mode switcher is absent from the k8s score files — like the ngrok relay,
it is a compose-only workload. On k8s, both the localizer and reconstructor
run on separate GPU nodes; no mode switching is needed.

### Localization router abstraction

The API's `localization.py` route is a dumb forwarder. Today it calls
`http://localizer:8000` directly. In the new design, it asks the router (the
mode switcher on compose) one question: "where do I send this?" The router
returns an address or null. The API forwards or returns "try again later."
The API never knows why — modes, sessions, pod affinity are all the router's
business.

```
phone → API (localization.py)
          └── asks router: "give me the localizer address"
                router returns address or null
          └── if address: forward to localizer at that address
              if null: return "try again later"
```

The client (capture tool) talks to the mode switcher directly for UX — "what
mode am I in?", "switch to reconstruction", "why is localization
unavailable?" The client's affordance for explaining the system's state comes
from the mode switcher, not from the API or the localizer.

### What stays unchanged

- **Localizer:** zero code changes. Loads models at boot, holds VRAM for its
  lifetime, serves requests, dies when stopped. No GpuSessionManager, no
  heartbeat, no idle timeout, no yield endpoint, no env-gating. The same
  container image runs on k8s (always-on Deployment) and compose
  (started/stopped by the mode switcher). It does not know which
  infrastructure manages its lifecycle.
- **Lease-server:** zero code changes. Pure work queue. No gpu_sessions
  table, no grant gate, no advisory lock, no new endpoints. Identical on
  both platforms.
- **Reconstructor:** zero code changes. Per-job model lifecycle (moving
  `load_models` from boot to per-job) is punted to a future k8s optimization
  — it frees VRAM during KEDA's 300s cooldown when GPU nodes are scarce. On
  compose with the mode switcher, the reconstructor runs until the user
  toggles modes; boot-load is fine because nobody else needs the GPU. The
  SIGTERM requeue logic (`workloads/reconstructor/src/reconstructor/main.py:124-140`)
  already handles "stopped mid-job" correctly — that is what it was built
  for.

### Comparison with the superseded design

| Concern | Old design (gpu_sessions table) | New design (mode switcher) |
|---|---|---|
| New table in Postgres | Yes (gpu_sessions) | No |
| New endpoints on lease-server | 4 (acquire, heartbeat, release, gpu-state) | 0 |
| Grant gate in request_lease | Yes (advisory lock) | No |
| Localizer code changes | GpuSessionManager, heartbeat, idle timeout, yield endpoint, typed 503s | None |
| Localizer new dependencies | placeframe-lease-server-client | None |
| API code changes | 503 pass-through, blocked_by derivation, lease-server-client dep | One address-query call |
| Reconstructor code changes | Per-job model lifecycle (all modes) | None (punted to k8s) |
| Client regen (python + C#) | Yes (typed 503 schema) | No |
| Dead code on k8s | Grant gate + reaper run as no-ops | None (mode switcher doesn't exist on k8s) |
| New container | No | Yes (mode switcher, compose-only) |
| User-facing UX | Typed errors, "blocked by" messaging, yield verb | Simple mode toggle |

## k8s vision

On k8s, the mode switcher does not exist. Both the localizer and
reconstructor run on separate GPU nodes. The scheduler enforces GPU
exclusivity (`nvidia.com/gpu: 1`). KEDA scales the reconstructor based on
queued work. The localizer is an always-on Deployment with its own GPU.

The localization router abstraction is the constant across both platforms.
On compose, the router is the mode switcher (returns the one localizer's
address or null). On k8s at scale, the router would be a **session manager**
— a service that tracks which localizer pods exist, which maps they have
loaded, and routes requests to the right pod:

| | Compose (mode switcher) | K8s at scale (session manager, future) |
|---|---|---|
| Rows/sessions tracked | One (the single localizer) | Many (one per pod) |
| What it tracks | "Is the localizer running?" | "Which maps does this pod have loaded, at what address" |
| Routing | Trivial — one pod or none | Map-aware — route to the pod with the requested map |
| Scaling | None — manual mode toggle | KEDA or custom scaler (cold-start rate, map distribution) |
| GPU coordination | Mode switcher enforces exclusivity | Scheduler enforces exclusivity |
| Crash recovery | Docker restart policy on mode switcher | Pod lifecycle (k8s restarts, device plugin frees GPU) |

The API's abstraction ("ask the router for an address") is the same on both
platforms. The router's implementation differs. The compose mode switcher is
forward-compatible with the k8s session manager — it is the degenerate
single-pod case.

The k8s session manager is not designed in this ADR. It is sketched here to
validate that the compose design is not a dead end. The session manager
would get its own ADR when multi-pod localizer deployment becomes a real
need. The open question below decides how much of the k8s vision to design
now vs. defer.

### Why the localizer can't scale to zero on k8s

AR tracking needs sub-second response. Model load takes seconds. KEDA's
polling interval adds ~30s. If the localizer scaled to zero when idle, the
first query after idle would take 30-60s (KEDA detects work → schedules pod
→ container starts → models load). Unusable for real-time AR. So the
localizer is always-on on k8s, holding a GPU permanently. This works because
it has its own GPU node — no contention.

## Rejected alternatives

Carried over from the superseded design (still apply):

- **`docker pause` / cgroup freezer** — freezes processes, releases no VRAM.
- **MIG partitioning** — data-center GPUs only; not desktops.
- **CUDA MPS** — shares a context, enforces no memory cap.
- **cgroup / device-plugin VRAM limits** — no enforceable VRAM limit exists
  for compose desktops; `nvidia.com/gpu` counts devices, not bytes.
- **Localizer on CPU** — ~700 ms/query becomes multi-second; kills AR use.
- **Two services polling each other** — check-then-act races resurrect the
  OOM.

Rejected during this design session:

- **Postgres-backed mutual exclusion (gpu_sessions table + grant gate +
  heartbeat + TTL reaper).** The previous design. Extensively explored and
  ultimately rejected because: (1) it pollutes the lease-server — a clean,
  platform-agnostic work queue — with compose-specific GPU coordination code
  that runs as dead no-ops on k8s; (2) the coordination machinery
  (heartbeat, idle timeout, yield, typed errors, blocked_by, client regen)
  is heavyweight for a single-GPU deployment; (3) the localizer — previously
  dependency-free — gains `placeframe-lease-server-client` and a
  GpuSessionManager; (4) the fundamental approach (both containers running
  simultaneously, fighting over VRAM) creates the problem the machinery
  exists to solve. The mode switcher eliminates the problem by not running
  both containers at once.
- **Lease-server checks localizer via HTTP.** Reintroduces the check-then-act
  race: lease-server asks "holding VRAM?" → localizer says "no" → grant →
  localization request arrives → localizer loads → OOM. Also blocks on the
  localizer's event loop during requests (~700ms).
- **Per-request flag in the lease-server.** Flag's lifetime (~700ms)
  doesn't match VRAM hold's lifetime (minutes to hours). The gap between
  requests is where the OOM happens.
- **In-memory flag in the lease-server.** Killed by lease-server restart —
  up to 60s window where the localizer holds VRAM but the lease-server
  thinks the GPU is free. Also needs a separate asyncio.Lock for async
  serialization.
- **Routing localization through the lease machinery (localization as queued
  jobs).** Localization is real-time (~700ms); poll-loop delay (5s average)
  kills AR tracking. The localizer and reconstructor have fundamentally
  different usage patterns (real-time session vs. batch job) that don't fit
  the same queue abstraction.

## Open questions

All closed. Each carries a `Decision:` line below. The design is locked
pending the code-verification session (step 3 of the session protocol).

### 1. Default mode at boot

`boatyard up` starts the stack. Which GPU container should be running
initially?

- (a) Localization — AR tracking is the primary use case. Reconstructions
  queue and wait for the user to toggle.
- (b) Reconstruction — process any queued work first, then the user toggles
  to localization.

**Decision: (a).** AR tracking is the primary, time-sensitive use case
(sub-second response). Reconstruction is batch work that queues fine.
Starting in reconstruction mode would leave AR unavailable at boot until the
user notices and toggles — backwards for the primary case. Matches the
commitment already in the Mechanism section.

### 2. Transition semantics — interrupt or wait?

Switching modes requires stopping one GPU container and starting the other.
In-flight work may be interrupted.

- (a) Interrupt both: SIGTERM the localizer immediately (kills in-flight
  localization), SIGTERM the reconstructor immediately (requeues the job).
- (b) Wait for localization, interrupt reconstruction: wait for in-flight
  localization to finish (~700ms), SIGTERM the reconstructor immediately
  (requeue is safe).
- (c) Wait for both: wait for in-flight localization AND current
  reconstruction job to finish. Could be minutes for reconstruction.

**Decision: (b).** Waiting ~700ms for an in-flight localization to complete is
nearly free and avoids a visible hiccup to anyone mid-tracking. Interrupting
reconstruction is fine — its SIGTERM requeue is purpose-built for exactly
this. (a) kills a near-finished localization for no real benefit; (c) blocks
the toggle behind a reconstruction job that could run for minutes, defeating
the point of a quick switch.

### 3. Boot race prevention

Both GPU containers are defined in the compose file. `boatyard up` starts
all services. Both GPU containers could briefly start and contend for the
GPU before the mode switcher stops one.

- (a) Don't auto-start GPU containers: define them in compose but don't
  start them at `up`. The mode switcher starts the appropriate one. Requires
  a compose mechanism for "defined but not started."
- (b) Accept brief overlap: start both, mode switcher immediately SIGTERMs
  one. The overlap is seconds; OOM risk is low but nonzero.
- (c) Sequence via depends_on: the mode switcher starts first and
  immediately stops one before the other starts.

**Decision: (a), via boatyard `up` selective-start + a provisioner-emitted
mode switcher that reconciles on boot.**

Start policy is its own annotation, separate from the gpu annotation: a
workload carrying `boatyard/autostart: "false"` is excluded from boatyard
`up`'s start step — created stopped, left for whatever enables it (the
mode switcher; boatyard neither knows nor cares). The gpu annotation keeps
its released semantics
untouched: substrate only, `"true"`, the patch templates its one reader.
The boatyard change is **`up` logic**, not a compose patch template:
`boatyard up` runs `docker compose up -d --no-start` (creates ALL
containers stopped, env slots resolved), then `docker compose start` for
every service except the held ones — any service, gpu or not. GPU
containers exist, stopped, from boot. The mode switcher
starts/stops **existing** containers — enable/disable, no creation logic, no
compose-file mounting, no config hardcoding. The k8s rendering is unchanged
— selective-start is a compose-only `up` behavior. The escape hatch is
removing the annotation (absence = today's auto-start behavior). Both
existing GPU workloads set `boatyard/autostart: "false"` (plan phase 5).

**Amendment (post-execution): the first execution encoded this wrong.** It
made `managed` a *value* of `boatyard/gpu` — alongside an invented `always`
— and widened the gpu patch templates to recognize both as GPU-carrying.
That conflated two orthogonal concerns: whether the container starts at
`up` is a lifecycle question that could apply to any container, not just
gpu ones, while `boatyard/gpu` exists to answer "does
this workload need GPU reservations?". The value-encoding made the
lifecycle concern inexpressible for non-gpu services and required a real
template change (widening the `"true"` guard, a behavioral change for any
consumer already using those strings). The split annotation needs no
template change at all, makes absence the escape hatch, and was
re-executed on the boatyard branch before anything downstream consumed it
(see the plan's phase 1). A follow-up rename settled the split
annotation's name: `boatyard/autostart: "false"`, not `boatyard/managed:
"true"` — "managed" named the consumer's motivation (an external
orchestrator owns the start/stop), an implementation detail boatyard can
neither see nor enforce, while the annotation's whole contract with
boatyard is the one bit of whether the container starts at `up`.

This replaces an earlier profiles-based approach that was revised after Q12
exposed a cascade: profile-gated services aren't created at `up`, so the
mode switcher had to create them itself, which forced a pre-creation step
(`--profile gpu-managed up --no-start`) to make them exist after all —
paying twice (profile machinery + pre-creation) for what `--no-start` +
selective start achieves once. Profiles also required a boatyard compose
patch template (profiles emission) and a test exception; both are
eliminated. The tradeoff is that raw `docker compose up` (the pressure
valve, `stack/AGENTS.md:142`) starts both GPU containers → the race
returns. Profiles protected the pressure valve; selective-start does not.
But the pressure valve is a rare escape hatch for when boatyard breaks, the
race is a visible OOM (not a silent failure), and the operator is already
in manual/debugging mode when using it. The caveat is documented: "raw
`docker compose up` starts both GPU containers — use `boatyard up` or start
services selectively." Trading structural simplicity (every boot) for
escape-hatch safety (rare) was the wrong trade.

The mode switcher is NOT a score workload. It is the compose provisioner's
emitted service for a new `localizer-router` resource type — the same
pattern as seaweedfs (code in `workloads/mode-switcher/`, emitted by
`stack/score/compose/localizer-router.yaml`, not authored as a score
workload, not in `boatyard.yml`'s workloads list). The API declares
`resources.localizer-router: type: localizer-router` and consumes
`outputs.address` — it depends on the interface ("a thing that provides a
localizer address"), not the implementation. On compose the provisioner
emits the mode switcher and outputs its URL; on k8s today a degenerate
outputs-only provisioner outputs `http://localizer:8000` (the localizer is
always-on on its own GPU node); on k8s at scale the provisioner emits the
session manager. Same resource type, different provisioner per tier — the
established pair pattern. The API stops referencing the localizer workload
directly (the `resources.localizer` service-port block and
`LOCALIZER_CONTAINER_URL` env var are replaced by the `localizer-router`
resource and one `address` consumption).

The docker-socket bind (`/var/run/docker.sock`) is authored directly in the
compose provisioner's service block — provisioners author full compose
service definitions including `volumes:` (see
`stack/score/compose/seaweedfs.yaml`). No boatyard docker-socket patch
template is needed. The exact Docker access method (SDK vs CLI) is Q12's
call, but the mount mechanism is settled here.

One test invariant in `scripts/tests/test_score_compose_generation.py`
moves from blanket to scoped: the bind assertion (lines 54-55) permits
exactly the `/var/run/docker.sock` bind on exactly the mode-switcher
service. The invariant's intent (catch accidental binds from the
score-compose post-pass) stays intact — the exception is explicit and
audited. The profiles assertion (line 52) is **unchanged** — no profiles
exist anywhere in the artifacts. `CORE_SERVICES` (line 10) gains the mode
switcher.

**Boot reconciliation (sub-decision).** At its own boot/restart, the mode
switcher does NOT blindly start `DEFAULT_MODE`. It inspects existing GPU
container state and reconciles: adopt the running GPU container's mode as
the current mode, stop any extras. Container state is the source of truth;
no persisted mode state is needed. This covers edge cases that blind-start
would re-introduce the OOM race in: `boatyard up` after partial cleanup
(leftover GPU container), mode switcher crash + restart (if a restart
policy is ever added — today's default `no` mitigates this but the
reconciliation makes it robust), and operator-triggered raw
`docker compose up` (both GPU containers start; the mode switcher stops
one). Selective-start prevents the `boatyard up` dual-start race;
reconciliation prevents the mode-switcher-boot race and the raw-`up` case.
Both are boot-race prevention.

The exact interface contract — whether the API does a runtime HTTP query to
`<address>/localizer-address` (returning null when the localizer is
stopped) or forwards directly to `<address>` — is downstream: Q5 ("try
again later" response format implies a runtime query returning null) and
Q10 (k8s vision detail level) settle it. Q3 commits to the resource type
existing and the compose provisioner emitting the mode switcher; the
runtime-query shape is not Q3's to decide.

### 4. Auto-switch back to localization after queue empties?

When in reconstruction mode and the queue empties, should the mode switcher
auto-switch back to localization, or always require manual switching?

- (a) Manual only: the user toggles back. Consistent with "the toggle is the
  yield." The client could hint "queue empty — switch back to localization?"
- (b) Auto-switch after a cooldown: if no jobs have run for N minutes,
  switch back to localization automatically. Convenient but surprising — the
  user might be about to queue more work.
- (c) Configurable: `AUTO_SWITCH_BACK=true/false` env var.

**Decision: (a).** Auto-switching is a footgun: the user queues a batch,
walks away, the queue drains, the system flips to localization — and when
they queue the next batch minutes later, AR tracking dies mid-session
because the system flipped itself back and forth (a 10-30s transition each
way) without them asking. The mode switcher is a simple, predictable
toggle; surprise state changes erode trust in a tool whose entire job is
"the user explicitly chooses which mode." The client hinting "queue empty
— switch back to localization?" gives the convenience of (b) without the
surprise — the user still pulls the trigger. (c) adds a config surface for
a behavior that shouldn't exist.

### 5. "Try again later" response format

When the API asks the router for a localizer address and gets null, what
does it return to the client?

- (a) 503 with a plain message ("Localization unavailable"). The client
  knows why from the mode switcher directly.
- (b) 503 with a structured code from the router (e.g.,
  `{"code": "reconstruction_mode"}`). The API passes it through without
  understanding it.
- (c) 502 (same as today's behavior). Simplest but least informative.

**Decision: (a).** This locks the interface contract Q3 deferred: the API
does a **runtime HTTP query** to `<address>/localizer-address` and gets
back `{address: string | null}`. When null, it returns 503 "Localization
unavailable." This is the contract the router abstraction requires — the
API learns at request time whether the localizer is available (it may be
stopped in reconstruction mode), which is the whole point of the
abstraction. (b) leaks router-internal vocabulary (mode names, pod-affinity
reasons) through the API, which the design explicitly rejects — the client
gets "why" from the mode switcher directly, not through the API's response
code. (c) preserves today's opaque 502 — the exact failure the design
exists to fix.

**Amendment (from Q10): the runtime query is conditional on `managed`.**
The query applies when `managed: true` (compose — the localizer may be
stopped, availability is uncertain). When `managed: false` (k8s today — the
localizer is always-on, availability is certain), the API forwards directly
to `<address>` without the query; the 503 "try again later" path never
triggers. Q5's intent ("learn availability when uncertain") is preserved —
`managed: false` means it's certain. The API branches on `managed`
(config-driven, same shape as `auth_mode`); it does not know "compose vs
k8s." Q10's decision records the debt accepted for leaving the k8s case
under-documented.

### 6. Queue visibility in localization mode

When in localization mode, reconstructions queue but don't process. How does
the user know there's queued work?

- (a) Client checks the API for queued reconstruction count alongside the
  mode toggle. Shows "N reconstructions queued — switch to reconstruction
  mode to process."
- (b) Mode switcher exposes queue depth (queries the API or database).
  One-stop-shop for status.
- (c) Client just shows "localization mode" and the user checks
  reconstruction status separately.

**Decision: (a).** The queue is the lease-server's concern (it's the work
queue) — the API already exposes reconstruction status endpoints. The
client already talks to the API for everything else; adding one queue-depth
query next to the mode toggle is trivial and keeps the mode switcher
focused on its one job (container lifecycle + mode state). (b) makes the
mode switcher a proxy for API/database state it doesn't own — it would gain
an API client dependency and a reason to reach into the data layer, purely
to save the client one call it's already making. (c) is the status quo —
the user gets no prompt and queued work sits silently, which is the failure
mode this question exists to prevent.

### 7. Cold start after mode switch

Switching to localization mode starts the localizer cold (no maps cached).
First requests trigger S3 downloads (seconds of latency per map).

- (a) Accept it: first requests are slow, subsequent are fast. Same as
  today's first-request-per-map behavior. The localizer's healthcheck
  (`/version`) passes immediately.
- (b) The mode switcher waits for the localizer's healthcheck to pass
  before marking it available. The client shows "warming up" during startup.
- (c) Pre-warm known maps on startup (requires the localizer to know which
  maps to load — a database dependency or persisted state).

**Decision: (a).** This is the existing behavior — today's localizer
already pays first-request-per-map latency. Mode switching doesn't make it
worse; it just makes it happen more often (each switch to localization is a
cold cache). The localizer's design is deliberately map-cache-agnostic
(loads on demand); (c) would couple it to a map registry it doesn't have,
adding a dependency for a latency optimization. (b) is a no-op as written —
the healthcheck is `/version`, which passes at boot before any map loads, so
"wait for healthcheck" gates on nothing useful. The honest version of (b)
would be "change the healthcheck to probe map readiness," but readiness is
per-map, not global — there's no single "ready" state to gate on. Accept the
cold cache; the client already handles per-request latency variance.

### 8. Programmatic mode switching

The mode toggle is in the client UI. But can modes also be switched
programmatically?

- (a) Client only: the mode switcher has an API endpoint, but only the
  capture tool uses it.
- (b) CLI verb too: `uv run gpu-mode reconstruction` (or similar). Useful
  for operators and automation.
- (c) API proxy: the API exposes `POST /mode` that proxies to the mode
  switcher. The client calls the API, not the mode switcher directly.

**Decision: (b), with a discovery mechanism for the client.**

Operators need a way to flip modes without the phone app — debugging,
headless air-gap LAN boxes with no phone attached, automation. Placeframe
should have a local CLI surface (the repo's `uv run <verb>` pattern), and
`uv run gpu-mode` (one token, not `uv run gpu mode`) shells to the mode
switcher's `POST /mode` endpoint, no new logic. (a) leaves operators
reaching for `curl` against an internal endpoint — works but undiscoverable.
(c) routes the toggle through the API gateway, but the mode switcher is the
client's UX surface for system state (per the design: "the client's
affordance for explaining the system's state comes from the mode switcher"),
and forcing it through the API collapses the router abstraction's clean
separation (the API forwards localization; the mode switcher owns mode
state). The client talks to the mode switcher directly for mode/mode-state;
the CLI verb mirrors that for operators.

**Discovery mechanism (resolved as part of Q8).** The client must (1) find
the mode switcher's endpoint and (2) know whether mode switching applies at
all (compose: yes; k8s: no mode switcher exists). Today the repo has no
unified discovery endpoint — `GET /server-info`
(`workloads/api/src/routers/server_info.py:17-32`) returns auth params only,
and the "single URL" property is emergent: the client holds one
`backendUrl`, and two client libraries hardcode two path suffixes onto it
(`/server-info`, `/livekit-token/connection-details`), routed by boatyard's
path-prefix edge. No capability/deployment flags reach clients today.

The mode switcher fits this pattern as a **third path-prefixed route** on
the same public host (e.g., `/gpu-mode/* → mode-switcher:8000`), with a
third hardcoded path constant in the client library. The single-URL
property holds — no new discovery infra.

The capability problem is real and must be solved: on k8s there's no mode
switcher, so no `/gpu-mode/*` route exists; the client must know before
calling whether mode switching applies. The backend tells the client, not
the client probing and inferring from a 404. The `localizer-router`
resource type (committed in Q3) gains a second output alongside `address`:

- `address` — the router's URL (mode switcher on compose, degenerate
  stub/localizer on k8s). The API already consumes this.
- `managed` — `bool`. `true` on compose (the mode switcher exists, modes
  apply); `false` on k8s (degenerate, no modes). The compose provisioner
  outputs `managed: true`; the k8s provisioner outputs `managed: false`.

The API consumes `${resources.localizer-router.managed}` as an env var
(e.g., `GPU_MODE_MANAGED`) and surfaces it in `/server-info` as a
capability field. The `ServerInfo` model gains a `gpu_mode_managed: bool`
field (exact name is Q11's call). The client flow: call `GET /server-info`
(already called at boot); read `gpu_mode_managed`; if `true`, show mode UI
and talk to `<backendUrl>/gpu-mode/mode`; if `false`, no mode UI, no mode
calls.

This fits every existing pattern: the `managed` output is score-native
(provisioner provides it, the API consumes it via the resource — same as
`s3.endpoint`, `config.public_url`); the `/server-info` extension is the
one discovery endpoint the client already calls; the mode switcher's path
is a third hardcoded constant, consistent with the two that exist. No
unified discovery manifest is built — LiveKit stays on its own
`/livekit-token/connection-details` path; each service owns its own path
prefix. If a unified manifest is wanted later, that's a separate design.

### 9. Healthcheck for stopped containers

The localizer has a healthcheck on `/version` (5s interval,
`stack/generated/compose/compose.core-cuda.yaml:139-148`). When stopped
(reconstruction mode), the healthcheck fails. Docker compose reports
unhealthy.

- (a) Accept unhealthy: the mode switcher knows the localizer is
  intentionally stopped. `docker compose ps` shows unhealthy, which is
  misleading but harmless.
- (b) The mode switcher provides a meta-healthcheck: an endpoint that
  returns healthy if "the right container for the current mode is healthy."
  Operators check the mode switcher, not individual containers.
- (c) Remove the healthcheck from the localizer in compose and rely on the
  mode switcher to detect hangs.

**Decision: (a).** A stopped container shows `Exited` in `docker compose ps`,
not `unhealthy` — the `unhealthy` state only applies to a running container
whose healthcheck is failing. Either way, Docker can't distinguish
"intentionally stopped" from "crashed"; that distinction lives in the mode
switcher's knowledge. (b) builds a meta-healthcheck endpoint to surface that
distinction authoritatively, which is the right shape for a fleet ops
platform but overengineering for the current situation: the mode switcher
targets single-GPU desktops and air-gap LAN boxes, where an operator can
check `GET /mode` and reason about whether an `Exited` localizer is
intentional. The meta-healthcheck is machinery the situation doesn't yet
warrant; revisit if the deployment grows beyond single-host. (c) removes
the localizer's own hang-detection while running — the healthcheck already
works when the container is up; removing it loses real signal for no gain.

### 10. k8s vision detail level in this ADR

How much of the k8s session manager should be designed here?

- (a) Full design: the ADR describes the session manager's API, map
  tracking, routing, and scaling. The compose mode switcher is a subset.
- (b) Vision only: the ADR sketches the k8s vision (above) and explains why
  the compose design is forward-compatible. The session manager gets its
  own ADR when needed.
- (c) No k8s: the ADR only designs the compose mode switcher. The k8s case
  is "both run on separate nodes" (today's state).

**Decision: (c), with the `managed`-branch refinement.**

The session manager (map-aware routing across many pods, cold-start
scaling, map distribution) is substantial design that doesn't exist as a
need yet — the localizer is a single always-on pod per GPU node today.
Designing it fully now is speculative work that will be outdated when real
multi-pod needs arrive. The k8s vision sketched above explains why the
compose design is forward-compatible (the `localizer-router` resource type
is the constant; the provisioner is the variable); the session manager gets
its own ADR when multi-pod localizer deployment becomes a real need.

**The `managed`-branch refinement (avoids the stub Q5's contract seemed to
require).** Q5 locked the contract as "the API does a runtime query to
`<address>/localizer-address → {address | null}`." Taken literally, k8s
would need a stub service implementing that endpoint — a new always-on
service every localization request hops through, and a single point of
failure for all localization on k8s even though the localizer is fine. That
is high-interest debt for no benefit. The `managed` flag (committed in Q8)
avoids it: the API branches on `managed` — when `true` (compose), query
`<address>/localizer-address` (the localizer may be stopped); when `false`
(k8s), forward directly to `<address>` (which IS the localizer's URL — the
localizer is always-on, no query needed). The k8s provisioner is
outputs-only (`address: http://localizer:8000`, `managed: false`) — no
service emitted, no stub, no extra hop, no failure point. This is a
config-driven branch, not platform detection — the API already branches
this way on `auth_mode` (disabled vs keycloak). The API doesn't know
"compose vs k8s"; it knows "is mode managed."

**Debt accepted.** (1) The API has a `managed` branch — low, established
pattern. (2) The k8s provisioner is outputs-only, ~5 lines — low,
self-explanatory. (3) The `/localizer-address` contract is compose-only in
practice (on k8s it's never called); the ADR under (c) doesn't spell this
out — a future reader infers it from the `managed` flag. Medium-low, one
inference step. (4) Forward path to session manager: k8s provisioner gains
a service, `managed` may flip; the API's branch already handles
`managed: true`. Low. (5) Q5's decision text amended below to name the
branch. The main interest is #3 — a one-sentence clarification that (c)'s
"no k8s" stance leaves unwritten. Not structural.

(b) would document the k8s case more explicitly, but the k8s case under the
refinement is so trivial (an outputs-only provisioner + a config branch)
that documenting it fully is more ceremony than the content warrants.

**Q5 amendment.** Q5's decision said "the API does a runtime HTTP query to
`<address>/localizer-address" unconditionally. Refined: the runtime query
applies when `managed: true` (compose — the localizer may be stopped,
availability is uncertain). When `managed: false` (k8s today — the
localizer is always-on, availability is certain), the API forwards directly
to `<address>` without the query. Q5's intent ("learn availability when
uncertain") is preserved — `managed: false` means it's certain. The 503
"try again later" path is compose-only; on k8s today it never triggers.

### 11. Naming

The mode switcher / router service needs a name that appears in score files,
DNS, env vars, and code.

- Options: "mode-switcher", "gpu-coordinator", "localization-router",
  "gpu-orchestrator", or something else.
- This is a bikeshed but needs to be locked early because it affects
  everything downstream.

**Decision: `mode-switcher` for the service/workload/DNS/path; 
`localizer-router` for the resource type.**

The resource type is `localizer-router` — already committed across Q3/Q5/Q8
decisions. It describes the abstraction the API depends on (routes
localization requests to an address). The compose service/workload is
`mode-switcher` — the concrete implementation that does container lifecycle
+ mode state. Keeping the implementation name (`mode-switcher`) distinct
from the abstraction name (`localizer-router`) makes the "this is the
degenerate single-pod case" relationship explicit: the resource type is
the constant across tiers, the compose service is one implementation of
it. `gpu-coordinator`/`gpu-orchestrator` over-name — the service switches
between two containers, it doesn't coordinate GPUs generally.

The service name `mode-switcher` carries everywhere: DNS
(`http://mode-switcher:8000`), the compose provisioner's emitted service
block, the path prefix on the public host (`/gpu-mode/* → mode-switcher:8000`),
and the workload directory (`workloads/mode-switcher/`). The CLI verb
`uv run gpu-mode` (Q8) and the path prefix `/gpu-mode/*` use the "mode"
stem, consistent with `mode-switcher`. The resource type
`localizer-router` appears in `stack/score/api.yaml` (`resources.localizer-router:
type: localizer-router`) and the provisioner files
(`stack/score/compose/localizer-router.yaml`,
`stack/score/k8s/localizer-router.yaml`). The `managed` flag and
`gpu_mode_managed` capability field (Q8) keep their names — they describe
the property, not the service.

### 12. Docker socket access method

The mode switcher needs to start/stop containers. The Docker socket is
root-equivalent on the host.

- (a) Docker SDK: the mode switcher uses `docker` Python library directly.
  Full socket access, but the code is narrow and auditable.
- (b) `docker compose` CLI: the mode switcher shells out to
  `docker compose up/down <service>`. Still needs Docker access but through
  compose's abstraction.
- (c) Docker API with filtered access: use Docker's TLS or socket proxy
  (e.g., Tecnativa/docker-socket-proxy) to limit operations to
  start/stop only.

**Decision: (a).**

Post-Q3-revision, the mode switcher's Docker interaction is start/stop/
inspect **existing** containers (GPU containers exist, stopped, from boot
via boatyard `up`'s `--no-start` + selective-start). No creation logic. The
Docker SDK finds containers by compose labels
(`docker.containers.list(filters={"label": ["com.docker.compose.service=localizer",
"com.docker.compose.project=placeframe"]})`) and calls `.start()` /
`.stop()` / `.wait()` directly — no compose files needed in the container,
no container-name reconstruction, no CLI output parsing. Structured state
(`container.status`) makes boot reconciliation (Q3) and wait-for-exit (Q2)
cleaner than parsing `docker compose ps` output.

(b) was considered but rejected: it shells out to an external binary (the
repo convention is "all scripting is Python"), adds a `docker compose` CLI
dependency to the container image, parses CLI output for state, and its
viability hinged on whether `docker compose start` works without the
compose files (`-f`) — an uncertainty (a) sidesteps entirely. (b)'s
abstraction-level advantage (service names vs labels) was small and didn't
justify the shell-out surface for a service holding root-equivalent access.

(c) was considered but rejected. The socket proxy relocates the code-bug
risk to the proxy rather than eliminating it (the proxy is software with
its own filtering-bypass surface) — real defense-in-depth (two bugs needed
instead of one), but its value is contingent: the proxy can only block
container CREATE (the dangerous operation) if the GPU containers are
pre-created so the mode switcher only needs START/STOP. Without that
contingency, the proxy must allow CREATE, which accepts host binds and
privileged flags — the filter is per-endpoint, not per-field, so allowing
CREATE = allowing escalation. (c) becomes theater. For single-host,
trusted-operator, compose-only deployment — where the mode switcher's input
surface is one enum-validated `POST /mode` with constant service names and
no string construction in the Docker calls — (a) with strict validation is
the honest trade. The code-execution risk in the mode switcher is low
(tiny auditable service, no untrusted input parsing beyond the enum, pure
Python Docker calls with no shell-out). (c) is the upgrade path if the
deployment grows beyond single-host or gains untrusted input surface.

The `docker` Python library is a declared dependency in the mode
switcher's `pyproject.toml`. Shell-out to Docker does not occur — all
container interaction is via the SDK's Python API.

## Carrying costs

- A new container (the mode switcher) — compose-only, simple, but needs
  Docker socket access (root-equivalent on the host).
- The API gains one extra HTTP call per localization request (query the
  router for address) — sub-millisecond on the compose network.
- The client (capture tool) gains a mode toggle UI and a mode-switcher API
  client. Lives in the placeframe-capture-tool repo.
- The score files gain the mode switcher service definition (compose only).
- Transition latency (10-30s per mode switch, during which neither service is
  available).
- Cold map cache after each switch to localization mode (first requests per
  map trigger S3 downloads).
- The mode switcher is a new failure point — if it crashes, mode switching
  is unavailable until restart. The currently-running GPU container is
  unaffected (it's a separate container).

## See also

- [`shared-gpu-coordination.md`](shared-gpu-coordination.md) — the superseded
  design. Its rejected-alternatives analysis (docker pause, MIG, MPS, etc.)
  still applies.
- `workloads/AGENTS.md` — stack data flow, service inventory, the
  worker-pull architecture the mode switcher joins.
- `workloads/localizer/AGENTS.md` — the localizer's boot lifecycle, map
  cache, and request flow. Unchanged by this design.
- `workloads/reconstructor/AGENTS.md` — the reconstructor's lease loop and
  SIGTERM requeue logic. Unchanged by this design.
- `workloads/lease-server/src/routers/leases.py` — the lease state machine.
  Unchanged by this design.
- `workloads/api/src/routers/localization.py` — the localization proxy route
  that will query the router for an address.
- `stack/score/localizer.yaml`, `stack/score/reconstructor.yaml` — the score
  sources for the two GPU services.
- `stack/generated/compose/compose.core-cuda.yaml` — the generated compose
  artifact the mode switcher rides.
