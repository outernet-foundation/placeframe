---
updated: 2026-11-21
---

# Demand-driven GPU orchestration — ADR

Successor to [design/gpu-orchestration.md](design/gpu-orchestration.md), whose
execution landed on this branch. That design hardcoded two assumptions: the two
GPU workloads cannot coexist, and a human decides which one runs. Both failed
against reality within days of shipping.

## Status and session protocol

This document is the entry point for a fixed sequence of sessions. A session
that opens by reading this doc must check this section first.

1. **Brainstorming session (complete, 2026-11-21).** Reframe identified,
   settled decisions recorded below, open questions enumerated. ADR authored
   at the repo root at the operator's instruction; it may move under
   `design/` alongside its predecessor.
2. **Interview session (complete, 2026-11-21).** The operator closed each
   open question in turn; all eight carry `Decision:` lines below.
3. **Planning review (complete, 2026-11-21).** Three independent candidate
   plans were produced from this ADR; their convergence and feedback drove
   the amendments folding contradiction fixes and pinned contracts into the
   decisions below. The checkpoint/resume prerequisite (S11) settled as an
   explicit external dependency with an interface contract.
4. **Plan session (complete, 2026-11-21).** The plan lives in
   [demand-driven-orchestration-plan.md](demand-driven-orchestration-plan.md)
   (repo root beside this ADR until closeout).
