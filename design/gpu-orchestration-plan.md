---
updated: 2026-11-19
---

# GPU orchestration — execution plan

Execution plan for [gpu-orchestration.md](gpu-orchestration.md) (the ADR; all
decisions of record live there). The ADR describes the what and why; this doc
sequences the how. Mechanism references below are grounded at branch
`gpu-orchestration`, `47b6cfaa` and will drift.

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

## External dependency and a fork the ADR left closed

The ADR's Q3 (as amended) commits to a separate autostart annotation —
`boatyard/autostart: "false"` marks a service created-stopped at `up`
rather than started — and to boatyard `up` gaining selective-start
(`docker compose up -d --no-start` then `docker compose start` for
un-annotated services only). The gpu annotation and its patch
templates are untouched: they keep keying on `"true"` exactly as released.
The ADR's code-verification note had flagged the pre-amendment design's
template-value change as "unverifiable from this repo"; the amendment
dissolves that dependency — there is no template change to verify. What
remains is a namespace fork the amendment does not touch:

- **Released boatyard 0.8.0** (installed in placeframe's venv,
  `scripts/pyproject.toml` pins `boatyard>=0.8`) keys the gpu templates on
  `boatyard/gpu`. placeframe's three `boatyard/gpu` spellings
  (`stack/score/localizer.yaml:5`, `stack/score/reconstructor.yaml:7`, the
  generated echo `stack/generated/compose/compose.core-cuda.yaml:120`)
  match it.
- **Trunk boatyard** (branch `refactor-even-more`, unreleased) has renamed
  the whole annotation namespace `boatyard/*` → `outernet.internal/*`. The
  gpu templates at
  `src/boatyard/score_patch_templates/gpu-{cuda,rocm,pod}.tpl` key on
  `outernet.internal/gpu`; `AGENTS.md` names the rename as policy
  ("Substrate needs live in workload files as `outernet.internal/*`
  annotations").

placeframe consumes boatyard via a **path reference** on the local
`/workspace/boatyard/` checkout for this initiative — no boatyard publish
or push is required to validate the changes. The autostart annotation +
selective-start land on whichever branch the local checkout carries, and
the placeframe-side delta differs by world:

- **World A — backport on the `boatyard/*` namespace.** The autostart
  annotation and selective-start land on a branch off the released line
  (which keeps `boatyard/*`). placeframe's gpu annotations stay untouched;
  the two GPU workloads each set `boatyard/autostart: "false"`. No
  annotation-namespace migration.
- **World B — ride the `refactor-even-more` branch.** The change lands on
  trunk, which carries the `outernet.internal/*` rename. placeframe
  migrates every `boatyard/*` annotation in its score files
  (`boatyard/gpu`, `boatyard/probe-adapter`, `boatyard/dockerfile`,
  `boatyard/route`) to the `outernet.internal/*` spelling — and the new
  annotation lands as `outernet.internal/autostart`, one of several, not a
  one-off.

Which world runs is the operator's call (which branch the local boatyard
checkout points at). Phase 1 below produces the boatyard change on that
checkout; phase 5 switches placeframe's `scripts/pyproject.toml` from the
`>=0.8` PyPI pin to a path reference on the local checkout and sets
`boatyard/autostart: "false"` on the two GPU workloads. Phases 2-4 do not
depend on phase 1 and can develop and land against the released boatyard —
no autostart annotation is authored yet and both GPU containers auto-start,
with the mode switcher reconciling the dual-start (the ADR's Q3 option
(b), rejected as the end state but acceptable as an intermediate, since
the mode switcher's boot reconciliation is strictly better than today's
silent OOM). Phase 5 is what activates selective-start and closes the
boot-race gap.

## End state

Once the last phase lands, all of the following hold. Each phase cites the
subset it delivers.

