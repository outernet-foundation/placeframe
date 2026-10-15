# Session compaction: compose decomposition × score initiative

Written 2026-10-12. Handoff document for a fresh session continuing the conversation about
replacing hand-authored compose files with score-generated ones and decomposing the published
stack into includable artifacts. **No code changes were made this session** — it was entirely
investigation and mental-model building. Read top to bottom.

The user's stated end goal (verbatim intent): *no compose files other than code-generated ones in
`stack/generated/compose`; any consumer of placeframe composes their own backend by building a
compose-of-composes from that output, rather than using switches like `COMPOSE_PROFILES` /
`AUTH_MODE`. GPU (cuda/rocm/cpu) is acknowledged as possibly a separate problem needing a
separate solution.*

---

## 1. Where the conversation got to

The user started from "I don't remember what we were planning and don't know how it interacts
with score." The session established:

1. **Two initiatives, one destination.** `design/compose-artifact-split.md` fixes the
   *consumption* model (5 includable OCI artifacts, structural auth, no switches). The score
   initiative fixes the *authoring* model (describe workloads once, generate compose AND k8s).
   They converge: score sources → generate → one compose file per artifact seam → publish →
   consumers `include:` what they want.
2. **Why they force each other:** score cannot express `profiles` or `AUTH_MODE`-style switches
   at all. Porting the stack to score *structurally requires* the artifact decomposition. The
   two initiatives are one program.
3. The user then built (through ELI5 rounds) a correct working model of score mechanics:
   provisioners, patch templates, the score-file-vs-provisioner seam, and workload-to-workload
   references via the built-in `service-port` provisioner. Those models are recorded in §5–§8
   so the next session doesn't have to re-derive them.
4. A sequenced roadmap with sizing exists (§9) and a list of decisions owed before starting (§10).

Not yet done: no design doc rewrite, no tickets checked/created (`linear` CLI not installed in
this sandbox), no code, no commits.

---

## 2. State of the world (verified this session)

### Repos / environment

- Repos live at `/workspace/<name>` in this sandbox (placeframe, docker-devkit, Make-it-Sing,
  placeframe-capture-tool, etc.), **not** at `/<name>` as the root `AGENTS.md` claims — that
  describes a different sandbox config.
- placeframe: branch `more-final-polish`, clean, 3 housekeeping commits ahead of `origin/dev`
  (dev is its ancestor). docker-devkit: branch `rename-folders`, synced with origin.
- placeframe pins `docker-devkit>=0.4.2` (uv.lock).
- `linear` CLI is NOT installed here — ticket linkage for the design doc unverified.
- The SaaS/Pulumi engineer's work is **not in this workspace** — coordination is external.
  (The k8s provisioner comments reference "the Pulumi program" creating `placeframe-secrets`.)
- `.pulsar/memories/score-poc.md` (referenced by stack/score/README) no longer exists.

### The artifact-split design doc is partially stale

`design/compose-artifact-split.md` predates two merged PRs: docker-devkit **#14** and
placeframe **#142**, both "Explicit compose profiles". What actually landed:

- `docker-devkit/src/docker_devkit/modes.py` was **rewritten, not deleted** —
  `resolve_auth_mode`/`VALID_AUTH_MODES` are gone; it now holds only
  `resolve_compose_profiles()` + `parse_env_file()` ("carries no consumer-domain knowledge").
- `up.py` has no keycloak knowledge; it forwards `COMPOSE_PROFILES` as explicit `--profile`
  flags and rejects unknown names. `down.py` enumerates all profiles for teardown.
- **`COMPOSE_PROFILES` is now the sole service selector** (keycloak profile gates keycloak +
  auth-initializer; `tunnel-ngrok`/`tunnel-rathole` gate tunnels). `AUTH_MODE` survives as a
  **runtime-only** string.
- The doc's Phase A (strip docker-devkit) is therefore **already done, differently than
  written**; its B5 pin-bump is moot (0.4.2 already required).

