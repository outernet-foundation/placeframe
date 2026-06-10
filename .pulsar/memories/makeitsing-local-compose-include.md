---
updated: 2026-06-08
---

# Local-dev path for make-it-sing to consume a locally-built placeframe backend (instead of the published OCI compose artifact)

## Goal

make-it-sing's `compose.yml` pulls the placeframe backend via Compose's `include: oci://…@sha256:…` directive — a fully self-contained, digest-pinned placeframe stack published to ghcr. The only way to test local placeframe changes from make-it-sing today is: rebuild → CI publishes a new artifact → bump the `@sha256` in make-it-sing. We want a local-dev loop where editing placeframe and rebuilding is immediately visible to a `docker compose up` run from a sibling make-it-sing checkout, with **fresh clones unaffected** and `docker compose up` staying the command in both modes.

## State

- Design researched and recommended; **nothing implemented yet**. This memory is the design conclusion, not committed code.
- A separate, unfinished follow-up task was started after the design: the host `.env` mounted for placeframe uses `PUBLIC_DOMAIN=skilled-finally-primate.ngrok-free.app` (make-it-sing's convention), but placeframe's entire codebase only reads `PUBLIC_URL=https://…` (full URL with scheme). `uv run up` failed at `resolve_auth_mode` because `PUBLIC_URL` was missing. The user then asked to copy the correct vars from make-it-sing's `.env` into placeframe's `.env` and retry the backend bring-up — that port-over was not completed in this session.
- Placeframe images rebuilt successfully in this session (`uv run build`, exit 0, all GPU services present).

## How the OCI include works today

- make-it-sing `/make-it-sing/compose.yml:3-4` = `include: - oci://ghcr.io/outernet-foundation/placeframe/placeframe-cuda@sha256:4c31988…`. `include` merges another Compose model at parse time; the `oci://` form pulls a Compose file published as an OCI artifact. Effective make-it-sing model = published placeframe stack + make-it-sing's own services (livekit, livekit-token, ingress, gateway `!reset`, rathole).
- The artifact is produced by `uv run publish-compose` (`build/src/build_scripts/placeframe/ci/publish_compose.py`) in CI. It: (1) merges `compose.yml` + `compose.postgres.yml` + `compose.{cuda,rocm}.yml`; (2) bakes placeframe-internal `${API_SHA}` / `${GATEWAY_SHA}` / … (from `compute_service_shas`, a `git write-tree` over the `.dockerignore` allowlist) and `.env.lock` third-party digests to literals; (3) pins every placeframe image `…/api:tag` → `…/api@sha256:…` via `imagetools inspect`; (4) leaves consumer-facing vars (`.env.sample` keys like `MINIO_ACCESS_KEY`, `PUBLIC_URL`) as literal `${VAR}` holes; (5) `docker compose … publish` → `placeframe-cuda:{sha}` / `:{branch}`.

## Two root blockers

1. The OCI include is hardcoded in the **auto-loaded** `compose.yml`, and `include` is **additive and conflict-erroring** — you cannot layer a second `-f` override that "replaces" the placeframe include with a local one (you'd get `api` defined twice → error).
2. Placeframe's raw `compose.yml` references `${*_SHA}` service vars that **only `uv run up` injects** (`up.py:_resolve_service_shas`, called before handoff to `docker compose`). They live in no file, so a plain `docker compose up` against placeframe's tree can't resolve them.

## Recommended design — a `COMPOSE_FILE`-selected local include

**make-it-sing side:**
1. Factor make-it-sing's own services out of `compose.yml` into `compose.services.yml` (livekit, livekit-token, ingress, gateway `!reset`, rathole).
2. `compose.yml` (auto-loaded → clean-clone path) = OCI include + `include: compose.services.yml`. `git clone && docker compose up` still works with zero config.
3. Add `compose.local.yml` (dual-checkout path):
   ```yaml
   name: makeitsing
   include:
     - path:
         - ${PLACEFRAME_DIR:-../placeframe}/compose.yml
         - ${PLACEFRAME_DIR:-../placeframe}/compose.postgres.yml
         - ${PLACEFRAME_DIR:-../placeframe}/compose.cuda.yml
       env_file:
         - ${PLACEFRAME_DIR:-../placeframe}/.env
         - ${PLACEFRAME_DIR:-../placeframe}/.env.lock
         - ${PLACEFRAME_DIR:-../placeframe}/.env.shas
     - path: compose.services.yml
   ```
   Opt in via `COMPOSE_FILE=compose.local.yml` in the gitignored `.env`. Placeframe uses only named volumes (no relative bind mounts), so `project_directory` is not required.

**placeframe side:**
4. Have `uv run build` also write a gitignored `.env.shas` containing the computed service SHAs (same dict `_resolve_service_shas` puts in the environment). The include's long-form `env_file` supplies them as **interpolation defaults for the included placeframe files**, filling `${API_SHA}` etc. Wiring it into `build` (not a separate command) keeps it from drifting from the locally-built images.

**Resulting loop:** edit placeframe → `uv run build` (rebuilds changed images + refreshes `.env.shas`) → `docker compose up` in make-it-sing picks them up by SHA. No CI, no digest bump. Fresh clones untouched.

## Decisions

- `.env.shas` is a **separate file from `.env.lock`** — mandated by the CI invariant ".env.lock contains only base/third-party digests, never built-image digests."
- Use the `COMPOSE_FILE`-selected local include over a thin `uv run` wrapper, so `docker compose up` stays the literal command in both clean-clone and dual-checkout modes.
- Compose's long-form `include` `env_file` providing interpolation defaults for the included file is the verified hook that solves the `${*_SHA}` problem. Compose also supports variable interpolation inside the `include` path/OCI ref itself (confirmed on recent versions), enabling `${PLACEFRAME_DIR:-../placeframe}`.

## Open questions

- Did the user prefer the generated `.env.shas` approach, or a thin `uv run` wrapper over it? (Asked at end of design; not answered.)
- Exact set of make-it-sing services to move into `compose.services.yml` should be re-confirmed against `/make-it-sing/compose.yml` at implementation time.

## Security note (act on during implementation)

- OCI-artifact includes were hit by **CVE-2025-62725** (path traversal escaping the artifact cache; even `docker compose ps` can trigger it on a malicious ref). Fixed in **Compose v2.40.2+**. Since make-it-sing consumes OCI includes, require/pin Compose ≥ 2.40.2.

## Key files

- `/make-it-sing/compose.yml` — holds the `oci://…placeframe-cuda@sha256:…` include and make-it-sing's own services; both `compose.yml`/`compose.services.yml`/`compose.local.yml` changes land here.
- `build/src/build_scripts/placeframe/ci/publish_compose.py` — produces the published OCI compose artifact; defines what gets baked vs. left as `${VAR}` holes.
- `build/src/build_scripts/placeframe/up.py` — `_resolve_service_shas()` injects `${*_SHA}` into the env before `docker compose` handoff; also already documents `compose.makeitsing.yml` as a base-file choice (file does not yet exist in tree).
- `compose.yml`, `compose.postgres.yml`, `compose.cuda.yml` — the placeframe files the local include must pull and feed SHA defaults to.
- `.pulsar/memories/multi-repo-refactor.md` — companion context on the placeframe/make-it-sing multi-repo split intent.

## Pending threads

- Implement the design: make-it-sing `compose.services.yml` / `compose.local.yml` split + placeframe `.env.shas` emission wired into `uv run build`. (Yield for the wrapper-vs-file choice first.)
- Finish the `.env` port-over: copy correct vars from make-it-sing's `.env` into placeframe's `.env` (notably translate `PUBLIC_DOMAIN` → `PUBLIC_URL=https://…`), then retry `uv run up`.