- A compose-only mode switcher container tracks the current mode
  (`localization` | `reconstruction`), exposes `GET /mode`, `POST /mode`,
  and `GET /localizer-address`, starts/stops GPU containers by compose label
  via the Docker SDK, and reconciles container state at its own boot
  (adopts the running GPU container's mode, stops extras). Default mode at
  boot: localization.
- The mode switcher is emitted by the compose provisioner for the
  `localizer-router` resource type (`stack/score/compose/localizer-router.yaml`),
  not authored as a score workload, not in `boatyard.yml`'s workloads list.
  The k8s provisioner (`stack/score/k8s/localizer-router.yaml`) is
  outputs-only: `address: http://localizer:8000`, `managed: "false"` — no
  service emitted, no stub, no extra hop.
- `boatyard up` creates all containers stopped (`docker compose up -d
  --no-start`), starts everything but the two held GPU workloads, and the
  mode switcher starts the default-mode
  GPU container. No dual-start race. Raw `docker compose up` starts both
  GPU containers — documented caveat, use `boatyard up`.
- placeframe consumes boatyard via a path reference on the local checkout
  (reverts to a `>=0.9` version pin when boatyard publishes the autostart
  annotation + selective-start changes — the 0.9 floor is the capability
  declaration).
- The API consumes `${resources.localizer-router.address}` and
  `${resources.localizer-router.managed}`. When `managed: true`, it queries
  `<address>/localizer-address` at request time and forwards to the
  returned address or returns 503 "Localization unavailable" on null. When
  `managed: false`, it forwards directly to `<address>` (the localizer,
  always-on). The opaque 502 collapse is gone.
- `/server-info` reports `gpu_mode_managed: bool`. The client (capture
  tool) reads it to decide whether to show the mode UI and call
  `<backendUrl>/gpu-mode/mode`.
- `uv run gpu-mode {localization|reconstruction}` POSTs the mode switcher
  via the public `/gpu-mode/mode` path.
- The gpu annotation stays `"true"` on both GPU workloads (substrate only,
  the patch templates unchanged); `boatyard/autostart: "false"`
  (or `outernet.internal/autostart`, per world) on both holds them out of
  `up`'s start step. Escape hatch: remove the annotation (absence = today's
  auto-start behavior).
- Localizer, reconstructor, lease-server: zero code changes.
- `scripts/tests/test_score_compose_generation.py`: `CORE_SERVICES` gains
  `mode-switcher`; the bind assertion permits exactly `/var/run/docker.sock`
  on exactly the `mode-switcher` service; the profiles assertion is
  unchanged (no profiles anywhere).

## Phases

### 1. boatyard: autostart annotation + selective-start (external)

Complete, 2026-11-17 — re-executed the same day on the ADR's
split-annotation amendment (the first pass made `managed` a gpu-annotation
value and widened the gpu template guards; the redo leaves the templates
byte-identical to the released line) and renamed once more to the
behavior-named `boatyard/autostart: "false"` ("managed" named the
consumer's motivation — an external orchestrator — which boatyard can
neither see nor enforce; the annotation's whole contract is whether the
container starts at `up`). boatyard branch `gpu-managed`
(World A: off the released line, `boatyard/*` namespace kept — confirmed:
pushed and merged into boatyard `dev` via PR #36, `837be6c`): one code
commit `06882a7` (the autostart-annotation selective start, the
pinned-compose test-binary cache, the compose_command dissolution with
quoting in `temp.py` as `quote_command_token`, and bundle records —
held services and declared ports — carried on the assembly plan, the
plan carrying the config; version 0.9.0 — the lock format grew, so
consumers relock once), then one AGENTS.md prose commit, tip `17d038c`.
Facts the later phases rely on: the gateway
project stays one-shot `up -d` (no annotation can appear in a document
boatyard itself renders, so the two-step applies to bundles only); docker
compose v5's `start` honors `depends_on` health/completion conditions and
starts only the listed services' dependency closures (verified empirically
— the `wait-for-resources` gating survives selective-start, and a `start`
naming the unheld services leaves the held containers
created-stopped); `up` parses no bundle text — every record (services,
routes, ports, container names, held services, declared ports) rides the
plan, extracted at relock for remote bundles and at resolve for local and
override bundles (placeframe's GPU workloads are local: the annotation
flows at resolve, no relock).