**Regression found:** the cleartext-OAuth guard (reject `http://` PUBLIC_URL + keycloak) was
dropped entirely in that cutover — nothing rejects it anywhere now. `workloads/AGENTS.md:79`
still claims the guard lives in `modes.py` — false. Restoring it inside the API's
`check_auth_config` is part of B1 (now a *restore*, not a move).

`AUTH_MODE` still threaded through: `compose.yml:194,262`, `.env.sample:6`,
`workloads/api/src/settings.py:12,49`, `auth.py:51`, `database.py:78` (plus `cast` violation at
`database.py:66`), `main.py:38`, `routers/server_info.py:20`, `workloads/gateway/entrypoint.sh:21,31-47`,
the whole score tier (api.yaml, gateway.yaml, config provisioner, both generated outputs),
`stack/score/README.md`, `packages/unity/Logging/AGENTS.md:31,80`, `workloads/AGENTS.md` (multiple).

### The three descriptions of the stack (today)

1. **Hand compose** (repo root): `compose.yml` (~20 services), `compose.postgres.yml`
   (standalone for preflight), `compose.cuda.yml`/`compose.rocm.yml` (GPU overlays; service
   names `reconstructor-cuda`/`localizer-cuda`, `gpus: all`, localizer gets network alias
   `localizer`), `compose.dev.yml` (bind-mount/debug overlay, never published). `uv run up`
   assembles these via `docker-devkit.yaml` `lifecycle.files` with `{gpu}` templating.
2. **Score tier**: `stack/score/` (authored) → `stack/generated/` (committed artifacts).
   Coverage is a deliberate slice: workloads `api.yaml`, `lease-server.yaml`, `gateway.yaml`;
   provisioners: `placeframe-postgres` (real PF postgres + database-manager create job +
   migrator job), `placeframe-s3` (fixed-name MinIO + mc bucket-init, overrides built-in),
   `placeframe-config` (pure env passthrough, no containers), `placeframe-keycloak` (minimal
   dev keycloak, no realm import). Plus k8s twins (`*.k8s.provisioners.yaml`) incl. a CNPG
   postgres variant. `generate-score` (docker-devkit `score_generate.py`) drives it: expands
   `${SHA}` placeholders from the bake manifest, inits state, generates both targets,
   sorts/normalizes for determinism, **deletes `.score-compose` state after** (relevant: score
   `files:` materialize under `.score-compose/mounts` — that mechanism is unusable here).
   Generation resolves from **committed** tree (`git ls-tree HEAD`): commit source, regenerate,
   commit artifacts. CI staleness gate is **disabled**; regeneration is manual.
3. **Published OCI artifact**: `scripts/src/scripts/publish_compose.py` (CI job
   `publish-compose` in `integrate.yml`) bakes compose+postgres+gpu-overlay per variant
   (var-substitute, `file:` configs → inline `content:`, image refs → digests) and publishes
   `placeframe-{cuda,rocm}:{sha,branch}`. **Make-it-Sing is the sole consumer**: single
   `include: oci://…placeframe-cuda@sha256:f15dc43f…` with `gateway`/`postgres` ports `!reset`,
   rathole `RATHOLE_SERVICES` override, its own livekit tier. (Note: the design doc references
   this script at `build/src/...` — it moved to `scripts/`.)

### Load-bearing defect found in the score tier

`api.yaml` feeds the api `MINIO_ENDPOINT_URL`/`MINIO_ACCESS_KEY`/`MINIO_SECRET_KEY` — but
`workloads/api/src/settings.py` reads `S3_ENDPOINT_URL`/`S3_ACCESS_KEY`/`S3_SECRET_KEY` (zero
minio references in api source). **Object storage is silently unconfigured in BOTH generated
renderings — compose and the k8s manifests the SaaS engineer is building on.** Fixing the
resource-output→env mapping (platform-neutral S3 resource outputs, not MINIO_* names) is an
early, load-bearing step of the port, plus a heads-up to that engineer.

### Other gotchas pinned this session

