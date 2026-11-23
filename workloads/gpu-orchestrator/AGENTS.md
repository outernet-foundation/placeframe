# gpu-orchestrator/

## What this is

The compose-only GPU control plane: a demand-driven reconcile loop that decides which
GPU workload runs and converges the containers to that decision. It replaces the v1
mode switcher — there is no mode vocabulary anywhere: no `POST /mode`, no `/gpu-mode/*`
gateway route, no `gpu-mode` verb. A compose-only score workload
(`stack/score/gpu-orchestrator.yaml`) carrying the `boatyard/docker-socket` annotation;
it is absent from the k8s rendering, where KEDA/scheduler own activation. This file
describes the shipped behavior.

## Shape

```
src/gpu_orchestrator/
|-- settings.py        pydantic-settings; boot values below the floors clamp with an Error log
|-- orchestrator.py    the control plane: the Orchestrator class (the reconcile loop and Docker
|                      actuation over instance state) and the demand predicates
`-- main.py            the Litestar surface: wire models, routes, bootstrap and compose
                       discovery; delegates to the Orchestrator held in the module-global
                       `_orchestrator`
```

The split is one behavior class over one state object: `orchestrator.py` defines
`Orchestrator`, which owns the loop and the actuation, and `main.py` is the HTTP
surface plus bootstrap delegating to it. `bootstrap` (in `main.py`) validates
`Settings`, discovers the compose project, builds one `BootState` dataclass (docker
client, compose project, queue-poll httpx client, both service URLs, the runtime
timer values), constructs the `Orchestrator` from it, stores it in the
module-global `_orchestrator`, and starts the loop task on `app.state`; every
handler first passes the unconfigured guard, which raises until bootstrap has run.
The loop state — queue sample, heartbeat, last-pass stamp, poll cadence, hint
edge, poke event — lives as public instance attributes on the `Orchestrator`, and
the timer values mutate `BootState` in place (PATCH rewrites
`idle_window_s`/`poll_interval_s`; everything else is fixed at construction). The
clock is constructor-injected (`Callable[[], float]`, default `monotonic`): tests
drive time through a fake clock, not monkeypatching. `require_managed_pair` is a module
function in `main.py` beside `bootstrap` (its only production caller), the two demand
predicates (`localization_demand_active`, `reconstruction_demand_active`) are zero-arg
query methods on the `Orchestrator` reading the cached heartbeat age and queue sample
where they live, and `orchestrator.py` never imports from `main.py`. `BootState` is a plain dataclass,
not a pydantic model: nothing validates it, because everything in it was already
validated at `Settings` parse time. The other classes are pydantic input-validation
models — `QueueSample` doubles as the wire validation of the lease-server's
`/queue-state` response and the domain value the loop caches.

- **The loop** — one background task started at boot (`bootstrap` starts
  `Orchestrator.run_forever`). Each pass
  refreshes the queue sample on the poll cadence, computes the desired set from the
  truth table inline in the pass, and converges the diff. Boot repair is the first tick — there
  is no separate repair path. The wait between passes is an `asyncio.Event` with timeout
  at the poll interval; `/localizer-address` sets the event so the interactive path
  reacts in milliseconds. Pokes are never load-bearing: poke-triggered passes reuse the
  cached queue sample, and deleting the poke degrades to plain periodic behavior.
- **Demand inputs** — localization demand is the router seam: every `/localizer-address`
  query is a heartbeat, null answer or not, and stays active for the idle window. The
  heartbeat clock is in-memory and dies at orchestrator restart — a fresh process must
  observe demand itself (observed live: a restart mid-traffic re-arbitrates from scratch).
  Batch demand is the queue seam: plain-httpx `GET /queue-state` on the lease-server
  (`queued > 0 OR in_flight > 0`, computed here — the endpoint is a dumb attribute read).
  Poll failure holds the last successful sample with an Info log; reading "unreachable"
  as no-demand would preempt a running reconstruction during every lease-server restart.
  The cached sample is never null: it starts as a zero sample at boot (no batch demand,
  reported as `queued: 0, in_flight: 0` in `/state`) and only a successful poll overwrites it.
- **Policy** — inline in the pass, with the two demand predicates
  (`localization_demand_active`, `reconstruction_demand_active`) as zero-arg query
  methods on the `Orchestrator`: contended: localizer iff localization demand active, else reconstructor iff
  batch demand, else localizer (a warm front door; localization always wins when demand
  exists). Uncontended: all managed — the no-op is emergent, drift repair still runs in
  both modes. Under contention, held-out demand logs a one-line hint naming
  `GPU_CONTENDED` once per rising edge, never per tick.
- **Actuation** — the managed pair is hardcoded (`localizer`, `reconstructor` constants
  in `orchestrator.py`): config that can only be changed by also changing code is indirection,
  not config. Containers are matched by the automatic `com.docker.compose.service`
  label within the compose project injected as the `COMPOSE_PROJECT_NAME` env —
  the config provisioner's `${COMPOSE_PROJECT_NAME:-}` passthrough, which compose
  resolves from the project name it was invoked with, so the launcher is the
  authority on which assembly this orchestrator belongs to. The orchestrator never
  identifies its own container, and boot requires the managed pair to exist in the
  injected project before the loop starts. Stop-first ordering
  frees the GPU slot before the winner starts; transitions
  serialize and run to completion inside their pass. The localizer (interactive class)
  drains ~700 ms before stopping; the reconstructor (batch class) stops with
  `stop(timeout=60)` so a future checkpoint-on-SIGTERM fits the budget — docker's 10 s
  default would SIGKILL mid-checkpoint (until checkpoint/resume lands, preemption
  costs the reconstructor's SIGTERM requeue-and-restart, which is exactly the shipped
  behavior).
- **The HTTP surface** — `GET /localizer-address` → `{address, retry_after_seconds}`
  (the field is meaningful only on the null answer); contractually reserved to the
  API's localize path — nothing else may poll it. `GET /state` → open object (running
  set, demand signals, queue counts, timers, `last_pass_at`) and doubles as the
  healthcheck. `PATCH /policy` → the two timers, floors enforced (window ≥ 60 s,
  poll ≥ 5 s, 400 below), every mutation logged old→new; overrides are in-memory only
  and evaporate at restart — values is truth at boot. Contention is values-only:
  `status` reports it, `set` cannot touch it. Nothing is gateway-reachable; the
  operator surface is the loopback publish (host 127.0.0.1:5687, from the root
  config's `ports:`) and `uv run gpu-policy {status|set}`.

## Constraints

- **The values knobs** — `GPU_CONTENDED` (default true — the hardware fact "only one
  managed workload fits"), `GPU_IDLE_WINDOW_S` (600), `GPU_POLL_INTERVAL_S` (15),
  `GPU_RETRY_AFTER_SECONDS` (60), all in `boatyard.values.yaml`'s flat list with
  `${VAR:-default}` slots in the placeframe-config outputs.
- **All container lifecycle is the Docker SDK** — start/stop/wait on existing
  containers; the orchestrator never creates containers. Both GPU workloads carry
  `boatyard/autostart: "false"`: `up` always creates them stopped and the loop's
  first tick starts what the policy wants, one code path in every deployment — which
  makes the orchestrator a boot-ordering dependency for GPU function, bounded to the
  boot window (actuation-only control: containers keep running if it dies later).
- **The docker-socket bind is root-equivalent.** The one sanctioned scoped-bind
  exception in the compose artifacts; operator access is being on the host, which the
  socket bind already makes root-equivalent — the loopback-only publish grants nothing
  new and refuses the LAN.
- **A running localizer container is not a serving localizer.** `/localizer-address`
  answers non-null as soon as the container runs; the model-load warm-up window after
  a swap can still fail proxied requests. Reading container healthcheck status inside
  the loop and measured warm-up are deferred — the 503 +
  `Retry-After` contract covers the null-address window only.

## See also

- `stack/score/gpu-orchestrator.yaml` — the workload declaration.
- `workloads/api/src/routers/localization.py` — the API side of the
  `/localizer-address` contract and the 503 + `Retry-After` echo.
- `scripts/src/scripts/gpu_policy.py` — the operator verb.
