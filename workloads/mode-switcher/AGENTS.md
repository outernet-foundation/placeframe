# mode-switcher/

## What this is

The compose-only GPU mode switcher: the always-on container that owns which GPU workload
holds the machine's single GPU slot. The localizer and reconstructor cannot coexist in
VRAM; exactly one runs, and this service is the user-facing toggle between them. It is
not a score workload — the compose provisioner for the `localizer-router` resource type
emits it (`stack/score/compose/localizer-router.yaml`); it is absent from `boatyard.yml`'s
workloads list and from the k8s rendering, where both GPU workloads run on separate GPU
nodes and the k8s provisioner twin is outputs-only.

## Shape

One module, `src/mode_switcher/main.py` — state, Docker logic, and routes in a
single file (no routers/ package, no settings module; the default mode is a
constant, not a deployment knob). State is module-level: the write-once
`_client`/`_project` pair and the boot repair (both inside `initialize()`,
run once from bootstrap), the `_transition` marker, and the two locks
(`_switch_lock` serializes whole switch sequences, `_flag_lock` guards the
marker for microseconds so mode reads never block behind a switch).

- `GET /mode` — the current mode, `localizer` | `reconstructor`: the compose
  service names themselves, one vocabulary end to end. The mode is derived
  from container state at read time; a single running container is the mode,
  and the transition marker answers the target while a switch is in flight.
  Zero or two running encode no mode and answer the default.
- `POST /mode` — switch (converge): stop the other GPU container if it runs
  (drain ~700 ms for in-flight localization first; an interrupted
  reconstruction requeues — its SIGTERM requeue is purpose-built), `.wait()`
  for exit, start the target if it is not already running. Idempotent.
- `GET /localizer-address` — the localizer's compose-network URL (from the
  `LOCALIZER_URL` env, injected by the provisioner and templated from the
  localizer workload's own `service.ports` declaration — no copied port) when the
  localizer is
  running, `{"address": null}` when not. The API's localization proxy calls this per
  request (`workloads/api/src/routers/localizer_router.py`); a client-facing UI reads the
  mode over the gateway's public `/gpu-mode/*` route (prefix stripped at the edge).

Boot repair (inside `initialize()`, run once from bootstrap): inspect the GPU
containers — both running → stop the non-default; a single one running → adopt
it; none running → start the default (`localizer`; AR tracking is the
time-sensitive case, reconstructions queue). Container state is the source of
truth; no persisted mode, no remembered mode at all.

## Constraints

- **All container lifecycle is the Docker SDK** — start/stop/wait on existing containers
  found by compose labels (`com.docker.compose.service` in `{localizer, reconstructor}`).
  No shell-out, no CLI output parsing. The compose project label is discovered from the
  switcher's own container labels — per-entry compose projects are entry-prefixed (e.g.
  `placeframe-core-cuda`), so no fixed project name matches.
- **The containers it manages exist created-stopped from `boatyard up`** — both GPU
  workloads carry `boatyard/autostart: "false"` (see `stack/AGENTS.md`); the switcher only
  ever starts/stops existing containers, never creates them.
- **The docker-socket bind is root-equivalent.** The service mounts
  `/var/run/docker.sock` (the one sanctioned bind in the compose artifacts); the input
  surface is one enum-validated POST with constant service names — the audited trade and
  the socket-proxy upgrade path are `design/gpu-orchestration.md` Q12.
- Mode switching never routes through the API — clients POST this service directly via
  `/gpu-mode/mode`; the operator verb is `uv run gpu-mode` (`scripts/AGENTS.md`).

## See also

- `design/gpu-orchestration.md` — the ADR (transitions, boot semantics, rejected
  alternatives).
- `stack/score/compose/localizer-router.yaml` — the provisioner emitting this service.
- `workloads/api/src/routers/localizer_router.py` — the API side of the
  `/localizer-address` contract.