- Unpinned images in generated tier: `alpine` (wait-for-resources gate), CNPG operand image
  (`placeframe-postgres-cnpg:14-trusted`, not registry-hosted). Violates pin-everything law;
  must fix before the tier becomes load-bearing.
- docker-devkit `rename-folders` branch moves config defaults to `images/images.yml` +
  `deployfiles/score` + `deployfiles/generated/compose/compose.yaml` (placeframe today:
  `workloads/images.yml` + `stack/score` + `stack/generated`, no explicit path overrides in its
  `docker-devkit.yaml` generate-score section). Adopting that release implies the layout move
  (or explicit paths). Decide as part of this initiative.
- Pinned tools: score-compose **0.42.0**, score-k8s **0.15.0** (versions matter — output
  differs between releases).
- `parse_env_file` (docker_devkit.modes) has placeframe consumers: `scripts/.../api_auth.py`,
  `sweep_postprocess.py` — relevant if anyone deletes modes.py later.

---

## 3. Target state (the converged picture)

```
stack/score/*.yaml          authored once per workload (+ provisioners per platform)
        │  generate-score
        ▼
stack/generated/compose/    one generated compose file per artifact seam
   core-<gpu> / edge-keycloak / edge-anonymous / tunnel-ngrok / tunnel-rathole
        │  publish-compose (bake: inline configs, pin digests)
        ▼
ghcr OCI artifacts          five (core per GPU variant; edges/tunnels variant-agnostic)
        │  include: oci://…
        ▼
consumers                   Make-it-Sing = core-cuda + edge-keycloak + tunnel-rathole + own services
                            air-gap demo = core + edge-anonymous
                            local dev   = whatever docker-devkit.yaml lists (uv run up unchanged)
```

- The 5-artifact table and structural rules (each artifact owns services wholly; gateway lives
  in the edge artifacts; auth presence = which edge you include) come straight from
  `design/compose-artifact-split.md` and remain valid.
