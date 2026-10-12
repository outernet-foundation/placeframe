# Compose artifact split and auth decoupling

Split the published placeframe stack into multiple OCI artifacts that consumers
`include:` separately, and eliminate the `AUTH_MODE` runtime switch that
currently gates auth across the gateway, the API, and the lifecycle tooling.
The two are one piece of work: the artifact split is only possible once auth
becomes structural (which edge artifact you include) rather than a string
branched on at runtime.

## Problem

The stack is switched today by three inconsistent mechanisms, all living in
`compose.yml`:

| Switch | Mechanism | Decided where |
|---|---|---|
| Keycloak on/off | `AUTH_MODE` string → `up.py:102` imperatively adds `--profile keycloak` | `docker-devkit` code |
| ngrok vs rathole vs neither | `COMPOSE_PROFILES=tunnel-ngrok\|tunnel-rathole` | `.env` |
| ngrok self-skip | empty `NGROK_DOMAIN` → container starts and exits | runtime |

Three shapes for "this container is present or not." Keycloak is switched by a
Python string read inside the lifecycle tool; tunnels are switched declaratively
in `.env`; ngrok has a third half-switch where the container runs and dies.

`AUTH_MODE` is not a container toggle — it is a runtime string threaded through
six places, each of which branches on it:

1. `docker-devkit/src/docker_devkit/modes.py:22` — rejects `http://` + keycloak
2. `docker-devkit/src/docker_devkit/up.py:102` — activates the keycloak compose profile
3. `workloads/gateway/entrypoint.sh:31` — emits/omits the `/auth/*` reverse-proxy and `/loki/*` `forward_auth` Caddy directives
4. `workloads/api/src/settings.py:49` — conditionally requires the five `AUTH_*` URL fields
5. `workloads/api/src/auth.py:51` — `AuthMiddleware` either skips JWT decode and returns the sentinel, or verifies a real token
6. `workloads/api/src/database.py:78` — `get_session` JIT-creates `SHARED_ANONYMOUS_TENANT` and rewrites `app.tenant_id`

The recorded ruling in `workloads/AGENTS.md` ("`PUBLIC_URL` and `AUTH_MODE` are
independent axes") defends keeping them as *two* switches rather than *one*. It
does not defend runtime-string-branch vs structural composition — that is the
question here, and the ruling is silent on it.

The strongest evidence this is wrong on its own merits, independent of the
artifact goal: **`modes.py` lives in `docker-devkit`**, a package whose own
`AGENTS.md` calls itself "a small, generic package that any repo shipping a
compose graph can depend on." It hardcodes `VALID_AUTH_MODES = ("keycloak",
"disabled")` — placeframe's auth vocabulary inside a consumer-agnostic tool.
Make-it-Sing's `uv run up` is forced through `resolve_auth_mode()` (called
unconditionally in `up.py:76`) even though Make-it-Sing does not care about
keycloak; `design/make-it-sing-ci-bringup.md` Stage 6 already flags "Reconcile
AUTH_MODE/PUBLIC_URL validation with the demo `.env`s" as an open wound.
Placeframe's auth policy leaked across a repo boundary into a shared tool.

Side findings in the same code path:

- `workloads/AGENTS.md:64` says the guard "lives in the external
  `stack-lifecycle`'s `modes.py`," but the code is in `docker-devkit`. Stale
  after a rename; dies entirely once `modes.py` is removed.
- `workloads/api/src/database.py:66` does `cast(str | None, claims.get("sub"))`,
  which violates the `typing.cast` prohibition in `AGENTS-SHARED.md`. The
  `claims` dict is already typed; this should be a typed access, not a cast. It
  sits in the exact code the auth refactor rewrites.

## Target

Five published OCI artifacts. The consumer `include:`s the ones they want. No
`AUTH_MODE`, no `COMPOSE_PROFILES`, no `--profile keycloak` in `up.py`.

| Artifact | Contents | Variant-tagged? |
|---|---|---|
| `placeframe-core-<variant>` | api, lease-server, postgres, seaweedfs\*, cloudbeaver\*, database-manager, database-migrator, loki, alloy, grafana, initialize-loki, reconstructor, localizer | yes (cuda/rocm) |
| `placeframe-edge-keycloak` | gateway (auth Caddyfile snippets mounted), keycloak, auth-initializer | no |
| `placeframe-edge-anonymous` | gateway (no auth snippets) | no |
| `placeframe-tunnel-ngrok` | ngrok | no |
| `placeframe-tunnel-rathole` | rathole-client | no |

**The gateway lives in the edge artifact, not core.** This is the load-bearing
decision: each artifact owns its services wholly, so there are zero cross-
include service overrides — the fragile thing `Make-it-Sing/compose.yml` already
warns about ("compose won't apply one include's overrides over another's"). Core
has no public surface on its own; the consumer must pick an edge, which makes
the auth choice explicit and unavoidable.

The API's auth behavior is driven by whether `AUTH_ISSUER_URL` is set in `.env`
(presence, not a mode string), so the same API image works in both edges with no
branch.

Consumer recipes:

- Full keycloak + ngrok: `core-cuda` + `edge-keycloak` + `tunnel-ngrok`
- Air-gap anonymous: `core-cuda` + `edge-anonymous`
- Make-it-Sing: `core-cuda` + `edge-keycloak` + `tunnel-rathole` (+ its own livekit/ingress)

## Plan

Sequenced by build-dependency. Phase A ships independently; B is one PR with
prose-first commits then code commits in build-order; C starts after B's
artifacts are in the registry.

```
A (docker-devkit: strip auth) ──release──┐
                                         │  pin bump in B5
