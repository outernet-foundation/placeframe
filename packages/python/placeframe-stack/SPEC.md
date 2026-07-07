# placeframe-stack/SPEC.md

## What this is

`placeframe-stack` is a standalone workspace member that owns the Docker-stack lifecycle commands — `up`, `down`, and `build` — plus the helpers they share (`detect_gpu`, `modes`, `context_sha`). It is split out from `build-scripts` so a consumer repo can git-reference *just* the bring-up/tear-down machinery without inheriting the codegen dependency surface (`sqlacodegen`, `psycopg`, `datamodel-code-generator`). The placeframe repo and downstream consumers such as make-it-sing both drive their stacks through these same `uv run up` / `uv run down` entry points.

## Shape

Entry points (`[project.scripts]`): `up` → `up.py:app`, `down` → `down.py:app`, `build` → `build_docker.py:app`, `generate-k3s` → `generate_k3s.py:app`. All accept `--help`.

| Module | Role |
|---|---|
| `up.py` | `docker compose up`. Flags: `--attached`/`-a`, `--quiet-pull`/`-q`, `--build`, `--gpu auto\|cuda\|rocm\|none`, `--no-dev`, `--compose-file`. |
| `down.py` | `docker compose down`. Flags: `--volumes`/`-v` (also removes named volumes), `--gpu`, `--compose-file`. |
| `build_docker.py` | `run_build()` + the `build` command — builds the local stack's images, auto-detecting CUDA/ROCm. |
| `generate_k3s.py` | `generate-k3s` command — runs the Compose Bridge transform (`my-transform/`) and post-processes the emitted `out/` Kustomize tree. Flag: `--output`. See `my-transform/SPEC.md`. |
| `detect_gpu.py` | `detect_gpu()` → `cuda`/`rocm`/`none` from host devices; the `Gpu` literal. |
| `modes.py` | `resolve_auth_mode()` — validates `PUBLIC_URL` + `AUTH_MODE` from `.env`, rejecting `keycloak` over cleartext `http://`. |
| `context_sha.py` | `compute_service_shas()` — per-service `tree-<hash>` image tags over the `.dockerignore`-allowlisted git tree. Also imported by `build-scripts`' CI commands. |

`build-scripts` depends on this package: its CI commands (`build-docker`, `create-release`, `preflight`, `publish-compose`) import `run_build` / `compute_service_shas` from here.

## Constraints

### Native stack vs. consumer stack

**Context:** The placeframe repo builds its own images and assembles a multi-file compose graph (`compose.yml` + `compose.postgres.yml` + the GPU layer + `compose.dev.yml`), injecting per-service `${*_SHA}` image tags and a `.env.lock` of third-party digests. A consumer repo (make-it-sing) has none of that: it ships a single self-contained compose file that pulls placeframe in *already baked* — either via an OCI `include` of the published artifact (image digests and internal vars frozen as literals) or via an `include` of a sibling placeframe checkout (which supplies its own `.env.lock`/`.env.shas` through the include's `env_file`). Running `compute_service_shas` there is meaningless (no `compose.bake.yml`, no Dockerfiles) and requiring `.env.lock` is wrong (the consumer has no internal vars to resolve).

**Constraint:** `up`/`down` pick the mode by the marker `compose.bake.yml`, which exists only in the placeframe repo. **Native** = the default `--compose-file compose.yml` *and* `compose.bake.yml` present → multi-file assembly, SHA injection, `.env.lock` required. **Consumer** = anything else → the single `--compose-file` is the whole graph, run with `--env-file .env` alone; SHA resolution is skipped and `.env.lock` is passed only if it happens to exist. `--build` is rejected outside native mode (a consumer has no local build graph).

**Consequences:** A consumer runs `uv run up` (default `compose.yml`) or `uv run up --compose-file compose.local.yml` from its own repo root, against its own `.env`, with no extra setup. The placeframe repo's behavior is unchanged: default `compose.yml` stays native, and an explicit non-default `--compose-file` inside placeframe still falls through to the single-graph path exactly as before.

### Why a package split rather than a flag

Lifecycle (`up`/`down`/`build`) and codegen (`generate-clients`/`generate-datamodels`/`lock-python`) have disjoint dependency surfaces. A consumer that only brings the stack up should not have to install `sqlacodegen`/`psycopg`/`datamodel-code-generator`. Keeping the lifecycle here — the way `placeframe-bash` and `placeframe-unity` are standalone for the same reason — lets make-it-sing git-reference a small package. `build-scripts` still depends on this one for the CI helpers (`compute_service_shas`, `run_build`).

### `--quiet-pull` logging and GPU auto-detection

`--quiet-pull` suppresses compose's per-layer progress (the CUDA images carry hundreds of layers) while still surfacing pull totals. `--gpu auto` resolves to `cuda`/`rocm`/`none` from host devices and selects the matching `compose.<gpu>.yml`; override only to reproduce a CI environment or test the CPU-only path.

### `build` emits two env files, partitioning image references by who builds the image

`.env.lock` (committed) carries third-party and base-image digests — images placeframe *pulls*. `.env.shas` (gitignored) carries the `tree-<hash>` tags of images placeframe *builds* from its own Dockerfiles, where the hash is a `git write-tree` over the `.dockerignore`-allowlisted context (`context_sha.py`). The split is mandated by a CI invariant — `.env.lock` must never contain built-image digests — and by churn: `.env.shas` changes on every source edit, so it stays out of version control. `up` injects the `${*_SHA}` values into the environment directly (native mode only) and reads neither file; `.env.shas` exists so a consumer running placeframe's compose files through raw `docker compose` (without the `up` wrapper) can resolve those holes via `--env-file .env.shas`.

## See also

- `build/SPEC.md` — the `build-scripts` package that owns codegen + Cesium + CI and depends on this package for `compute_service_shas` / `run_build`.
- `docker/SPEC.md` — the service inventory and data flow of the stack these commands bring up.