Produced at `/workspace/boatyard/` (the bind mount, not a fresh clone).
Merged to boatyard `dev` (PR #36); no PyPI release yet — until 0.9.0
publishes, placeframe still needs the phase 5 path reference (or pin the
merged dev line).

- `src/boatyard/verbs/up.py` (`_orchestrate_up`): after materializing the
  compose file, run `docker compose up -d --no-start` (creates all
  containers stopped, env slots resolved), then `docker compose start` for
  every bundle-recorded service except the held ones. Any service can be
  held, gpu or not. GPU containers exist, stopped, from boot. This is
  `up` logic, not a patch template.
- `src/boatyard/lock.py` + `src/boatyard/resolve.py`: the bundle-record
  extraction (`extract_bundle_records`) collects `held_services` and
  `declared_ports` in the same walk as services/routes/ports — baked into
  `boatyard.lock.yml` at relock for remote bundles, extracted from the
  rendered bundle text at resolve for local and override bundles, adopted
  onto `BundleProject` either way (fields defaulted, so pre-annotation
  locks parse unchanged).
- The gpu patch templates (`gpu-cuda.tpl`, `gpu-rocm.tpl`, `gpu-pod.tpl`)
  are untouched — they keep keying on `"true"`.
- Tests in boatyard's suite: `up`'s selective-start skips the
  lock-recorded held services and starts the rest; the extraction holds a
  service marked `boatyard/autostart: "false"` (the flipped-polarity
  guard); gpu annotation values in bundle text do not gate the start step
  (the decoupling regression guard).
- `AGENTS.md` (boatyard): the substrate-annotation bullet names the gpu
  annotation (`"true"`, substrate only, the patch templates its reader)
  and the separate autostart annotation (start behavior, recorded in the
  bundle records as held services). Prose commit.

Verification: boatyard's own lint/type/test battery + preflight. The change
is not consumable from placeframe until phase 5 switches the dependency to
a path reference on this checkout.

Commit: code commit + prose commit (AGENTS.md). No push — the changes
live in the local checkout that phase 5's path reference points at.

### 2. Mode switcher workload

Complete, 2026-11-19 — one code commit `9767028d` ("Add the mode-switcher
workload"), preceded by a canonical `Run generate-clients` (`682b55ac`) for
staleness pre-existing on `origin/dev` (the `successful` field on
`ReconstructionMetrics` in placeframe-core landed there without a regen;
preflight's hard gate required it, and it is unrelated to this phase's
surface). Executed deviations from the text below, all forced by the plan's
own `src/mode_switcher/` layout, which contradicts the `src.main:app`
uvicorn target borrowed from lease-server: the package is an installable
hatchling package (the s3-initializer shape, so the tests import
`mode_switcher` from the workspace venv), the uvicorn target is
`mode_switcher.main:app`, and boot reconciliation runs in an `on_startup`
hook appended after `create_litestar_app` (which does not forward hooks),
with handlers receiving the switcher via Litestar `State` injection and the
Docker SDK calls wrapped in `asyncio.to_thread`. The root `testpaths` gained
`workloads/mode-switcher/tests` so preflight's plain pytest runs them (the
s3-initializer precedent). Compose project label
`com.docker.compose.project=placeframe` confirmed against `boatyard.yml`'s
`project_name`. Full battery + preflight green.

The service itself, standalone-verifiable. Not yet wired into the stack
(phase 3 wires it); the workload exists at `workloads/mode-switcher/` with
its Dockerfile, pyproject, entrypoint, and unit tests against a mocked
Docker client.

- `workloads/mode-switcher/` (new), mirroring the lease-server shape
  (`workloads/lease-server/`):
  - `Dockerfile` — the standard `ARG UV_BASE_IMAGE` multi-stage shape; no
    `packages/generated/datamodels` COPY (no DB dependency).
  - `entrypoint.sh` — `uvicorn src.main:app --host 0.0.0.0 --port 8000`
    with `RELOAD`/`DEBUG_*` toggles, matching lease-server's entrypoint.
  - `pyproject.toml` — `placeframe-common`, `litestar`, `uvicorn[standard]`,
    `pydantic`, `docker` (the SDK, per ADR Q12). No `[project.scripts]`
    (run via uvicorn, like lease-server).
  - `src/mode_switcher/main.py` — the Litestar ASGI app
    (`create_litestar_app([router], openapi_config)`, mirroring
    `workloads/lease-server/src/main.py:12`).
  - `src/mode_switcher/routers/mode.py` — `GET /mode` (returns the current
    mode), `POST /mode` (sets mode: SIGTERM the current GPU container →
    `.wait()` → `.start()` the other; Q2 transition semantics: wait
    ~700ms for in-flight localization before SIGTERM, interrupt
    reconstruction immediately), `GET /localizer-address` (returns
    `{"address": "http://localizer:8000"}` when the localizer container is
    running, `{"address": null}` when not).
  - `src/mode_switcher/docker_lifecycle.py` — Docker SDK container
    operations: find GPU containers by compose labels
    (`com.docker.compose.service` in `{localizer, reconstructor}`,
    `com.docker.compose.project=placeframe`), `.start()` / `.stop()` /
    `.wait()`, `.status` for boot reconciliation. No shell-out, no CLI
    output parsing (ADR Q12 decision (a)).
  - `src/mode_switcher/settings.py` — `pydantic-settings`: `default_mode`
    (`Literal["localization", "reconstruction"]`, default `localization`).
  - Boot reconciliation (ADR Q3 sub-decision): at boot, inspect existing
    GPU container state; adopt the running GPU container's mode as current,
    stop any extras. Container state is the source of truth; no persisted
    mode state.
- `tests/` — unit tests against a stubbed Docker client: mode switch
  (stop→wait→start), boot reconciliation (one running → adopt; both running
  → adopt default, stop other; none running → start default),
  `/localizer-address` null/non-null, transition semantics (wait for
  localization, interrupt reconstruction).

Verification: ruff/pyright/pytest. The workload is not in the stack yet —
verify via `uv run pytest workloads/mode-switcher/tests/`.

Commit: one code commit.

### 3. Provisioner pair + score wiring + test invariants

Complete, 2026-11-19 — replayed onto `gpu-orchestration` after boatyard
0.9.1 published the host-binds change (branch `host-binds`, merged; the
relock is `ee5c30b1`, the replayed source `2a77d673`, the regen
`078a1e07`; the published 0.9.1 regenerates the committed artifacts as a
byte-identical no-op). Execution discovered two things the plan's text
got wrong, both fixed in the landed source: the route entry needs
`,strip` (`/gpu-mode/*=mode-switcher:8000,strip` — without it the gateway
forwards the prefixed path and the switcher 404s; keycloak's `/auth/*` is
the strip precedent), and phase 2's `ModeSwitcher` hardcoded
`com.docker.compose.project=placeframe`, which matches nothing at runtime
(per-entry projects are `placeframe-core-cuda` etc.) — the switcher now
discovers the project from its own container labels
(`attrs["Config"]["Labels"]`, since typeshed's docker stubs leave
`Container.labels` unannotated), landed as `6ef2b10c`. The docker-socket
bind required the boatyard 0.9.1 host-binds change (repo-relative bind
sources inline as configs content, absolute sources are authored host
mounts that pass through — the alternative spellings are dead ends: a
named volume with local-driver `o: bind` opts renders but fails at
create, "not a directory", because the local driver cannot bind a single
socket file onto its pre-created `_data` dir). A second candidate defect
— the gateway one-shot `up -d` not recreating on Caddyfile change — was
ruled a known compose limitation, not a boatyard defect (compose 5.1.3
does not recreate on `configs.content`-only change; operational
consequence: route changes need a manual gateway recreate). Verified
end-to-end twice (venv-patched boatyard at execution, published 0.9.1 at
replay): mode-switcher healthy in `docker compose ps`, the barrier gates
on it, `curl localhost:8443/gpu-mode/mode` →
`{"mode":"localization"}`, `/gpu-mode/localizer-address` → the address,
the socket sees the GPU containers under the discovered project, boot
reconcile stops a left-over extra, and a POST toggle cycle exercises the
real SIGTERM → wait → start lifecycle both directions. Both GPU
containers still auto-start at `up` (the accepted intermediate, Q3
option (b)) until phase 5's annotations.

Wires the mode switcher into the compose stack. The mode switcher now
exists in `docker compose ps`, the gateway routes `/gpu-mode/*` to it, and
the score generation tests assert its presence. The API is unchanged (still
consumes `LOCALIZER_CONTAINER_URL` via the `localizer` service-port
resource, which stays for now).

- `stack/score/compose/localizer-router.yaml` (new) — the compose
  provisioner, following the seaweedfs pattern (`stack/score/compose/seaweedfs.yaml`):
  - `type: localizer-router`
  - `outputs`: `address: http://mode-switcher:8000`, `managed: "true"`
  - `services`: `mode-switcher` — `image: {dockerfile:
    workloads/mode-switcher/Dockerfile}`, the docker-socket bind
    (`/var/run/docker.sock` authored directly in the service's `volumes:`
    as `type: bind`, per ADR Q3 — provisioners author full compose service
    definitions including `volumes:`), env from `boatyard.values.yaml` as
    needed, healthcheck on `/mode`.
- `stack/score/k8s/localizer-router.yaml` (new) — the k8s twin,
  outputs-only (ADR Q10): `type: localizer-router`, `outputs: {address:
  http://localizer:8000, managed: "false"}`, no `manifests:`, no services.
  The asymmetric pair (compose emits a service, k8s emits only outputs) is
  a new shape — ngrok's no-twin is the closest precedent, but this carries
  a k8s stub for output resolution.
- `stack/score/api.yaml:4-8` — add `/gpu-mode/*=mode-switcher:8000` to the
  `boatyard/route` annotation (before the `/*=api:8000` catch-all). The
  gateway now routes the public path prefix to the mode switcher.
- `stack/score/api.yaml:53-65` — declare `localizer-router` resource
  (`type: localizer-router`, `id: placeframe-localizer-router`) alongside
  the existing `localizer` service-port. The API does not consume its
  outputs yet (phase 4 does); declaring the resource triggers the
  provisioner pair to ship.
- `scripts/tests/test_score_compose_generation.py:10-27` — add
  `"mode-switcher"` to `CORE_SERVICES`.
- `scripts/tests/test_score_compose_generation.py:54-55` — move the bind
  assertion from blanket to scoped: permit exactly `/var/run/docker.sock`
  on exactly the `mode-switcher` service. The profiles assertion (`:52`) is
  unchanged.
- Regen: `uv run generate-score`. Canonical `Run generate-score`.

Verification: battery + preflight (the `generate-score --check` in CI's
build-docker getter gates staleness separately; preflight's score test
asserts structure). Manual: `uv run boatyard up --quiet-pull`, then
`docker compose ps` shows `mode-switcher` running, `curl
localhost:8443/gpu-mode/mode` returns `{"mode": "localization"}`,
`docker exec` confirms the mode switcher can see GPU containers via the
socket. This phase's verification is the one mandatory end-to-end pass for
the mode switcher's presence.

Commit: source commits, then canonical `Run generate-score`.

### 4. API integration + CLI verb

Complete, 2026-11-19 — one code commit `60537b7c`, then canonical regens
`783bfc61` (`Run generate-clients`) and `0f260137` (`Run generate-score`;
see deviations). The battery + full preflight green. Executed deviations
from the text below, all recorded in the landed source: (1) the phase
regenerates the score artifacts too — the plan's regen table listed only
lock + clients, but the `api.yaml` env/resource change bakes literals
into all three artifacts and `test_score_k8s_generation.py` asserts the
committed k8s artifact, so the staleness gate forces `Run generate-score`
at this boundary, not at phase 5's; (2) `localizer_router_address` is a
required `Field()`, not `AnyHttpUrl | None = None` — the replaced
`localizer_container_url` was required, every tier's provisioner always
provides the router outputs, and required keeps a missing wire a loud
boot error rather than a request-time crash; (3) the resolver lives in a
new leaf module `workloads/api/src/routers/localizer_router.py` (the
`localization_maps.py` sibling-helper precedent) exporting
`resolve_localizer_address` + `UNAVAILABLE_DETAIL` — `localization.py`
transitively imports `src/database.py`, whose module-level `get_settings()`
crashes import outside a provisioned env, and the leaf module is what
makes the router-query branch unit-testable; `localization.py` dropped
its module-level `settings` global in the move; (4) the 502→503
replacement is total per the end-state text — the ApiException fallthrough
also raises 503 `Localization unavailable` (the shared constant), not
just the null-address path; (5) `api_auth._read_public_url` is renamed
`read_public_url` (two entry-point modules now consume it; the private
name tripped basedpyright's reportPrivateUsage); (6) the k8s generation
test now asserts `LOCALIZER_ROUTER_ADDRESS`/`GPU_MODE_MANAGED` on the api
Deployment — the plan didn't list it, but that test locks the committed
k8s artifact's mechanics and follows the env swap. The lock-python run
was a no-op (entry-point additions don't touch locks). Unit tests landed:
router-query branch against a real stdlib HTTP stub (address ⇒ forward,
null ⇒ 503, unreachable router ⇒ 503, unmanaged ⇒ direct return with the
stub never queried), server-info handler via Litestar TestClient in both
auth modes, and the CLI verb against a stubbed POST (payload, clean
exit-1 on switcher error, --help lists both modes).

The API stops hitting `LOCALIZER_CONTAINER_URL` directly and starts asking
the router for the localizer address. `/server-info` gains the
`gpu_mode_managed` capability field. The CLI verb lands alongside.

- `workloads/api/src/settings.py` — add `gpu_mode_managed: bool = False`
  and `localizer_router_address: AnyHttpUrl | None = None`. The branch on
  `managed` mirrors the `auth_mode` pattern (config-driven, not platform
  detection — ADR Q5 amendment). Remove `localizer_container_url` (replaced).
- `workloads/api/src/routers/localization.py:72-113` — before forwarding,
  branch on `settings.gpu_mode_managed`: when `true`, query
  `<router_address>/localizer-address`; null ⇒ 503 "Localization
  unavailable"; non-null ⇒ forward to the returned address. When `false`,
  forward directly to `<router_address>` (which is the localizer URL on
  k8s). The 502 collapse (`:113`) is replaced by the 503 path; the 422
  pass-through (`:111`) is unchanged. The `/version` route (`:116-119`)
  gets the same branch.
- `workloads/api/src/routers/server_info.py:9-14` — add
  `gpu_mode_managed: bool` to `ServerInfo`; populate from
  `settings.gpu_mode_managed` in both return paths (`:21` disabled,
  `:23-29` keycloak).
- `stack/score/api.yaml:28` — replace `LOCALIZER_CONTAINER_URL` with
  `LOCALIZER_ROUTER_ADDRESS: ${resources.localizer-router.address}` and
  `GPU_MODE_MANAGED: ${resources.localizer-router.managed}`. Remove the
  `localizer` service-port resource (`:60-65`, now unconsumed).
- `scripts/src/scripts/gpu_mode.py` (new) — typer app, one command taking
  `mode: Annotated[Literal["localization", "reconstruction"],
  typer.Argument()]`. Reads `PUBLIC_URL` (via the `api_auth._read_public_url`
  pattern at `scripts/src/scripts/api_auth.py:36`), POSTs to
  `f"{public_url}/gpu-mode/mode"` with `{"mode": mode}` via `httpx`. Prints
  the outcome. Exit non-zero only on infrastructure failure.
- `scripts/pyproject.toml:37-50` — add
  `gpu-mode = "scripts.gpu_mode:app"` (typer `:app`, per the convention).
- Regen: `uv run lock-python` (new verb registration) then
  `uv run generate-clients --config openapi-client-codegen.yaml` (the API
  OpenAPI gains `gpu_mode_managed` on `ServerInfo` → python + C# clients).
  Canonical `Run generate-clients`.

Verification: battery + preflight (client staleness is the hard gate).
Tests: localization router-query branch (stub the router: address returned
⇒ forward; null ⇒ 503; `managed: false` ⇒ direct forward),
`/server-info` reports `gpu_mode_managed` in both auth modes, `uv run
gpu-mode --help` + unit test of the POST against a stubbed endpoint.

Commit: code commits, then canonical `Run generate-clients`.

### 5. Path-pin boatyard + autostart annotation + selective-start activation

Complete, 2026-11-19 — as the note below reduced it: the two annotations
(`45b83751`), the regen (`839d847e`, `Run generate-score` — amended once to
fix a copy mistake that had landed the k8s manifest at
`stack/generated/manifests.yaml` instead of `stack/generated/k8s/`), and one
follow-up code commit the end-to-end forced (`96762654`): `gpu-mode` failed
against the repo's own values file because `read_public_url` only knew the
literal `public_url`/`PUBLIC_URL` keys while placeframe's values spell it
`public_host` + `public_scheme` — the helper now derives
`scheme://host` from that pair (fit-calibration and tune-reconstruction
inherit the fix). End-to-end verified on the live stack: `boatyard up`
leaves the reconstructor `Created` (held) and the localizer `Up healthy`
— started by the mode switcher, not `up`; no dual-start. `uv run gpu-mode
reconstruction` drains and SIGTERMs the localizer (Exited 143), cold-starts
the reconstructor, and `GET /localize/version` returns 503 while in
reconstruction mode; toggling back reverses both containers and the route
answers 200. One observed behavior recorded: the response body on that 503
reads `{"detail":"Internal Server Error"}` — placeframe_common's shared
exception handler masks every ≥500 detail (`log_http_exception`,
`packages/python/common/src/placeframe_common/litestar.py`) — the status
code is the wire contract and the real detail reaches the api logs; the
client learns "why" from the mode switcher, which is Q5 decision (a)'s
intent. Two build mechanics noted on the way: the moved tree tags had to
be rebuilt with targeted `boatyard build --targets <service>` (the
no-targets form minted a divergent tag set — clean-tree hashes — that
`up`'s working-tree hashes refused), and the annotation rides the k8s
manifest as inert workload-metadata lines (selective-start is compose-only
`up` behavior).

Note (2026-11-19): boatyard 0.9.0 has published to PyPI, and
`scripts/pyproject.toml` already pins `boatyard>=0.9` (bumped on `origin/dev`
by the pg-schema-diff work, `bfa97626`) with `uv.lock` resolving 0.9.0 from
the registry — the path-reference bridge below is moot, and so is the
World A/World B fork's dependency on the local `/workspace/boatyard/`
checkout's branch. This phase reduces to the two autostart annotations +
`Run generate-score`.

Depends on phase 1's changes being in the local `/workspace/boatyard/`
checkout. This is the phase that activates selective-start and closes the
boot-race gap — until it lands, both GPU containers auto-start and the
mode switcher reconciles (Q3 option (b), the intermediate).

- `scripts/pyproject.toml:7` — switch the boatyard dependency from the PyPI
  pin (`boatyard>=0.8`) to a path reference on the local checkout carrying
  phase 1's changes. `uv sync --all-packages` (regenerates the workspace
  `uv.lock` against the local boatyard). This is the bridge that makes
  phase 1's annotation + `up` logic changes consumable from placeframe
  without a boatyard publish. If boatyard 0.9.0 has published to PyPI by
  the time this phase runs, skip the bridge and pin `>=0.9` directly.
  Either way the pin reverts to `>=0.9` once published.
- `stack/score/localizer.yaml:5` — add `boatyard/autostart: "false"` beside
  the existing gpu annotation (World A; the gpu annotation itself is
  untouched). World B: the whole namespace migrates to
  `outernet.internal/*` — every `boatyard/*` annotation in the score files
  (`boatyard/gpu`, `boatyard/probe-adapter`, `boatyard/dockerfile`,
  `boatyard/route`) gets the new spelling, and the new annotation lands as
  `outernet.internal/autostart: "false"`.
- `stack/score/reconstructor.yaml:7` — same change. The gpu comment at
  `:5-6` ("the GPU marker boatyard's built-in gpu patch templates key on")
  stays accurate (the templates still key on `"true"`); the new annotation
  line carries its own comment naming the created-stopped semantics.
- Regen: `uv run generate-score` (now runs against the path-pinned boatyard
  with the autostart annotation + selective-start). Canonical
  `Run generate-score`.

Verification: battery + preflight. Manual (the mandatory end-to-end for
selective-start): `uv run boatyard up --quiet-pull`, then `docker compose ps`
shows exactly one GPU container running (the default-mode one) and the
other `Exited` — the mode switcher started it, not `up`. `uv run gpu-mode
reconstruction` ⇒ the localizer stops, the reconstructor starts. Toggle
back ⇒ the reverse. A localization request while in reconstruction mode ⇒
503 "Localization unavailable".

Commit: code commit (path-pin + annotations), then canonical
`Run generate-score`.

### 6. Promotion and closeout

Complete, 2026-11-19 — every item below landed, with two text-vs-tree
adjustments: the block comment lives at
`workloads/api/src/routers/localizer_router.py` (the router-query branch
moved out of `localization.py` in phase 4), and the mode-switcher doc
mirrors `workloads/localizer/` (which carries `AGENTS.md` + a one-line
`CLAUDE.md` import; `workloads/lease-server/` carries neither). Prose
commit for the docs, code commit for the block comment; verification
prose-only per the plan.

- Fold hardened truth into co-located docs:
  - `stack/AGENTS.md` — the gpu-annotation constraint (`"true"` substrate
    semantics, templates its reader) and the separate `boatyard/autostart`
    annotation (created-stopped at `up`); the
    `localizer-router` resource type; the mode switcher as
    a compose-only provisioner-emitted service (joining ngrok as the second
    compose-only workload); the selective-start `up` behavior; the scoped
    bind exception to the hermetic-artifacts constraint; the raw-`docker
    compose up` dual-start caveat.
  - `workloads/AGENTS.md` — the mode switcher in the service inventory +
    the data-flow diagram; the `localizer-router` abstraction replacing
    the direct `LOCALIZER_CONTAINER_URL` forward; the 503-replacing-502
    failure mode.
  - new `workloads/mode-switcher/AGENTS.md` — the endpoints, boot
    reconciliation, Docker-SDK lifecycle, compose-only existence (mirrors
    how `workloads/lease-server/` and `workloads/localizer/` carry their
    own AGENTS.md).
  - `scripts/AGENTS.md` — the `gpu-mode` verb in the Entry points table.
  - `workloads/api/src/routers/localization.py` — a block comment at the
    router-query branch naming the `managed`-conditional contract (the
    single-file-deep rationale home per the AGENTS-SHARED rule).
  - Prose commits, separate from any code.
- ADR status section (`design/gpu-orchestration.md:20-50`): mark execution
  complete; the ADR stops being load-bearing (file remains).

Verification: prose-only; no code, no regen.

Commit: prose commit(s).

## Regens at a glance

| Phase | Regen | Canonical commit |
|---|---|---|
| 3 | score artifacts | `Run generate-score` |
| 4 | lock + clients (ServerInfo `gpu_mode_managed`) + score artifacts (api env/resource swap) | `Run generate-clients`, `Run generate-score` |
| 5 | score artifacts (autostart annotations) | `Run generate-score` |