B (placeframe: prose → API → gateway → compose → publish → pin) ──publish artifacts──┐
                                                                                       │
C (Make-it-Sing: include new artifacts) ─────────────────────────────────────────────┘
D (verification + follow-ups)
```

### Phase A — docker-devkit: strip auth-mode (separate repo, release first)

Ships independently; no placeframe repo consumes it until Phase B bumps the
pin. Old placeframe keeps its pinned old docker-devkit, so no breakage.

Code:

1. Delete `src/docker_devkit/modes.py` entirely. Move `parse_env_file` (still
   used by `up.py` for the image lock) into `lifecycle.py`.
2. `src/docker_devkit/up.py` — drop `resolve_auth_mode` import + call; drop the
   `profile_flag` computation and its interpolation into `compose_args`; fix the
   `parse_env_file` import to its new home.
3. `src/docker_devkit/down.py` — drop `resolve_auth_mode` import + call; drop
   the hardcoded `--profile keycloak ` from the command. `--remove-orphans`
   (already present) handles tearing down keycloak containers from prior runs.
4. Delete `tests/test_modes.py` if present; fix any up/down test asserting the
   profile flag.

Prose:

5. `AGENTS.md` — remove the `modes.py` row from the module table; rewrite the
   ".env (required)" bullet (drop `AUTH_MODE`, keep `PUBLIC_URL`).

Release: version bump + publish to PyPI. Breaking change, but docker-devkit is
<1.0, so it rides the patch flow per its own `AGENTS.md`.

### Phase B — placeframe structural cutover (one PR, commits sequenced)

The API refactor, gateway refactor, compose split, publish refactor, and pin
bump are coupled and ship together. A backward-compat bridge between API and
compose would be throwaway work — the API derives auth from `AUTH_ISSUER_URL`
presence and the new core compose soft-defaults it, so they must land together.

#### B0 — prose (spec-first, before any code)

1. `workloads/AGENTS.md` — rewrite "Authentication and public URL": delete
   `AUTH_MODE` as a switch; describe the edge-artifact choice as structural.
   Replace the "PUBLIC_URL and AUTH_MODE are independent axes" constraint with
   "auth presence is structural: which edge artifact you include." Delete the
   stale `stack-lifecycle`/`modes.py` reference (line 64). Update the services
   table: keycloak → "edge-keycloak artifact"; ngrok "always present,
   self-skips" → "tunnel-ngrok artifact"; gateway row → "Caddyfile assembled
   from snippet configs mounted by the edge artifact, no runtime auth branch."
2. `README.md` — replace "Deployment shapes" with artifact-include recipes and
   the 5-artifact table.
3. `AGENTS.md` — update "Initial Setup" to the artifact recipe; drop the
   `AUTH_MODE`/`COMPOSE_PROFILES` env notes.
4. `build/AGENTS.md` — update the `publish_compose.py` description to
   multi-artifact emit.
5. `packages/unity/Logging/AGENTS.md` — replace "`AUTH_MODE=disabled`" prose
   with "when the edge-anonymous artifact is used."

#### B1 — API auth-backend refactor (code)

Eliminates `AUTH_MODE` from the API. The signal becomes `auth_issuer_url is
not None`.

- `workloads/api/src/settings.py` — delete the `auth_mode` field. Keep the five
  `auth_*` URL fields Optional (no default). Rewrite `check_auth_config`: if
  `auth_issuer_url` is set → require the other four; if unset → they must be
  None. Add the moved cleartext-OAuth guard here: if `auth_issuer_url` is set
  and `public_url` scheme is `http` → raise. (This is the `modes.py` guard's
  new home — the API is the thing that would put OAuth creds in cleartext, and
  it already validates its settings at boot.)
- `workloads/api/src/auth.py` — introduce a backend selected by
  `settings.auth_issuer_url is not None`. Anonymous backend returns
  `(SHARED_ANONYMOUS_USER, SHARED_ANONYMOUS_TENANT)`; keycloak backend runs the
  existing JWKS flow. `authenticate_request` delegates; the
  `auth_mode == "disabled"` branch dies.
- `workloads/api/src/database.py` — delete the `auth_disabled` branch
  (lines 78–89). `get_session` consumes `(user_id, tenant_id)` from the auth
  result uniformly: set `app.user_id` always, set `app.tenant_id` if non-None,
  JIT-create the tenant row when the backend provides one. Fix the `cast`
  violation (line 66) — the backend already produced `user_id` as a typed
  `str`; consume it directly, drop `from typing import cast`. Move
  `SHARED_ANONYMOUS_TENANT` into the anonymous backend.
- `workloads/api/src/main.py` — line 38: `if settings.auth_mode == "disabled"`
  → `if settings.auth_issuer_url is None`. The keycloak branch references
  `auth_audience`/`auth_url`/`auth_token_url` (valid only when issuer set) —
  same condition guards them.
- `workloads/api/src/routers/server_info.py` — derive the response `auth_mode`
  from `settings.auth_issuer_url is not None` (`"keycloak"` if set else
  `"disabled"`). Client contract preserved — the field and its values are
  unchanged, so no client/codegen churn. OIDC URLs included only when set.
- `workloads/api/src/constants.py` — unchanged (sentinels now owned by the
  anonymous backend).
- `workloads/api/tests/test_server_info.py` — still passes as-is (asserts both
  modes); optionally add a case asserting `AUTH_ISSUER_URL` absence → disabled.
- Grep all tests for `AUTH_MODE` and switch them to set/unset `AUTH_ISSUER_URL`.

The `/server-info` OpenAPI schema is unchanged (the response model keeps
`auth_mode`), so no `generate-clients` run is required by this refactor.

#### B2 — gateway entrypoint refactor (code)

- `workloads/gateway/entrypoint.sh` — delete the `AUTH_MODE` branch (lines 21,
  31–47). Keep the `PUBLIC_URL` scheme/port parsing (unrelated to auth).
  Replace `${auth_handler}` with `import /etc/caddy/snippets/site-*.conf;` at
  the top of the site block. Replace `${loki_forward_auth}` with
  `import /etc/caddy/snippets/loki-*.conf` inside the `/loki/*` handle before
  `reverse_proxy`. Drop `AUTH_MODE="${AUTH_MODE:-keycloak}"`. Caddy glob-imports
  that match nothing are silent no-ops; if a given Caddy version warns, gate the
  import line on `[ -n "$(ls /etc/caddy/snippets/*.conf 2>/dev/null)" ]` —
  file-presence, not a mode string.

#### B3 — compose split (code)

- New `compose.core.yml` — from old `compose.yml`, extract everything except
  gateway, keycloak, auth-initializer, ngrok, rathole-client. The `api` service:
  drop the `AUTH_MODE` env; change the five `AUTH_*` envs from hardcoded-
  PUBLIC_URL-derived to soft-defaulted (`AUTH_ISSUER_URL: "${AUTH_ISSUER_URL:-}"`,
  etc.). Drop the `keycloak`/`auth-initializer` profile entries. Keep `volumes`
  minus `auth_data`/`keycloak_import`/`keycloak_data` (they move to edge). Keep
  the loki/alloy/grafana `configs`.
- New `compose.edge.keycloak.yml` — `gateway` (moved here, owned wholly):
  `depends_on: [keycloak (required: true), api]`; mounts two compose `configs`
  (`site-auth-handler`, `loki-forward-auth`) at `/etc/caddy/snippets/`; env
  `PUBLIC_URL` only (no `AUTH_MODE`). The snippet `content:` is the `/auth/*`
  `handle_path` block and the `forward_auth` directive currently generated in
  `entrypoint.sh`. `keycloak` (moved, no `profiles:`). `auth-initializer`
  (moved, no `profiles:`). Top-level `volumes`: auth_data, keycloak_import,
  keycloak_data. Top-level `configs`: the two snippets (inline `content:`).
- New `compose.edge.anonymous.yml` — `gateway` only, no snippet mounts,
  `depends_on: [api]` only.
- New `compose.tunnel.ngrok.yml` — `ngrok` (moved, no `profiles:`); keep the
  `:-` soft defaults for `NGROK_*`.
- New `compose.tunnel.rathole.yml` — `rathole-client` (moved, no `profiles:`).
- Delete `compose.yml` — its contents are distributed across the new files.
- `compose.postgres.yml`, `compose.cuda.yml`, `compose.rocm.yml`,
  `compose.dev.yml` — unchanged.
- `docker-devkit.yaml` — `lifecycle.files`: `[compose.core.yml,
  compose.postgres.yml, compose.{gpu}.yml, compose.edge.keycloak.yml,
  compose.tunnel.ngrok.yml]` (the default full stack). The dev swaps edge/tunnel
  entries to switch shapes. `down.py`'s `--remove-orphans` cleans up when the
  dev switches edge.
- `.env.sample` — rewrite: drop `COMPOSE_PROFILES` and `AUTH_MODE`. Sections:
  "core (always)" → PUBLIC_URL, DB creds, S3, ports; "edge-keycloak" → the five
  `AUTH_*` + `KEYCLOAK_*`; "tunnel-ngrok" → `NGROK_*`; "tunnel-rathole" →
  `TUNNEL_*`/`ENGINEER_NAME`. Default filled for keycloak + ngrok.

#### B4 — publish_compose.py multi-artifact (code)

- `build/src/build_scripts/placeframe/ci/publish_compose.py` — generalize from
  one bundle to an artifact registry. Define the five artifacts (name,
  variant-suffix flag, source-file list). For each: bake (var-substitute),
  `_inline_configs`, `_pin_references`, `docker compose publish` with `<sha>`
  and `<branch>` tags. Core is `--variant`-parameterized; edge/tunnel are
  variant-agnostic (one publish per sha/branch, not per variant). The existing
  `_inline_configs` and `_pin_references` helpers are reused per-artifact
  unchanged.
- `build/tests/test_publish_compose.py` — add tests that the registry produces
  five publish targets and that variant-agnostic artifacts don't carry the
  variant suffix.

#### B5 — pin bump (code)

- `pyproject.toml` + `uv.lock` — bump `docker-devkit` to the Phase A release;
  relock.

#### B6 — verification (run, not commit)

`uv run up` (default files: core+edge-keycloak+tunnel-ngrok) → `/server-info`
reports keycloak, keycloak container present. Swap `docker-devkit.yaml` to
`compose.edge.anonymous.yml` → `uv run up` → `/server-info` reports disabled,
no keycloak container. `uv run down -v --remove-orphans` clean. `uv run ruff
check && uv run basedpyright && uv run pytest` green. `uv run --no-sync
preflight` green. `uv run publish-compose --variant cuda` (CI-shape) emits five
artifacts.

### Phase C — Make-it-Sing consumption (after Phase B artifacts are published)

- `Make-it-Sing/compose.yml` — replace the single
  `include: oci://.../placeframe-cuda@sha256:…` with three:
  `placeframe-core-cuda`, `placeframe-edge-keycloak`,
  `placeframe-tunnel-rathole`, each digest-pinned. Keep `gateway: ports: !reset
  []` and `postgres: ports: !reset []` (Make-it-Sing's ingress owns the public
  port; postgres is in-core now). Re-audit the rathole `RATHOLE_SERVICES`
  override still applies cleanly.
- `.env` — ensure the five `AUTH_*` vars are set (edge-keycloak's keycloak
  service `:?err`-enforces them).
- Verify: `docker compose -f compose.yml config` parses; `uv run up` brings up
  the combined stack; livekit + placeframe gateway both reachable through the
  ingress.

### Phase D — verification & follow-ups

- Grep all org repos for residual `AUTH_MODE` / `COMPOSE_PROFILES` / `modes.py`
  references; clean up.
- Audit other consumers of the old single `placeframe-cuda`/`placeframe-rocm`
  artifact (capture-tool likely has its own compose — verify it doesn't include
  the bundle). The old tags stay in the registry as historical; B4 already
  stops publishing them.

## Out of scope (flagged follow-ups)

- **`stack/score/` parallel tier**: the score-generated k8s/compose tier
  carries `AUTH_MODE` too (`stack/score/placeframe-config.provisioners.yaml`,
  `stack/generated/...`). It is a separate deployment surface (k8s) and should
  receive the same presence-driven treatment, sequenced after the compose tier
  is green. Not a blocker for the compose/OCI refactor.
- **docker-devkit `{edge}`/`{tunnel}` template**: generalize the `{gpu}`
  templating in `lifecycle.files` to `{edge}`/`{tunnel}` so the dev switches
  shapes without editing `docker-devkit.yaml`. Convenience, not correctness.

## Open decision

`AUTH_CERTS_URL` is currently an internal compose-network URL
(`http://keycloak:8080/...`) that a consumer including `edge-keycloak` would now
have to set in `.env` — leaky. The clean fix is to have the API derive it from
`AUTH_ISSUER_URL` + a default internal keycloak host (`keycloak:8080`), so the
consumer only sets public URLs. B1 assumes that derivation lands; if instead
`AUTH_CERTS_URL` stays an explicit consumer env, B1 shrinks slightly and
`.env.sample` carries one extra var.
