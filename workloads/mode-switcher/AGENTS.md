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

- `GET /mode` — the current mode, `localization` | `reconstruction`.
- `POST /mode` — switch: drain ~700 ms for in-flight localization before stopping the
  localizer; interrupt a running reconstruction immediately (its SIGTERM requeue is
  purpose-built). Stop the current GPU container, `.wait()` for exit, start the other.
- `GET /localizer-address` — `{"address": "http://localizer:8000"}` when the localizer is
  running, `{"address": null}` when not. The API's localization proxy calls this per
  request (`workloads/api/src/routers/localizer_router.py`); a client-facing UI reads the
  mode over the gateway's public `/gpu-mode/*` route (prefix stripped at the edge).

Boot reconciliation: at start, inspect the GPU containers and adopt the running one's
mode as current — both running → keep the default, stop the other; none running → start
the default (`localization`; AR tracking is the time-sensitive case, reconstructions
queue). Container state is the source of truth; no persisted mode.

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
