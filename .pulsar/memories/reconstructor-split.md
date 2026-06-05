---
updated: 2026-05-27
---

# Extract the lease / work-queue endpoints into a standalone `lease-server` service so the reconstructor doesn't need Keycloak

## Goal

The reconstructor authenticates to the API today via a Keycloak client-credentials JWT to call `/leases` and related work-queue endpoints. The auth boundary is in the wrong place: this is an in-cluster service-to-service control-plane call, not a user-facing API. The right boundary is the **network**, not a token. Eliminate the reconstructor's Keycloak dependency by extracting the lease endpoints into their own service; in doing so, remove an entire class of ceremony (the client-credentials grant, the RS256 token plumbing, the JWT verification on every lease call) that nothing actually uses.

This refactor is also a hard prerequisite for the air-gap / `AUTH_MODE=disabled` initiative (see `.pulsar/memories/auth-disable-mode.md`). Once the split lands, the reconstructor has no token to skip in disabled mode — the "reconstructor service-to-service auth in disabled mode" sub-problem evaporates and `docker/reconstructor/` falls out of the airgap PR's scope entirely.

## State

- Scaffold landed (commits `078e063f` code, `fdbc2a78` README). `docker/lease-server/` exists with Dockerfile, pyproject, pylock, entrypoint, settings, a minimal session factory (orchestration DB user only, no auth check), `routers/leases.py` (four routes copied from the api router, dropped `/internal/` prefix, swapped to local `get_session`), Litestar app via `common.litestar.create_litestar_app`, and `dump_openapi.py`. Wired into `compose.yml` (no `ports:`, no gateway upstream, depends on `migrate-database`), `compose.bake.yml` (build target — `LEASE_SERVER_SHA` auto-derived by `build/src/build_scripts/placeframe/context_sha.py`), `build/openapi-projects.json` (`"docker/lease-server": ["python"]`), `pyproject.toml` (workspace member). `uv.lock` and `docker/lease-server/pylock.toml` regenerated.
- Verified before commit: `CODEGEN=1 python -m src.dump_openapi` produces a full spec; `ruff check`, `ruff format --check`, `basedpyright`, and `deptry-check` are all clean for the new service.
- The api still owns the old `docker/api/src/routers/leases.py` and the reconstructor still uses the Keycloak token path — those changes are the next pending threads. `lease-server` is reachable in the stack, but nothing consumes it yet.
- Today's wiring (still live until the re-point): the reconstructor fetches a Keycloak client-credentials token (`packages/python/common/src/common/token_manager.py`) and attaches it as a Bearer header to API calls. The API's Litestar `AuthMiddleware` (`docker/api/src/auth.py:36+`) verifies the JWT on every request and extracts `claims["sub"]` into the request principal. **Nothing reads that principal.** The leases router (`docker/api/src/routers/leases.py:38-146`) does not branch on token type, does not key any row on `claims["sub"]`, and no auditing path reads it (`docker/api/src/auth.py:96` confirms). It's pure "yes I have a JWT" ceremony.
- The reconstructor's full control-plane surface is exactly four routes, all in `docker/api/src/routers/leases.py` (and now duplicated in `docker/lease-server/src/routers/leases.py`): `POST /leases/request`, `PUT /leases/{id}/progress`, `PUT /leases/{id}/succeed`, `PUT /leases/{id}/fail`. No other router has a service-to-service endpoint to relocate.

## Decisions