- Consumer model: cross-repo consumers include **published OCI artifacts derived from**
  `stack/generated/compose` (they cannot include files from placeframe's tree). The user's
  phrase "compose-of-composes from that folder" was interpreted this way — the one flagged
  ambiguity of the session.
- k8s (SaaS/Pulumi) is the second rendering of the same sources and rides along — and
  constrains the refactor window (every score-tier change alters their input).
- The artifact-split doc should be **rewritten** to target score-generated sources before the
  port starts (its B3 hand-split becomes generated split; spec-first per repo law).

---

## 4. Is it possible? (research results, verified)

Score spec (v1b1) expressible: containers (image, command, args, variables, files, volumes,
resource limits, liveness/readiness probes, `before` ordered-start), service ports, resources.
What it cannot express and where it goes:

| Concern | Mechanism |
|---|---|
| Profiles / mode switches | Impossible — replaced structurally by which artifact you include (the point) |
| Backing infra (postgres, s3, keycloak, seaweedfs, loki, …) | provisioner `services:` — arbitrary raw compose |
| restart policy, `gpus: all`, exec healthchecks, network aliases, env-parameterized published ports | patch templates (JSON-patch on generated output) |
| Runtime `.env` holes in output | provisioner `outputs:` only place `${VAR:?err}` survives verbatim (score's own `${}` is generation-time) |
| Workload→workload address | built-in `service-port` provisioner (lookup, no file needed) |
| Cross-workload startup ordering | Not a concept. Drop (poll-retry absorbs it) or thin custom provisioner. `before` is intra-workload only and postdates the pinned score-compose (PRs score-compose#454, score-k8s#294) |
| Probes → compose healthchecks | score-compose **validates probes and ignores them** (issue #86; "cannot reliably convert httpGet→exec"). Patch template emits the healthcheck instead (api image has python; hand check is CMD python urllib) |
| Top-level compose `configs:` | Nothing in score emits them (provisioners CAN emit `networks:`/`volumes:`/`services:`/`files:`, not `configs:`). Use bind-mount of committed repo path in provisioner service for local dev; publish step converts bind→content-config |
| `docker compose publish` | refuses bind mounts — hence the bind→content conversion is mandatory before publishing any file-carrying service |
| Cross-include `depends_on` | included files are validated standalone → dangling refs error; `required: false` tolerates absence (hand compose already uses this for keycloak) |

**Can generated compose equal hand `compose.yml` in contents?** Semantically yes (fixed delta
list, each with a designated escape hatch); byte-for-byte no — three unavoidable structural
deltas: (1) workload services are named `<workload>-<container>` (`api-api`) — either update
references (gateway Caddyfile proxies `api:8000`) or one-line alias patch
`services.api-api.networks.default.aliases: [api]`; (2) every workload gets exactly
`depends_on: wait-for-resources` instead of direct cross-workload edges; (3) `required: false`
softness becomes structural (provisioner absent from the generation), which is the desired
artifact-split behavior anyway.

---

## 5. Score mechanics — the mental models established (ELI5 recap)

### Demand and supply

Score files are the **demand side** (a workload + abstract resources it needs); provisioner
files are the **supply side** (how this platform provides one resource type). Join key =
`type` in `resources:`. Many-to-many: api.yaml touches all four provisioners; postgres
provisioner serves api+lease-server (shared via identical `id: placeframe-db`; resource
identity = `type.class#workload.resource_name`, `id` = cross-workload sharing). The two file
sets being disjoint in the current slice is NOT coincidence: everything placeframe authors
became a workload; third-party infra became provisioned resources. A service appears on both
sides only when (a) an app-workload is the answer to another workload's question
(`service-port`), or (b) it straddles the app/infra line (keycloak) and a side was chosen.

### Generation = two pipelines, one output

```
score-compose generate
├── score files ──▶ CONVERTER ───▶ workload services (api-api, gateway-gateway, …)
└── resources  ──▶ PROVISIONERS ─▶ infra services (pf-postgres, minio, keycloak, jobs…)
                        └─ outputs also fill the ${resources.*} holes in workload services
```

Plus score-compose auto-builds the `wait-for-resources` gate every workload depends on
(conditions derived from provisioner services' healthchecks/completion).

### The three tests that draw the score-file/provisioner/patch seam

1. **Platform variance**: "would this statement still be true on another platform?" → yes:
   score file; no: provisioner.
2. **Spec coverage**: workload-adjacent but docker-only deployment detail (restart, gpus,
   healthcheck, aliases) → patch template (no spec word exists, by design).
3. **Resolution time**: generation-time baking (image SHAs) vs runtime `.env` holes
   (credentials, PUBLIC_URL) — runtime holes only survive via provisioner outputs inserted
   verbatim. This is the entire reason `placeframe-config` exists (it provisions nothing; it's
   the `${VAR:?err}` passthrough valve).

A score file is the **intersection** of all platforms, not a thinner compose. Fat provisioners
are the design working: they carry the per-platform knowledge with no other home.

### Provisioner anatomy (compose target)

Fields: `uri`, `type` (matching key), `state` (persisted constants), `init`, `shared`,
`outputs` (fill the workload's holes; inserted verbatim so `${VAR}` survives to runtime),
`directories`, `files`, `networks`, `volumes`, `services` (raw compose spliced into output —
anything compose can do), `info_logs`, `supported_params`, `expected_outputs`. Go text/template
+ Sprig. k8s twins: same types, `manifests:` instead of `services:`, secrets as
`{{ encodeSecretRef "placeframe-secrets" "KEY" }}` instead of `${VAR}` holes. Custom
provisioners override built-ins first-match (that's why fixed-name MinIO beats the random
built-in s3).

### Patch templates

Registered at `init --patch-templates`; run after conversion+provisioning, before write; each
is a Go template emitting an array of `{op: set|delete, path: dot-path, value}` applied to the
compose. Sees `.Compose` and `.Workloads` so it can loop/conditionalize. Current repo example:
`stack/score/restart-policy.tpl` (`set services.api-api.restart = unless-stopped`) — the
degenerate static case. **Coupled to generated names** — patches must compute `<workload>-<container>`
names, never hardcode. This is the designated home for GPU (`gpus: all`), healthchecks-from-probes,
aliases, etc.

### Workload→workload references (service-port)

When workload A needs workload B (both first-party), B needs **no provisioner file**.
`resources: X: {type: service-port, params: {workload: B, port: <port name>}}` — a **built-in**
provisioner (ships in `zz-default.provisioners.yaml`) answers by pure lookup in generation
state (`.WorkloadServices`), emitting only `host: <B's generated service name>` +
`port: <translated targetPort>`, creating nothing. Rule: author a provisioner file only when
the answer requires creating things or nontrivial derivation; pure address translation is
built-in. **Address discovery ≠ ordering**: A gets B's address but does not wait for B. (A
community `service` provisioner is even barer — outputs just the name.)

---

## 6. Where each hand-compose feature lands in the end state

| Hand compose content | Score-world home |
|---|---|
| api, lease-server, gateway, reconstructor, localizer, ngrok, rathole | score workload files (env via config-provisioner holes) |
| seaweedfs stack, cloudbeaver, initialize-*, create-database, migrator, keycloak, auth-initializer, loki/alloy/grafana + initialize-loki | provisioner `services:` (healthchecks, depends_on chains, jobs all fine there) |
| api/lease-server depends_on (init-s3/migrator completed, keycloak healthy) | wait-for-resources gate (derived from declared resources) |
| Healthchecks on workload services | patch template (probes ignored by score-compose) |
| `gpus: all`, restart, localizer alias | patch templates |
| `configs:` (loki/alloy/grafana) | bind-mount committed repo path in provisioner service (local) → bind→content conversion at publish |
| `${GATEWAY_PORT}` published ports | small divergence: `--publish` bakes numbers at generation; patch to re-inject holes if parity wanted |
| `profiles:` | gone — replaced by artifact seams |
| `AUTH_MODE` | gone — B1 refactor (`AUTH_ISSUER_URL` presence) + structural edge choice |

---

## 7. The B1 API auth refactor (unchanged from the design doc, needed under every end state)

- `settings.py`: delete `auth_mode`; keep five `auth_*` optional; `check_auth_config`: issuer
  set ⇒ other four required; unset ⇒ all None; **restore cleartext-OAuth guard here** (issuer
  set + `public_url` scheme http ⇒ raise).
- `auth.py`: backend selected by `settings.auth_issuer_url is not None`; anonymous backend
  returns `(SHARED_ANONYMOUS_USER, SHARED_ANONYMOUS_TENANT)`; JWKS flow otherwise.
- `database.py`: delete `auth_disabled` branch (78–89); uniform `(user_id, tenant_id)`
  handling; fix the `cast` at line 66; move `SHARED_ANONYMOUS_TENANT` into anonymous backend.
- `main.py:38` and `routers/server_info.py:20`: condition becomes `auth_issuer_url is None`;
  `/server-info` keeps `auth_mode` field/values (client contract unchanged, no codegen).
- Grep tests for `AUTH_MODE` → set/unset `AUTH_ISSUER_URL`.
- Open decision inherited from the doc: derive `AUTH_CERTS_URL` from `AUTH_ISSUER_URL` +
  internal keycloak host (preferred; shrinks consumer env) vs keep explicit.

---

## 8. GPU variants (separate problem, three options)

1. **Per-variant generated core** (recommended; matches artifact-split's `placeframe-core-<variant>`):
   generation parameterized by variant; `{gpu}` templating in `lifecycle.files` picks the file.
   Score frees the per-variant service-name ugliness — service stays `reconstructor`, only
   image + device patch differ.
2. Tiny generated GPU overlay on one core (closest to today).
3. Image-by-env injected by `up` (docker-devkit already injects shas into env) — still needs a
   devices overlay, so it half-reverts to 2.

---

## 9. Roadmap (sequenced lift)

1. **B1 API auth refactor** — day; needed everywhere; also de-AUTH_MODEs the score tier's
   config provisioner; restore the lost guard.
2. **Finish the score port** (the bulk; weeks):
   - Slice A: fix S3 env mapping (platform-neutral S3 resource outputs; seaweedfs-provisioner
     for compose, minio for k8s — idiomatic score); decide SeaweedFS-vs-MinIO-for-dev; heads-up
     to SaaS engineer.
   - Slice B: observability (loki/alloy/grafana; inline/bind-mounted configs; forces the
     bind→content publish transform; initialize-loki chown sidecar).
   - Slice C: long tail (seaweedfs stack, cloudbeaver, auth-initializer, ngrok, rathole).
   - Slice D: reconstructor + localizer (GPU patch, alias or renamed references,
     service-port for lease-server/localizer wiring).
3. **Seam generation + multi-artifact publish** (retarget doc's B3+B4 at generated sources;
   couple days): generate-score emits one compose per seam (simplest: multiple score-compose
   generations with subsetted workload lists); publish-compose publishes 5 artifacts; edge
   pair = two generations differing in keycloak provisioner + auth snippet configs presence.
4. **Cutover** (day + coordination): lifecycle.files → generated files; delete hand compose;
   Make-it-Sing 1→3 includes; `.env.sample` drops AUTH_MODE/COMPOSE_PROFILES; `uv run up` UX
   unchanged.
5. **k8s rides along + housekeeping**: sync with SaaS engineer per step; resolve staleness-gate
   question (manual two-commit dance vs CI-enforced once generated compose is the stack); pin
   `alpine` + CNPG operand; decide docker-devkit layout adoption (`deployfiles/` rename);
   rewrite `design/compose-artifact-split.md` to score sources (do this before step 2, spec-first).

Survives untouched: `compose.dev.yml` role (hand overlay on generated files, never published),
`uv run up/down` UX, image build pipeline, images.lock, preflight's compose.postgres.yml role
(re-think during cutover).

---

## 10. Decisions owed before starting

1. SeaweedFS vs MinIO for the generated compose tier.
2. GPU shape (recommend per-variant generated core).
3. `AUTH_CERTS_URL` derivation vs explicit env.
4. Regeneration cadence once generated compose is load-bearing (manual vs CI gate).
5. SaaS engineer's coordination window (their work consumes every step's output).
6. Rewrite the design doc (and its Linear ticket linkage — `linear` unavailable here to verify).

---

## 11. Key file map

| Path | What |
|---|---|
| `design/compose-artifact-split.md` | the initiative doc (partially stale; §2 above) |
| `compose.yml`, `compose.{postgres,cuda,rocm,dev}.yml` | hand stack (to be replaced) |
| `docker-devkit.yaml` | lifecycle.files + generate-score config (no path overrides) |
| `workloads/images.yml` + `images.lock` | bake manifest + third-party pins |
| `stack/score/*.yaml` | authored score workloads + provisioners (compose + k8s) |
| `stack/generated/compose/compose.yaml`, `stack/generated/k8s/manifests.yaml` | committed generated artifacts |
| `stack/score/README.md` | the tier's own docs (deploy commands, gaps, CNPG notes) |
| `scripts/src/scripts/publish_compose.py` + `scripts/tests/test_publish_compose.py` | artifact publish (moves to 5-artifact) |
| `/workspace/docker-devkit/src/docker_devkit/score_generate.py` | the generator wrapper |
| `/workspace/docker-devkit/src/docker_devkit/{up,down,modes,lifecycle,config}.py` | lifecycle tooling |
| `/workspace/Make-it-Sing/compose.yml` | the one artifact consumer today |

## 12. Suggested continuation

Likely next moves, in order: (1) rewrite `design/compose-artifact-split.md` to target
score-generated sources and re-sequence per §9 (spec-first); (2) verify/create the Linear
ticket linkage; (3) execute B1 (self-contained, shippable); (4) sync with the SaaS engineer on
the MINIO_* finding before touching slice A.