5. **Execution sessions (complete, 2026-11-21).** One phase per session, per the plan's
   execution protocol. All four phases are complete on this branch: the rename to
   `gpu-orchestrator`, the lease-server `/queue-state` endpoint, the orchestrator
   rewrite + atomic mode-surface removal, and the live acceptance battery + docs
   fold. The full 13-step acceptance battery passed live on the GPU sandbox
   (2026-11-21), including a real end-to-end reconstruction preempted and rerun by
   the policy; one minor fix landed from it (the policy PATCH handler declared
   `sync_to_thread=False` — its Litestar boot warning was noise on every start).
   With execution complete this ADR stops being load-bearing; the hardened truth
   lives in the co-located `AGENTS.md` files. Three plan-vs-reality settlements
   landed during execution, all recorded in the phase commits: the `/gpu-mode/*`
   claim needed an explicit `, strip` under the boatyard 0.9.3 claims grammar (the
   committed no-strip claim 404'd at any freshly rendered gateway); the lease-server
   was restructured into an installable `src/lease_server` package so its tests can
   join the combined battery (a second flat `src` collides with the api's in
   `sys.modules`); and the plan's `extra_headers` spelling for
   exception-carried response headers is starlette vocabulary — litestar's
   kwarg/attribute is `headers`, so the 503 carries `Retry-After` via
   `HTTPException(headers=...)` and the shared handler forwards
   `exception.headers` in both branches (the ≥500 detail masking is unchanged,
   which means the 503's detail is masked — the header is the wire contract).

## Problem

An external contributor runs placeframe on a 32 GB VRAM card. Both GPU
workloads fit comfortably at once. The shipped mode switcher enforces
exclusive either/or as a hardcoded arity of one, so on his hardware it
manufactures scarcity that does not exist: while in reconstruction mode,
localization requests 503 for no physical reason, and vice versa.

Even under real scarcity (one GPU, only one workload fits), explicit mode
switching is the wrong interface. The human is acting as the demand signal:
they predict what they need next, flip a switch, wait out a cold start, and
flip back. The system already holds every fact needed to make that decision
itself — localize requests arrive at the API, reconstruction backlog sits in
the lease-server's queue — so the switching should be automatic, with the
manual verb demoted to an operator override.

The redesign must also keep one eye on the k8s future. Multi-machine and
multi-GPU scale-out is planned on Kubernetes, not compose. The policy
vocabulary grown here should map onto that world rather than fork the
operational model into two systems.

## The reframe

The mode switcher is not a placeframe feature. It is a stub of the control
plane compose lacks. Compose has actuation (start/stop) but no admission
control, no placement, no capacity or priority notion — VRAM contention is
invisible to it, which is why the pre-branch stack silently OOMed. Three
concerns the v1 design fused must stay separate:

| Concern | What it is | v1 answer | v2 answer |
|---|---|---|---|
| Capacity | fact about hardware: how many GPU activations fit | hardcoded 1 | config, from values |
| Policy | given capacity and demand, what runs | "whatever the human last POSTed" | automatic, demand-driven |
| Routing | where is the localizer, is it up | localizer-router + `managed` + 503 | unchanged |

The k8s mapping is exact and is the reason the vocabulary matters. The
orchestrator bundles three jobs compose ships none of:

| Job | Compose orchestrator | k8s counterpart |
|---|---|---|
| Observe demand | polls lease-server, watches the router seam | KEDA scaler, activator, Endpoints |
| Decide | policy: capacity, priority, pins, idle | scheduler, PriorityClass, HPA |
| Actuate | Docker SDK start/stop | kubelet starting pods |

The thing that survives the migration is not the container. It is the two
seams and the policy vocabulary. The seams map one-to-one, the policy maps to
config, the actuation dies. The orchestrator is the temporary occupant of
seams that are permanent — which also dictates its boundaries: it may contain
policy, actuation, and reconciliation; it may not contain product semantics
(leases, localize requests, tenant data). Product knowledge enters only as
configuration.

## Settled decisions

Each of these was resolved in the brainstorming session and is not open for
relitigation without new facts.

- **S1 — the mode switcher grows into a compose-only orchestrator.** Renamed
  (working name: the orchestrator), emitted by the compose provisioner as
  today, absent from the k8s rendering. Its k8s successor is configuration of
  the real control plane, not ported code. Compose remains a deployment tier
  forever (self-hosters, demos, dev); the orchestrator is compose's GPU
  control plane permanently.
- **S2 — capacity is data, not code.** Flows from `boatyard.values.yaml` into
  the orchestrator's env as the `gpu_contended` boolean (Q3). At
  `gpu_contended: false`, behavior is the pre-branch behavior: both GPU
  workloads run. "Out of the way" means no arbitration, not no
  reconciliation — the loop computes desired = all managed in both modes
  and repairs drift (an externally stopped container restarts on a later
  tick) in both modes; the no-op at `false` is emergent, not a mode switch.
  The constrained box and the 32 GB box are one policy with different
  values of one fact.
- **S3 — two priority classes, asymmetric.** Localization is interactive:
  latency-sensitive, preempts. Reconstruction is batch: restartable by
  construction (lease semantics), never preempts, fills idle capacity. This
  is the k8s PriorityClass vocabulary.
- **S4 — demand flows through seams the platform owns; the product never
  calls the platform.** The API gains no outbound dependency on the
  orchestrator. In k8s nothing pokes anything either: KEDA polls the queue
  source, the activator sits on the request path. (The alternative — the API
  POSTing demand notifications to the orchestrator — was proposed and
  rejected in the brainstorming session; see Rejected alternatives.)
- **S5 — localization demand is the routing seam.** Every `GET
  /localizer-address` query from the API is a demand heartbeat, null answer
  or not. A null answer is a failed localization attempt, the exact analog
  of an empty EndpointSlice. The endpoint is contractually reserved to the
  API's localize path; nothing else may poll it (the healthcheck is
  `GET /state`, Q6 — never this endpoint).
- **S6 — reconstruction demand is the queue seam.** One new read-only
  endpoint on the lease-server, `GET /queue-state`, answering two integer
  counts, `queued` and `in_flight` — the SQS `GetQueueAttributes` analogy,
  corrected to counts so a future KEDA scaler and the state report can
  distinguish backlog from in-flight. The demand predicate
  (`queued > 0 OR in_flight > 0`) is computed orchestrator-side, where
  policy lives; the endpoint stays a dumb attribute read. Poll failure
  holds the last successful sample with an Info log — reading "unreachable"
  as no-demand would preempt a running reconstruction to the resting state
  during every lease-server restart. The orchestrator never reads Postgres
  and never gains database credentials: the demand predicate encodes
  lease-state semantics the lease-server owns, a SQL string in config
  would rot silently and fail plausible (confident zeros), and the endpoint
  is the seam a KEDA external scaler can consume unchanged in the k8s
  world.
- **S7 — the API delta is approximately zero.** The existing per-request
  `resolve_localizer_address` flow and the 503-on-null contract stand. At
  most: a `Retry-After` header on the 503 (decided in Q7).
- **S8 — the lease-server is a claim coordinator over Postgres rows, not a
  proto-Kafka, and stays.** The truth of a reconstruction is a database row;
  the five lease endpoints grant exclusive claims on those rows. Kafka is a
  durable ordered log for high-volume fan-out — no lease, no visibility
  timeout, no renewal for minutes-long GPU jobs — and would put a second
  store of truth beside Postgres. Volume is dozens of jobs per day with one
  consumer type. The lease-server is tier-neutral and walks into k8s
  unchanged; of all services in the stack it has no migration ahead of it.
- **S9 — live policy API, in principle.** A control-plane API for runtime
  mutation is the k8s shape (`kubectl` is an authenticated live policy
  mutation). Three guardrails: it mutates runtime decisions only, never
  topology (which stays in values and flows through `up`); overrides are
  non-persistent, living in memory and dying at restart, values is truth at
  boot; it is not publicly routed by default (Q7 decides the surface).
- **S10 — the manual verb disappears in v2.** Automatic policy replaces
  explicit switching outright: no `POST /mode`, no override, the
  `gpu-mode` verb loses its mutation role. The capture tool's mode UI is
  removed with nothing replacing it (Q7) — a cross-repo change in
  placeframe-capture-tool. Overrides may return later as pins, strictly
  additive per Q6's decision.
- **S11 — the orchestrator requires no changes inside the two GPU workloads,
  with one declared external dependency.** The reconstructor gains
  preemptible, resumable jobs — checkpoint on SIGTERM, resume on next
  start — as an independently planned feature; the planning review
  (2026-11-21) settled it as an explicit external dependency, not a phase
  in this initiative's plan: the Q4 policy and the converger are correct
  without it (preemption then costs a requeue-and-restart, exactly the
  shipped v1 behavior — strictly-bounded degradation, capped by the idle
  window), and nothing in the orchestrator changes when it lands. Interface
  contract handed to that feature: (a) a checkpointed, paused job presents
  as claimable resumable work in `GET /queue-state`, counting in `queued`
  (nothing holds its lease while paused); (b) the orchestrator stops the
  reconstructor with an explicit stop timeout (~60 s placeholder) —
  docker's 10 s default SIGKILLs mid-checkpoint, so the checkpoint must
  fit the negotiated budget; (c) with it landed, localization-wins is
  hardwired behavior with no knob (S3): preempting a reconstruction costs
  a checkpoint cycle, not minutes of redone SfM. The localizer: zero
  changes. Lease semantics remain the ownership boundary for work state.
- **S12 — what v1 built that survives:** the localizer-router resource and
  `managed` flag (a k8s Service in embryo), compose-only provisioner
  emission, the autostart annotations + selective start (up creates-stopped;
  the orchestrator decides — this is what makes any automatic actuation
  possible), Docker-SDK actuation by compose label, and boot reconciliation
  (subsumed into the main loop per Q1).

## k8s vision

The end state on k8s: the API and lease-server unchanged, the orchestrator
absent. Routing is a Service with Endpoints (today's `managed: false`
outputs-only twin already is this). Demand-driven activation is KEDA
scalers — queue-driven scale-from-zero for the reconstructor, the postgres
or external scaler against the lease-server for demand, min-replicas for
keep-warm. Preemption order is PriorityClass. The compose orchestrator's
policy decisions must be expressible in that vocabulary, or the two tiers
fork.

## Open questions

Interview order below; each gains a `Decision:` line as resolved.

### Q1 — Internal architecture: reconcile loop or event transitions

The orchestrator computes "which managed services should be running" and
converges reality to it. Options: a periodic reconcile loop over a pure
desired-state function (kube controller-manager shape; boot repair is just
the first tick) versus event-driven transition handlers (the current code's
generalization: signals directly trigger stop/start actions). The current
single-file switcher already manages one mode axis and one input with a
transition marker and two locks; demand + capacity + timers multiplies the
interleavings an event design must handle explicitly.

**Decision (2026-11-21): the reconcile loop.** One `while True` background
task in the orchestrator process, started at boot. Each pass gathers the
inputs — heartbeat log, latest queue-state poll, capacity, pins, container
states, the clock — computes the desired running set with a pure function,
and converges the diff via the Docker SDK. Boot repair is the first tick:
`initialize()`'s separate repair path dissolves into the loop, leaving one
mechanism for boot, crash recovery, and steady state. The wait between
passes is an asyncio event with a timeout. The timeout guarantees a pass on
schedule (timers, queue polls, and docker drift are otherwise unpoked); the
`/localizer-address` handler sets the event after recording a heartbeat, so
the interactive path reacts in milliseconds instead of being tick-bound.
Pokes are never load-bearing — delete them and the system degrades to plain
periodic behavior. A converger transition runs to completion inside its
pass, never abandoned mid-swap; a pass that finds a transition in flight
skips actuation and re-evaluates on the next tick, and poke-triggered
passes reuse the cached queue-state sample (fetching only on the poll
cadence) — which is what keeps pokes literally never load-bearing.
Handlers decide nothing and actuate nothing; all
decisions happen inside the loop. The pure function is the unit-test
surface: input fixtures to desired sets under a fake clock, which is where
the Q4 and Q5 semantics get pinned.

### Q2 — Where per-service policy lives

The managed set (which compose services the orchestrator governs), their
priority class, and per-service hints could be config in
`boatyard.values.yaml`, or annotations in the score files beside
`boatyard/autostart` (which arrive as container labels the orchestrator can
discover via the Docker SDK). Values is where operators look; annotations
co-locate workload concerns with the workload and avoid name duplication.

**Decision (2026-11-21, final form after three corrections: hardcoded in
the orchestrator's own code).** The managed set — the two GPU services and
their per-service behavior — is hardcoded: `localizer` and `reconstructor`
are constants in the orchestrator, matched at runtime by the automatic
`com.docker.compose.service` label (the v1 switcher's proven plumbing).
The principle that settles it: **config that can only be changed by also
changing code isn't config, it's indirection.** Adding a third managed
workload requires policy code no env var can carry, and generalizing is
explicitly deferred (see below); the managed set is a repo-constant, not a
per-deployment fact. This is also the strongest form of the
manager-names-its-managees rule: the names live in the manager's own code
beside the behavior they trigger (heartbeat-mapped demand, preemption
direction, warm rest, drain grace). Two rejected ancestors, recorded so
they stay rejected: score-file annotations under a `placeframe.io/`
prefix materializing as container labels — a dependency inversion (the
managed thing volunteering for management; HPA/KEDA `targetRef` name their
targets, the targets never volunteer) plus a compose-only concern leaking
into tier-neutral workload files; and a `GPU_MANAGED_SERVICES` env stanza
with interactive/batch class symbols — generality smuggled in for a
third-workload future that is explicitly deferred. "Interactive" and
"batch" survive as prose describing the S3 asymmetry, not as identifiers.
Host facts and tunables — `GPU_CONTENDED`, the timers — remain values-file
keys (per-deployment facts). The layer rule: repo-constants live in code,
per-deployment facts live in values, runtime decisions live in memory
(S9).

### Q3 — Capacity representation and default

Enum `exclusive|both` versus per-workload VRAM weights. And the default:
`both` recreates the silent OOM on small cards; `exclusive` imposes
artificial scarcity on large cards until the operator reads the docs.

**Decision (2026-11-21): a boolean named `gpu_contended`, default `true`,
authored in the values file** — the values grammar's flat ALL_CAPS list,
so the key is spelled `GPU_CONTENDED`; `gpu_contended` names the concept.
True states the operator's hardware fact
"this GPU is a contended resource, only one managed workload fits", and the
orchestrator arbitrates exclusivity. False states "everything fits": the
orchestrator starts all managed services at boot and otherwise stays out of
the way. The name names the condition that makes a policy necessary rather
than the policy mechanism, and its meaning survives the eventual VRAM
weights generalization, where contention is derived by arithmetic instead
of declared. The default is the soft-fail side: current deployments keep
their behavior, small cards (the majority) are correct with zero config,
and a large-card operator pays one documented line. Defaulting false would
silently regress every small deployment into the CUDA OOM the predecessor
initiative existed to kill. Paired mitigation: under `gpu_contended:
true`, when the orchestrator observes demand for the held-out class while
the slot is occupied, it logs a one-line hint naming the knob once per
rising edge of held-out demand (never per tick), making the
default self-correcting for anyone reading logs. Enum and integer
representations remain rejected: the enum is the boolean with more syntax,
and the integer count is a fake stepping stone — counts only generalize to
interchangeable workloads, GPU workloads never are, "which combinations
fit" is inexpressible as a count, and the boolean's exhaustion when a
third managed workload lands is the loud, visible moment the weights
generalization deserves.

### Q4 — Demand predicates

**Semantics note (2026-11-21): designed for the checkpoint/resume world per
S11's interface contract, and correct without it.** The predicates below
assume preemption is eventually cheap — but they were chosen (in-flight
work counts as demand) so the policy is also right while checkpoint/resume
remains the declared, not-yet-landed external dependency of S11: until it
lands, preemption costs a requeue-and-restart, the shipped v1 degradation,
bounded by the idle window. Q4 was resolved through a user-story interview;
the predicates fall out of the stories.

**Decision (2026-11-21): one policy, from the user stories.** Under
`gpu_contended: true`, the desired state is: the localizer runs whenever
localization demand is active; otherwise the reconstructor runs whenever
reconstruction demand is active; otherwise the localizer runs — the resting
state is a warm front door. Localization demand is active iff a
`/localizer-address` query arrived within the localization idle window
(the number is Q5's): every query refreshes the clock, null answer or not,
demand is measured by request arrival and is independent of localizer
state. Reconstruction demand is active iff queue-state reports unclaimed
work OR an active lease: a strictly-"queued" reading produces either a
deadlock (a paused job never presents as queued and never resumes) or a
checkpoint-resume loop (paused jobs requeue, the last job of the day swaps
forever at the drain point), so in-flight work counts and the last job
finishes undisturbed. Contract note for the resume feature: a
checkpointed, paused job must present as claimable resumable work in
queue-state. Under `gpu_contended: false` none of this applies, both run
always. Localization always wins when demand exists, hardwired (S3, S11).

### Q5 — Timers and hysteresis

Idle timeout per class, minimum run time after start before reclaim is
allowed, cooldown after a preemption so a bursty localize stream cannot
ping-pong the GPU. Which of these are live-tunable through the policy API
versus boot-only.

**Decision (2026-11-21): idle window 10 minutes, poll interval 15 seconds,
both live-tunable, no anti-flapping machinery.** Both defaults live in the
values file; both are mutable at runtime through the orchestrator's
internal policy API (network placement per Q7), with validation floors —
window at least 60 s, poll at least 5 s — because a live-tuned window
small enough would manufacture the flapping the structure otherwise
prevents. Boot-time values below the floors clamp to the floor with an
Error log rather than crashing (Q8 makes the orchestrator a boot-ordering
dependency of GPU function; a bad timer must not brick the GPU); live
mutation below the floors remains a hard rejection. The policy is its own flap protection: the idle window is the
structural oscillation floor (localization demand cannot expire faster
than the window), and Q4's active-lease clause eliminated the
reconstruction-side oscillation, so possible swap cycles are slower than
the window and each transition completes before the next can begin
(transitions serialize in the converger). Guard timers were considered and
rejected as aimed at oscillations the policy cannot generate. Live
mutation lifecycle follows S9: values is truth at boot, live values are
in-memory and die at restart, every mutation logs old→new, and current
values are readable via GET so state is never opaque. The k8s precedent
for live mutation of exactly these numbers: the HPA stabilization window
and KEDA pollingInterval are runtime-mutable API objects.

### Q6 — Pin semantics

What overrides exist (pin a service, unpin, drain?), their precedence over
demand signals while set, and the fate of the current `POST /mode` wire
contract and its known callers (the capture tool's UI).

**Decision (2026-11-21): punt pins entirely — no overrides in v2.** No
pin, no unpin, no drain. `POST /mode` dies with nothing replacing its
mutation role, and the `gpu-mode` verb loses its write side (superseded by
Q7: the verb retires entirely — `gpu-policy` is the operator surface).
The read surface becomes a state report at `GET /state` — what is running,
both demand signals' activity, queue counts, `gpu_contended`, current
timers — operator-only via the loopback surface (Q7); it doubles as the
healthcheck target replacing `/mode`, carrying a `last_pass_at` timestamp
so loop liveness is observable in the health payload itself. The capture
tool renders nothing: its mode UI is removed, not replaced — Q7's
zero-gateway-surface ruling supersedes any client-facing status view. The
punt is debt-free:
a pin is one more input to the Q1 pure function, the converger and loop
are unchanged, the state report is an extensible object so fields grow
without breaking consumers, and the internal API already mutates state (Q5
timers), so mutation plumbing exists regardless. Re-adding pins later
costs exactly what adding them now would. The state report ships as an
open object; the `"pin": null` placeholder once proposed here is dropped —
its only justification was a client contract Q7 deleted (a planning-review
observation). Note that
hardwired localization-always-wins (S3, S11) already collapses the pin
space: a pin-localizer is the only coherent override, and a
pin-reconstructor against active traffic is the knob that rule forbids.

### Q7 — Network surface, auth, and Retry-After

The `/gpu-mode/*` gateway route exists today and is public. Options:
internal-only with operator access via ssh/exec, or public behind keycloak
with an admin role. No-auth lab deployments make a public pin endpoint a
prank vector. Also: where the 503's `Retry-After` value comes from — an API
constant versus the orchestrator reporting measured warm-up time.

**Decision (2026-11-21): zero gateway surface, loopback operator port,
`gpu-policy` verb, orchestrator-owned retry hint, and the name
`gpu-orchestrator`.** The `/gpu-mode/*` gateway route is deleted: nothing
about the orchestrator is publicly reachable in any deployment mode, and
client tier-neutrality holds because k8s never had such a route either.
The capture tool's mode UI dies with nothing replacing it — the cross-repo
ripple shrinks to removal, and the client contract is purely the API plus
the 503/`Retry-After` behavior. The orchestrator publishes its HTTP port
bound to `127.0.0.1` only: operator access is being on the host, which is
already root-equivalent through the docker socket bind, so loopback grants
nothing new and refuses to extend trust onto the LAN — the same reasoning
as the lease-server's internal-only binding, one notch stricter. The
operator surface is `uv run gpu-policy status` and `uv run gpu-policy set
--idle-window 30m --poll-interval 30s` against the loopback port (raw curl
documented as the underlying form); `gpu-mode` retires with the dead
"mode" vocabulary. Operators are host-side by construction — the repo
checkout that ran `boatyard up` is where the verbs live. Contention stays
values-only, mutated through values + `boatyard up`: symmetry of
visibility, not mutation (`status` reports it; `set` cannot touch it) —
the wrong direction OOMs the box, a live flip evaporates on reboot into a
mystery, and no user story wants it. The 503's `Retry-After` is
orchestrator-owned: the null `/localizer-address` response carries
`retry_after_seconds` (a configured default initially, measured
start-to-healthy later if ever), and the API echoes it into the header —
one additive JSON field on an existing internal response, no new API
settings, never generated on k8s where the null path cannot occur. The
service is named `gpu-orchestrator` — directory, compose service, and
image alike — joining the `gpu_contended`/`gpu-policy` family,
disambiguating from the historical "orchestrator service" the lease
system's docs record as collapsed, and following the workloads
domain-qualifier-plus-role pattern. The loopback publish rides
`boatyard.yml`'s root config `ports:` with `host_ip: 127.0.0.1` (the
api/lease-server debug-port precedent), materialized at `up` — the
committed compose artifact stays port-free and the zero-published-ports
test invariant stands; host port 5687. Settled by the planning review
(2026-11-21), previously ripples: the `localizer-router` score resource
type does not rename (it names the routing seam, the permanent
tier-neutral abstraction — its outputs stay accurate and the k8s twin
would be misnamed by any orchestrator-flavored type); `GPU_MODE_MANAGED`
renames to `LOCALIZER_ROUTER_MANAGED` (env, score files, api settings,
k8s generation test — atomic across score and code); and the
`/server-info` field `gpu_mode_managed` is dropped on this branch before
merge — the field is two days old and unmerged with no released reader,
and its absence is itself the capability-off signal a gate-checking
client needs, so the dead vocabulary never reaches a merged release (one
api client regen rides the initiative).

### Q8 — Boot behavior at `gpu_contended: false`

Keep the autostart annotations and let the orchestrator start both (one code
path) versus drop the annotations and let `up` start them at
`gpu_contended: false` (one less dependency, two paths).

**Decision (2026-11-21): annotations unconditional — the orchestrator is
always the starter.** `boatyard/autostart: "false"` stays static on both
GPU workloads regardless of contention: `up` always creates them stopped,
and the gpu-orchestrator's first reconcile tick starts what the policy
wants, both containers on a big card, one on a contended box. One code
path for every deployment. The conditional-holding alternative would need
values-driven annotation templating in the score tier or new boatyard
capability, cross-repo machinery plus two boot paths to document and test,
to save a few hundred milliseconds of boot. (Reasoning note: the
"new boatyard capability" cost carries less weight now that the
first-party principle is explicit — boatyard changes are on the table. The
conclusion survives on its own merits regardless: one boot path, no
conditional annotations, the orchestrator always the starter.) The accepted cost, named: at
`gpu_contended: false` the orchestrator is a boot-ordering dependency for
GPU function. Bounded to the boot window — containers keep running if the
orchestrator dies later, actuation-only control — and a down orchestrator
degrades the router seam regardless of how boot went. Same dependency
class as the gateway being down.

### Deferred by name

Reading container healthcheck status inside the loop; adaptive warm-up
measurement; generalizing beyond two managed services. Say no to all three
until something hurts.

## Rejected alternatives

- **Both GPU workloads auto-start with no arbiter** — the pre-branch stack;
  silent OOM under real scarcity. Returns as the *correct* behavior at
  `gpu_contended: false`, which is the point: arbitration only where the
  hardware forces it.
- **API POSTs demand notifications to the orchestrator** — proposed mid-session
  and retracted. It has no k8s counterpart (KEDA polls the queue; the
  activator sits on the request path; nothing in a k8s product pokes the
  control plane), and it makes the API platform-aware, the exact coupling
  the router seam exists to prevent.
- **Orchestrator queries Postgres directly for queue depth** — the demand
  predicate encodes lease-state semantics the lease-server owns; a config
  SQL string rots silently and fails plausible; a database driver and
  credentials enter a platform component that needs neither; the private
  arrangement dies with the compose orchestrator instead of leaving a seam
  behind.
- **Kafka (or any event log) replacing the lease-server** — wrong pattern:
  a durable ordered log for high-volume fan-out applied to a claim
  coordinator over Postgres rows, at dozens of jobs per day. Enormous
  carrying cost, two stores of truth, and no lease/visibility-timeout
  semantics without building them beside Kafka anyway.
- **Growing the orchestrator into a general compose control plane** — health
  management, restart supervision, general placement. Docker restart
  policies own restarts; its entire jurisdiction is "N GPU workloads,
  capacity K < N, who runs". Rebuilding kubelet badly is the failure mode.
- **Compose profiles** — rejected in the predecessor ADR (Q3 there), stays
  rejected.

## Carrying costs

- The orchestrator container holds the docker-socket bind (the one sanctioned
  scoped bind exception; the socket-proxy upgrade path stays as recorded in
  the predecessor ADR's Q12).
- One more always-on service; policy bugs manifest as GPU flapping — the
  idle window is the only flap protection, by design (Q5).
- The config surface grows: capacity and timers — the managed set is code
  per Q2's final form.
- Cross-repo ripple: the capture tool removes its mode UI (and any
  `gpu_mode_managed` read); nothing replaces it.

## See also

- [design/gpu-orchestration.md](design/gpu-orchestration.md) — the
  predecessor ADR, complete and landed; its decisions of record (Q2
  transition semantics, Q3 selective start, Q12 Docker SDK) carry forward.
- [workloads/gpu-orchestrator/AGENTS.md](workloads/gpu-orchestrator/AGENTS.md) —
  the shipped service.
- [workloads/AGENTS.md](workloads/AGENTS.md) — service inventory, the lease
  system, the 30-minute lease reaper.
- [workloads/api/src/routers/localizer_router.py](workloads/api/src/routers/localizer_router.py)
  — the API side of the routing seam.