- **Standalone `lease-server` service, not a second listener inside the api service.** The repo already follows a small-focused-service pattern (`docker/livekit-token/`, `docker/state-sync/`, `docker/reconstructor/`, `docker/migrate-database/`); `docker/lease-server/` fits that shape. A separate service gives failure isolation (a bug in lease handlers can't crash user-facing routes), independent restart/deploy, and a tiny image with no Scalar UI / Keycloak schemes / `auth.py` import. "Two listeners inside one Litestar app" was rejected as a smaller-diff bias that introduces a novel pattern for no architectural gain.
- **`lease-server` has no JWT auth.** Bound only to the compose network — no `ports:` mapping, no gateway upstream block, no Caddy route. The network boundary is the control. A static shared-secret header was considered as belt-and-suspenders and rejected as ceremony; default to nothing.
- **The reconstructor calls `lease-server` directly by container DNS**, not through the gateway. No Bearer token. No Keycloak round-trip on startup. No token refresh.
- **Separate generated client.** `lease-server` gets its own entry in `build/openapi-projects.json` and produces `placeframe_lease_server_client` at `packages/generated/python/`. The reconstructor depends only on `placeframe_lease_server_client`; the user-facing `placeframe_api_client` stops advertising `/leases/*` it can't reach. One client per surface mirrors the service split.
- **Endpoint paths drop the `/internal/` prefix.** That prefix existed in the old single-service world as a hint about the auth boundary; on a service that is wholly internal it's redundant. Routes on `lease-server` are `/leases/request`, `/leases/{id}/progress`, `/leases/{id}/succeed`, `/leases/{id}/fail`.
- **Shared code stays shared.** `lease-server` imports `core.*` and `datamodels.public_tables` like the api service does. **Decided at scaffold time: `get_session` was duplicated into `docker/lease-server/src/database.py` rather than extracted to `common`.** The shapes diverged enough — `lease-server` has no auth check, no `request: Request` param, and only the orchestration session — that extracting to a shared helper would have introduced more conditional branching than the ~15-line duplicate.
- **Do not fold this into the airgap PR.** This refactor is a separate, narrowly-scoped ticket that lands first. Conflating the two would mix an architectural cleanup (correctly placed auth boundary) with a deployment-mode feature (`DEPLOYMENT_MODE` / `AUTH_MODE`) and bloat the diff.
- **The reconstructor is excluded from the airgap initiative's scope once this lands.** After the split, `packages/python/common/src/common/token_manager.py` and `docker/reconstructor/` no longer appear in the airgap initiative's key-files list.

## Open questions

- None blocking. Shared-helper extraction (`get_worker_session`) is a judgement call at implementation time, not a decision needing user input.

## Key files

- `docker/api/src/routers/leases.py` — the four routes that move to `docker/lease-server/`. Self-contained except for `..database.get_worker_session`.
- `docker/api/src/database.py` — source of `get_worker_session`; either extracts to `packages/python/common/` or gets duplicated.
- `docker/api/src/main.py` — drops the `leases_router` import and registration.
- `docker/api/src/auth.py` — unchanged in this initiative; remains the user-facing auth middleware.
- `docker/lease-server/` — new directory: `Dockerfile`, `pyproject.toml`, `pylock.toml`, `src/lease_server/{main,settings}.py`, copies of the four route handlers from `leases.py`. Litestar app without auth middleware, without OAuth/Scalar plugins.
- `docker/reconstructor/src/reconstructor/main.py` — drops `TokenManager` instantiation and the `default_headers["Authorization"]` plumbing (lines 29, 38–40); points the client at `lease-server`'s container DNS via a new `lease_server_url` setting; switches imports from `placeframe_api_client` to `placeframe_lease_server_client` for lease calls.
- `docker/reconstructor/src/reconstructor/progress_publisher.py` — same client-package swap (line 11).
- `docker/reconstructor/src/reconstructor/settings.py` — drops `auth_token_url`, `auth_client_id`, `private_key_path`; adds `lease_server_url`.
- `packages/python/common/src/common/token_manager.py` — deleted once no service uses it (verify no other consumer first).
- `compose.yml` — adds `lease-server` service (no `ports:`, no gateway upstream); reconstructor service loses `KEYCLOAK_*` env injection.
- `build/openapi-projects.json` — adds `lease-server` entry to drive `generate-clients` codegen for `placeframe_lease_server_client`.
- `docker/SPEC.md` — service inventory, data flow, and auth model; updated first per repo policy (spec-first on disagreement). Documents `lease-server` as a separate service and the network-as-auth-boundary rationale.
- `.pulsar/memories/auth-disable-mode.md` — downstream initiative blocked on this work; cross-references this memory as a prerequisite.

## Pending threads

1. ~~Update `docker/SPEC.md`~~ — done in commit `3d54f2df` (alongside both memory updates).
2. ~~Scaffold `docker/lease-server/`~~ — done in commit `078e063f` (+ README in `fdbc2a78`).
3. ~~Add `lease-server` to `compose.yml`, `compose.bake.yml`, `build/openapi-projects.json`, `pyproject.toml` workspace.~~ — done in commit `078e063f`.
4. **Next:** run `uv run generate-clients --config build/openapi-projects.json --project docker/lease-server` to produce `placeframe_lease_server_client` at `packages/generated/python/lease-server-client/`. Codegen output goes in its own commit per repo policy (canonical message: `Run generate-clients`).
5. Re-point the reconstructor: in `docker/reconstructor/src/reconstructor/main.py` (lines 7, 29, 38–40) and `progress_publisher.py` (line 11), swap `placeframe_api_client` → `placeframe_lease_server_client` for lease/progress calls; drop `TokenManager` instantiation and the `default_headers["Authorization"]` plumbing; point `Configuration(host=...)` at `http://lease-server:8000` via a new `lease_server_url` setting (replace `api_internal_url`); drop `auth_token_url`, `auth_client_id`, `private_key_path` from `docker/reconstructor/src/reconstructor/settings.py`. Update reconstructor's compose env block accordingly, and add `depends_on: lease-server: service_healthy`.
6. Delete `docker/api/src/routers/leases.py`, remove its import + registration from `docker/api/src/main.py` (lines 14, 84). Re-run codegen so `placeframe_api_client` stops advertising `/leases/*`.
7. Delete `packages/python/common/src/common/token_manager.py` after confirming no other consumer (grep `token_manager` / `TokenManager` across the repo — `state-sync` still uses worker-private-key but that's a different mechanism).
8. Verify the user-facing path still works end-to-end (Unity client + Keycloak + Caddy + api service) — no regression in the default `localtonet` + `keycloak` deployment. Verify the reconstructor still claims and completes leases against `lease-server`.
9. Once merged, unblock and resume `.pulsar/memories/auth-disable-mode.md`.
