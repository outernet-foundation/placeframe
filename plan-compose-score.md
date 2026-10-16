# Compose → score initiative plan

The remaining work to reach the end state: no hand-authored compose files — the stack is
score-generated in `stack/generated/compose`, decomposed into five published OCI artifacts,
and consumers assemble their own backend by `include:`-ing artifacts instead of flipping
`COMPOSE_PROFILES`/`AUTH_MODE` switches. The k8s manifests (SaaS/Pulumi tier) are the second
rendering of the same score sources and ride along.

Replaces `compaction.md`, `plan-auth-refactor.md`, and `design/compose-artifact-split.md`
(all deleted; B1 is shipped; the artifact table and structural rules are carried below).

## Settled — do not re-litigate

- **Auth is structural.** `AUTH_ISSUER_URL` presence selects OIDC vs anonymous inside the api
  (B1, shipped). Issuer set requires `AUTH_JWKS_URL`/`AUTH_AUTHORIZATION_ENDPOINT`/
  `AUTH_TOKEN_ENDPOINT` (explicit — split-horizon kills discovery; no derivation); issuer +
  cleartext `http://` PUBLIC_URL is a boot error. `/server-info`'s `auth_mode` wire values
  unchanged.
- **Object storage is SeaweedFS everywhere.** MinIO is dead in both tiers. The fixed-name
  MinIO provisioners existed only because loki's config once hardcoded `minio:9000`; loki
  now addresses `seaweedfs:8333` and the score `s3` provisioner stands up SeaweedFS at the
  fixed names `seaweedfs`/`seaweedfs-audit` (the entrypoint wrapper's rendered fluent sink
  and loki's config reach them by DNS name).
- **The hand compose files are dead from work item 1 onward.** No work item spends effort
  keeping them coherent; intermediate breakage is accepted, not repaired (B2's entrypoint,
  for instance, leaves the hand gateway without auth routing, and nobody wires snippets into
  `compose.yml`). The files stay on disk only as porting references for the slices and are
  formally deleted at cutover. This initiative is one unified project, not a compatibility
  bridge.
- **Generated compose is hermetic at rest: zero host-filesystem references.** score-compose
  materializes workload `files:` as bind mounts into its gitignored `.score-compose` state
  dir — its model is generate-and-run-here, incompatible with committed/published artifacts.
  The bridge is a docker-devkit `generate-score` post-pass that rewrites every bind into a
  top-level `configs.content` entry, doubling each `$` (the rule `publish_compose.py`'s
  `_inline_configs` already uses — compose interpolation would otherwise eat both loki's
  `${VAR}` and caddy's `{$VAR}` before the container sees them). A bind surviving in a
  generated compose is an artifact bug. Patch templates cannot host this conversion (no disk
  access; `.Workloads` carries literal content only).
- **Auth snippets ride as score workload `files:` with literal content in `gateway.yaml`** —
  one source for both renderings: score-k8s emits ConfigMap+mounts natively; score-compose's
  bind output feeds the generation converter.
- Score tools pinned: score-compose 0.42.0, score-k8s 0.15.0 (output differs across
  versions). `ensure_score_tools` (revived, extended to fetch a pinned helm) makes the
  tools appear on a fresh machine/CI runner; until its release they are hand-fetched onto
  PATH.
- Generation resolves image SHAs from the **committed** tree: commit sources, regenerate,
  commit artifacts.
- **Infra authoring layers by category** (decided post-cleanup, gates Slice B): score
  stays the workload tier; stateful infra goes operator-first (postgres via CNPG at
  promotion time, keycloak via its official operator at the edge work item); third-party
  stamp-outs go Helm charts rendered by `helm template` inside docker-devkit's
  generate-score — helm is a renderer, never a deployer. Everything renders at generation
  into the committed deterministic `manifests.yaml`; Argo never knows helm exists.
  Operators are cluster preconditions installed by the Pulumi/infra layer (same class as
  the Hetzner CSI driver); their CRs are ordinary manifest content. Kustomize is
  permanently out — variation is already handled by generation (env holes, `--local`,
  storage classes). Charts follow the image laws: digest-pinned, mirrored to the org
  namespace. Chart values never carry secrets — charts reference existing Secrets
  (`placeframe-secrets` pattern).
- **GPU shape: per-variant generated core.** The service stays `reconstructor`; each
  variant generation substitutes the variant image + device patch, producing
  `placeframe-core-cuda` / `placeframe-core-rocm`. Accelerator choice is which artifact a
  consumer includes — never a runtime switch (same model as the edge pair).

## Current state

- B1 complete on `more-final-polish` (API, compose.yml, .env.sample, score tier, docs;
  Make-it-Sing env sample conformed; OidcAuthBackend named for the protocol, not provider).
- **Work item 1 shipped (a–d)**: the converter is released — docker-devkit 0.4.4 (branch merged
  via PR #16 after review squash + rebase onto origin/dev, which carries PR #15's per-run state
  model: state dirs torn down post-generation, instance suffixes hash-normalised). placeframe
  pinned it (`uv lock --upgrade-package docker-devkit`, `requires: ">=0.4"` admits it) and
  regenerated both artifacts through the released tool — compose hermetic (zero binds, snippets
  inlined as `configs.content`), k8s ConfigMaps native, no `AUTH_MODE` in either rendering, and
  `stack/generated/k8s/.score-k8s/state.yaml` gone from the tier (expected under the new model).
  Known debt riding the release: the inliner and uid-normalisation carry only volume-model
  typing tests in docker-devkit.
- **Slice A shipped (work item 2)**: `api.yaml` feeds `S3_ENDPOINT_URL`/`S3_ACCESS_KEY`/
  `S3_SECRET_KEY` from the s3 resource (the MINIO_* defect is gone). Both MinIO
  provisioners deleted, replaced by `compose/seaweedfs.yaml` (weed
  server + admin console + audit relay + s3-initializer, ported from the hand compose
  corpse; credentials as `${S3_*:?err}` holes) and the k8s twin
  `k8s/seaweedfs.yaml` (Service + StatefulSet, audit relay
  Deployment + Service, s3-initializer bucket Job with `S3_*` secretKeyRefs; no admin
  console — k8s publishes no host ports). Score resource type `placeframe-keycloak` →
  `oidc-issuer` (the api
  resource id stays `placeframe-keycloak` — an id names the instance, not the
  implementation). Artifacts regenerated through the released converter: zero minio
  references, zero binds, deterministic across fresh runs. Loki's config was already on
  `seaweedfs:8333`; the generated tier now matches it via the provisioner endpoint.
- **docker-devkit re-pinned to 0.4.6** (the chart-render release; first `uv lock
  --upgrade-package docker-devkit` resolved 0.4.5 from a not-modified cached simple-index —
  `uv cache clean docker-devkit` fixed it). Both artifacts regenerated byte-identical
  through the released pin, as predicted; the lock bump does not feed service image globs,
  so no tree-tag movement and no artifacts commit. Per-service pylocks unaffected.
- **Slice B shipped (compose half + all k8s authoring)**: `compose/observability.yaml`
  (loki/alloy/grafana + initialize-loki chown sidecar, config binds of the committed
  `workloads/*/config.*` inlined `$`-doubled by the converter, `${LOKI_IMAGE:?err}`-style
  runtime holes, loki-data volume), `k8s/observability.yaml` (alloy Deployment + Service +
  ConfigMap; loki/grafana arrive via charts), workload wiring (`observability` resource
  type, id `placeframe-observability`, declared by api + lease-server feeding
  `loki_url`/`otlp_endpoint`), and the alpine pin
  (`compose/wait-for-resources-image.tpl` patch template → `${ALPINE_IMAGE:?err}`;
  ALPINE_IMAGE was already declared/locked). Compose artifact regenerated: deterministic
  across fresh runs, zero binds, `docker compose config`-valid, preflight exit 0.
- **Slice B deviations from the anticipated shape**: the grafana chart's newest release
  (10.5.15) is flagged deprecated, so the pin is **10.5.14**
  (`sha256:161aa072…0764e`) — the last non-deprecated; loki is the planned 7.3.0
  (`sha256:ba8b6b3e…d2f8`). **Alloy's chart has no OCI artifact** (ghcr.io/grafana/alloy
  and ghcr.io/grafana/helm-charts/alloy both "repository not known") — ChartConfig requires
  digest-pinned OCI refs, so alloy's k8s half is hand-written (the seaweedfs twin pattern)
  with a ConfigMap body mirroring `workloads/alloy/config.alloy` by hand (drift risk noted
  in stack/AGENTS.md). Loki chart gotchas folded into `values/loki.yaml`: singleBinary
  reads its own `extraArgs`/`extraEnvFrom` (not global — only the distributed templates
  concat global), `-config.expand-env=true` + `extraEnvFrom: placeframe-secrets` carries the
  S3 credentials as `${S3_*}` config holes (the chart's sanctioned pattern), and
  SimpleScalable targets must be zeroed or chart validation fails. Test pods, canary,
  gateway, memcached caches, and the rules sidecar all disabled in values; every rendered
  image lands as a mirror digest. Grafana k8s gets admin creds from `placeframe-secrets`
  (**new keys `GRAFANA_ADMIN_USER`/`GRAFANA_ADMIN_PASSWORD`** — k3d recipe and the Pulumi
  list updated) and no anonymous access, unlike the compose dev stack.
- **k8s artifact regeneration is pending the CI mirror job**: `helm template` pulls the
  org-mirrored form of each chart ref, and the mirror job has not copied loki/grafana yet
  (declare → mirror job → generate; single-writer law — no local mirror push from the
  sandbox). Values were validated against upstream refs directly (rendered output audited:
  Services `loki:3100`/`grafana:3000` match the gateway Caddyfile; single mirror-digest
  image per chart). After the operator pushes and the mirror job runs, `uv run
  generate-score --target k8s` unblocks; the k8s artifact is stale in the interim (expected
  mid-initiative).
- Resumption facts: the pinned score tools, helm v3.22.1, and the repo-pinned uv 0.12.15
  all live in `~/.local/bin`, which is not on the sandbox's default PATH
  (`export PATH="$HOME/.local/bin:$PATH"`; the system uv 0.11.14 cannot read the lock).
  Regeneration is plain `uv run generate-score` from the placeframe root and is deterministic
  across fresh runs; commit sources first, then regenerate, then commit artifacts. The
  branch's commits are unpushed until the operator pushes (sandbox has no push scope);
  hand off branch + HEAD at each session end. At this session's close: placeframe
  `more-final-polish` is 15 commits ahead of origin once this close-out record commits
  (the 13 inherited from the prior session plus this session's two plan records: the
  inclusion build and the audit absorption; the audit itself changed nothing outside
  the plan file — the working-tree inventory is unchanged). Operator pushes
  needed at close: placeframe `more-final-polish` (unblocks the CI mirror job for the
  two charts → k8s regen — push this now, it gates nothing else). docker-devkit `dev`
  is 4 commits ahead of origin (authoring format + inclusion, each code+docs) — the
  next session's lock-resolution code joins them BEFORE any push, and one patch
  release (0.4.7) carries all of it, unblocking the placeframe re-pin.

  The sandbox cannot fetch docker-devkit over its SSH remote —
  the bind-mounted checkout's refs are the truth (currently at `7d974c6`, 4 commits
  ahead of origin/dev: the authoring-format code + docs and the inclusion code + docs;
  one patch release carries all four). Placeframe's working tree holds the 10 migrated
  provisioner files plus the two include-migration edits (`k8s/observability.yaml`'s
  alloy ConfigMap body is now an `include:` marker; `k8s/values/grafana.yaml`'s
  datasources block an `include-yaml:` marker) — all uncommitted by design; they commit
  with the 0.4.7 re-pin.

- **docker-devkit file inclusion — implemented on `dev`, migration validated in-tree**:
  one shared resolver (`includes.py`), two consumers. The marker is a single-key plain-
  YAML mapping (lintability law): `include: <repo-root-relative path>` inserts file bytes
  verbatim as a string scalar; `include-yaml: <path>` parses the file and inserts the
  structure — two modes because grafana's chart renders datasources through
  `tpl (toYaml $value)` and mangles string values, while alloy's river config and the
  eventual loki full-override need bytes. Neither mode transforms content (`${S3_*}`
  holes survive untouched; `$` handling stays per-consumer). Repo-root anchoring with
  absolute/`..` rejection; missing files, non-string marker values, invalid/empty YAML
  includes, and cycles are loud errors; `include-yaml` trees resolve recursively with
  cycle detection, text content is never scanned. Consumer 1: the compile pre-pass
  resolves markers before validation (`compile_provisioner_document` gained a `root`
  param, as did `compiled_provisioners`). Consumer 2: `resolved_values_path` passes a
  marker-free values file through as the committed path and otherwise writes an
  include-resolved copy into the per-run tempdir (subpath preserved, so same-named files
  cannot collide) for `helm template --values`. 187 devkit tests green (+22), ruff +
  basedpyright strict clean. Acceptance: `--with file://` compose regeneration
  reproduced the committed artifact **zero-diff** with the resolver in the pipeline
  (compose provisioners carry no markers — binds carry their content, as designed).
  Placeframe-side authored changes rode the working tree (see resumption facts). The
  k8s rendering gets its first full exercise of inclusion at the post-mirror regen:
  assert there that the rendered alloy ConfigMap equals `workloads/alloy/config.alloy`
  and grafana's datasources ConfigMap equals the committed datasources file (already
  noted in the regen step).

- **Dedup audit + prior-art survey (research session; nothing outside this plan file
  changed)**: two read-only audits ran after the inclusion build. The dedup audit
  found two **live** drifts (stack/AGENTS.md's k3d mint recipe omits `AUTH_AUDIENCE` —
  pod-failing `CreateContainerConfigError`; the bucket set already diverged —
  `dev-reconstructions` compose vs `reconstructions` k8s, with `dev-captures`
  hardcoded in api source for both tiers), one large remaining hand-copy
  (`values/loki.yaml` mirrors `workloads/loki/config.yaml` near-verbatim — the alloy
  failure mode; closable via the chart's `loki.config` full-override), and a
  digest-duplication class (five hand-written mirror digests in k8s sources + a
  keycloak literal on the compose side; no cross-file checker exists today). Verified
  single-sourced and closed: gateway snippets, audit sink, env-var names, alpine pin.
  Catalogued as deliberate pair-variance (not closable by design): `${VAR:?err}` vs
  `secretKeyRef` wiring, chart probes vs compose healthchecks, host ports, grafana
  auth modes, the CNPG twin. Every structurally correct closure the audit surfaced is
  absorbed into the work items — mechanical fixes + preflight guards + devkit
  lock-resolution + source migrations (item 4), bucket contract (item 5), Slice C
  riders (item 6), Slice D riders (item 7) — with the two genuine decisions
  (bucket naming, devkit publishing) branched under Open decisions. The prior-art
  survey's verdict feeds the publishing decision: parts precedented, the integrated
  whole not — the differentiators worth leading with are the deterministic committed
  dual artifacts, hermetic zero-host-ref compose, and lock-coupled fail-closed mirror
  governance.
- **Next session, in order**:
  1. ~~docker-devkit provisioner authoring format~~ **done** (rides the pending 0.4.7).
  2. ~~docker-devkit file inclusion~~ **done** (same release).
  3. **Audit-hardening batch, mechanical half (work item 4a)**: the stack/AGENTS.md
     `AUTH_AUDIENCE` fix lands as its own prose commit immediately; the dead
     `BUCKET` constant deletion and the lease-server `DEPLOYMENT_ENVIRONMENT` fix
     land as code commits (both re-stale the compose artifact's api/lease-server
     tree-shas — accepted; regen rides the re-pin); the keycloak lock-hole edit and
     the `| default` drops ride their already-dirty wait-set files. Add the two
     preflight guards to `scripts/preflight.py` (digest-equality; secrets-contract)
     — both pass on the current tree; verify with `uv run --locked
     scripts/preflight.py`.
  4. **docker-devkit lock-resolution (work item 4b)**: design the marker shape,
     implement + test (provisioner manifests and the chart-values pre-pass both
     resolve against `workloads/images.lock`), AGENTS.md row, commit on `dev` —
     folds into the pending 0.4.7, which now carries three features and still waits
     on this before the operator push.
  5. **Migrate k8s sources to lock refs + loki single-source attempt (work item 4c)**:
     replace the five hand-written digests with lock refs; switch `values/loki.yaml`
     to the `loki.config` full-override include — both ride the working tree, all
     committing with the re-pin.
  6. **Re-pin + commit the migration**: once 0.4.7 lands (now authoring format +
     inclusion + lock-resolution), `uv cache clean docker-devkit` then
     `uv lock --upgrade-package docker-devkit` (per-service pylocks expected
     unaffected), re-run `uv run generate-score --target compose` against the already
     migrated working tree (confirm zero diff again through the released pin), then
     commit sources + lock — the commit covers the 10 migrated provisioner files,
     the two include edits, the lock-ref migration, the loki values switch, and 4a's
     wait-set edits. Consider whether `requires` should move to `>=0.4.7` in the
     same commit (older devkits fail loudly on mapping-form sources, so the loose
     range is safe but noisy). stack/AGENTS.md gains the authored-format facts
     (mapping form is the authoring law; string form is compiler output; k8s config
     content arrives via inclusion, not hand mirrors — delete the alloy drift-risk
     note) with that commit.
  7. **Regenerate the k8s artifact** (needs the operator's placeframe push + the
     mirror job having copied the two charts — and the 0.4.7 re-pin, since the k8s
     sources now carry lock refs). `uv run generate-score --target k8s`, inspect the
     merged manifests (chart docs sorted beside the score docs; alloy twin present;
     no unpinned/unmirrored images), commit. Assertion list, in full: the rendered
     alloy ConfigMap equals `workloads/alloy/config.alloy`; grafana's datasources
     ConfigMap equals the committed datasources file; the rendered loki config
     semantically equals `workloads/loki/config.yaml` (the full-override composed
     with singleBinary — if the chart mangles it, revert to the structured values
     and add the semantic-diff preflight guard instead); every lock-resolved digest
     equals its `images.lock` entry (the preflight guard already checks this
     mechanically); pre-existing k8s content (postgres/seaweedfs/gateway/api)
     reproduces identically, with the chart + observability additions on top.
  8. **Bucket contract (work item 5)** — after the naming decision under Open
     decisions is made; small slice, order-flexible against 9.
  9. **Slice C (work item 6, with its audit riders)**, then Slice D (7), seam
     generation + publish (8), cutover (9).
- **Cleanup pass shipped (between Slices A and B)**: provisioners reorganised into
  `stack/score/compose/` + `stack/score/k8s/` with truncated names (`compose/seaweedfs.yaml`
  etc.; registration lists in `docker-devkit.yaml` are the authority — score tooling imposes
  no file-naming requirements on authored sources). `AUTH_JWKS_URL` fixed from a baked
  keycloak literal to a passthrough in both renderings (the api's `check_auth_config` boots
  anonymous mode only when issuer and endpoints are all empty — the baked URL crashed
  anonymous boots). Vestigial efs mounts and all restart keys dropped; CNPG Jobs got Argo
  sync hooks; the k8s seaweedfs StatefulSet got a readiness probe mirroring the compose
  healthcheck; `restart-policy.tpl` deleted. `stack/score/README.md` replaced by
  `stack/AGENTS.md` + `CLAUDE.md` import. Pending: docker-devkit's `image_globs` went
  recursive (dev @ 90aad4d, unpushed) so preflight's unpinned-image scan covers the moved
  files — re-pin (`uv lock --upgrade-package docker-devkit`) once released.
- **Pulumi follow-up — deferred until the rest of this plan completes** (external):
  `placeframe-secrets` gains `AUTH_ISSUER_URL` + `AUTH_JWKS_URL` +
  `AUTH_AUTHORIZATION_ENDPOINT`/`AUTH_TOKEN_ENDPOINT` + `S3_ACCESS_KEY`/`S3_SECRET_KEY` +
  `GRAFANA_ADMIN_USER`/`GRAFANA_ADMIN_PASSWORD` (the k8s grafana chart reads its admin
  credentials from the Secret), and drops `AUTH_URL`/`AUTH_TOKEN_URL`, `MINIO_ACCESS_KEY`/`MINIO_SECRET_KEY`, and (already
  safe — the generated manifests no longer reference it) `AUTH_MODE`. The dev-stack Pulumi
  config keys feeding `pf-secrets` (e.g. `placeframe:minioSecretKey`) rename to their `s3*`
  spellings in the same pass — the camelCase→SNAKE mapping in `secrets_exec.py` then
  yields the S3_* env names the stack now reads. The SaaS engineer sync for Slice A is
  this secret-key contract plus the storage swap (SeaweedFS StatefulSet + audit relay +
  bucket Job in the manifests, api env MINIO_*→S3_*) — surfaced here; the manifests
  themselves are already regenerated. Findings from his `placeframe-pulumi` branch
  (checked 2026-10, may be stale): his `placeframe-secrets` block predates Slice A
  entirely (still MINIO_*/AUTH_MODE/AUTH_URL); his Argo Application points at
  `score/deploy` on placeframe `main` — a path that exists nowhere (his "score-split"
  hasn't landed; this branch carries `stack/generated/k8s/manifests.yaml`) — so the Argo
  source path needs reconciling at merge; his `reconstructor.py` hardcodes the
  StatefulSet DNS name `pf-postgres`. **k8s postgres stays the StatefulSet provisioner
  until the CNPG package is agreed with him.** CNPG promotion prerequisites when that
  happens: slim `k8s/postgres-cnpg.yaml` (its minted passwords break determinism and
  commit secret values into emitted manifests — latent while unregistered), host +
  digest-pin the `14-trusted` operand image (operator action; CI token cannot push to
  the placeframe ghcr namespace), operator install in Pulumi, `pf-postgres` →
  `pf-postgres-rw` DNS sync in `reconstructor.py`, and a PG-14-vs-compose-tier
  major-skew check.
- **Generated-compose smoke test passed (both auth modes, first runtime validation)**:
  anonymous boots `auth_mode:"disabled"`, OIDC boots `auth_mode:"keycloak"` with
  unauthenticated `/capture_sessions` → 401 (the `AUTH_JWKS_URL` passthrough holds at
  runtime); gateway proxies the api (`/schema` 200) and `/auth/*` → keycloak (302); all
  one-shots (create/migrate/initialize-s3/wait-for-resources) exit 0. The token flow is
  unexercisable — auth-initializer (realm import) is Slice C, so keycloak has no
  `placeframe-dev` realm. Smoke fixes shipped: stack/AGENTS.md swagger URL corrected
  (`/schema`, not `/schema/swagger`) and the image prerequisite documented (fresh
  `tree-<sha>` tags must exist before `up` — api/gateway were unbuilt; `uv run build -t
  api -t gateway --gpu none`). Teardown side effect: `down --remove-orphans` also removes
  the hand `compose.postgres.yml` postgres (shared project name `placeframe`; its data
  volume survives). Keycloak admin/admin creds in the compose provisioner match the hand
  stack's posture — not a defect.
- **docker-devkit chart-render step implemented (next item 1 done, awaiting release)**: `dev`
  @ `01b0565` (code `8a77a61` + AGENTS.md docs), unpushed. `ScoreConfig` gains `charts:`
  (digest-pinned upstream-native OCI refs, parse-time validated; unique names;
  per-chart values files + optional namespace) and `helm_version` (required with
  charts); `generate-score --target k8s` runs `helm template` against the
  **org-mirrored** form of each ref (mirror section required — no mirror, no charts)
  and merges the blocks into the same kind/namespace/name-sorted `manifests.yaml`.
  Tool pinning flows through one shared policy: `tool_requirements(config, target)`
  (public, `ToolRequirement` descriptors carrying binary/version/release/archive/
  extract) feeds both the loud PATH gate inlined at the top of the `generate-score`
  CLI and `ensure_score_tools(config, bin_dir, target="both")` (fetches pinned
  helm beside the score tools; nested `linux-amd64/` member, strip-components).
  The `mirror` verb now copies chart declarations too (crane copies OCI charts
  byte-identically — the CI mirror job populates them, single-writer law intact).
  Smoke-verified end-to-end with helm v3.22.1: digest-pinned
  `oci://ghcr.io/grafana/helm-charts/loki@sha256:ba8b6b3ee954c9d6eeee713d148a22e6f73eb440189e11acd3112a06acdfd2f8`
  (tag 7.3.0) templates cleanly into `---\n# Source:` blocks, missing chart values
  (loki demands `storage.bucketNames` + schema config) fail loudly at generation.
  Helm current lines: v3.22.1 (v3 terminal) / v4.3.1 (v4 current) — Slice B pins
  explicitly; v3.22.1 is the smoke-verified one. Release handoff: operator pushes
  `dev` — now three commits ahead of origin/dev (code + docs + the operator's own
  `plan-image-identity.md` tree-tag audit, whose Part 1 defect is exactly the
  missing-`tree-<sha>`-tags failure the smoke test hit) — cuts the release, then
  `uv lock --upgrade-package docker-devkit` here (also closes preflight's scan gap
  over the moved provisioner files; re-run `uv run lock-python` if the workspace
  lock re-stales).
- **Provisioner authoring format — implemented on docker-devkit `dev`, migration validated
  in-tree** (designed prior session; built this session). docker-devkit `dev` carries two
  unpushed commits — `e11a790` (code: `provisioners.py` with `AuthoredProvisioner`,
  `extra="forbid"`, `state`/`outputs`/`volumes`/`services` as mappings, `manifests` as a
  list; the string-form law fires as per-field `mode="before"` validators, so pydantic
  wraps it into a loud `ValidationError`; `compiled_provisioners()` compiles into a
  per-run tempdir *under `score_dir`*, keeping `--provisioners` paths repo-relative;
  `ComposeDumper` moved there, imported back by the artifact dump; ~215 lines + ~250
  lines tests in `tests/test_provisioners.py`) and `ea8b55f` (AGENTS.md rows). Both
  renderings wrap init+generate in the compile; ruff + basedpyright strict + 165 tests
  green. The release does not ship alone: the file-inclusion step (next session's item 2)
  adds its commits on top of these before any push, and one patch release (0.4.7) carries
  both features — one placeframe re-pin covers them. Placeframe's 10 registered provisioner files are **migrated to
  mapping form in the working tree, uncommitted** — running
  `uv run --with 'docker-devkit @ file:///workspace/docker-devkit' generate-score
  --target compose` through them reproduced the committed compose artifact with **zero
  diff** (the acceptance test), and no tempdir residue remains. They stay uncommitted
  until the 0.4.7 re-pin: committing them against the 0.4.6 lock would leave the branch
  unable to regenerate its own sources (0.4.6 has no compile step and fails loudly on
  mapping form). `k8s/postgres-cnpg.yaml` is deliberately left in string form — it is
  unregistered and carries an `init:` block, a field the authored format intentionally
  does not model; registering it would hit the loud format law and force that decision.
  The k8s authored files compile (round-trip verified) but get their first full exercise
  at the k8s regen (the regen step below).
- Make-it-Sing still includes the old published bundle by digest; its new env names go live
  only when it re-pins (work item 7).

## Target: five artifacts

| Artifact | Contents | Variant-tagged |
|---|---|---|
| `placeframe-core-<variant>` | api, lease-server, postgres, seaweedfs, cloudbeaver, database-manager, database-migrator, loki, alloy, grafana, initialize-loki, reconstructor, localizer | yes (cuda/rocm) |
| `placeframe-edge-keycloak` | gateway (auth snippets mounted), keycloak, auth-initializer | no |
| `placeframe-edge-anonymous` | gateway (no auth snippets) | no |
| `placeframe-tunnel-ngrok` | ngrok | no |
| `placeframe-tunnel-rathole` | rathole-client | no |

The gateway lives in the edge, not core: artifacts own their services wholly (zero
cross-include overrides), core has no public surface on its own, and the auth choice is
which edge you include. The edge pair is two generations differing in keycloak provisioner
and auth snippet presence.

## Work items (ordered)

1. **B2 — gateway by file presence + generation hermeticity.** Three parts; (a) gates the
   regeneration, (b)/(c) are independent of it:
   a. **docker-devkit converter.** `generate-score` gains the bind→`configs.content`
      post-pass (+ tests; the zero-binds invariant above is its acceptance). Commit,
      hand off for push/release, then `uv lock --upgrade-package docker-devkit`.
   b. **Entrypoint rework.** `workloads/gateway/entrypoint.sh`: delete the AUTH_MODE
      branch, keep the PUBLIC_URL scheme/port parsing; export `FORWARDED_PROTO`/
      `FORWARDED_PORT` for the snippets to read via caddy's `{$VAR}`; `import
      /etc/caddy/snippets/site/*.conf` at site level and a `/etc/caddy/snippets/loki/*.conf`
      glob inside the static `handle /loki/*` (the loki proxy itself stays unconditional —
      anonymous clients push logs unauthenticated; only the `forward_auth` gate is
      snippet-borne). Verify caddy 2.8.4 treats no-match globs (missing dir included) as
      silent no-ops; gate on file presence if it warns.
   c. **Score sources.** `gateway.yaml`: drop `AUTH_MODE`; author the two snippet files
      (site/ + loki/) as literal `files:` content. Drop `AUTH_MODE` from the `.env` files.
      Hand compose untouched.
   d. **Regenerate** both artifacts (compose through the converter; k8s ConfigMaps native) —
      generator green. The k8s manifests stop referencing `AUTH_MODE`, clearing Pulumi to
      drop it from `placeframe-secrets`.
2. **Slice A — storage on SeaweedFS + provider-neutral edge.** S3 resource outputs feed
   `S3_ENDPOINT_URL`/`S3_ACCESS_KEY`/`S3_SECRET_KEY` (fixes the MINIO_* bug); SeaweedFS
   compose provisioner (weed server + admin console + audit relay + s3-initializer/
   bucket-init, ported from the hand compose corpse); delete both MinIO provisioners and
   write the SeaweedFS k8s twin (StatefulSet + services, postgres-provisioner pattern); loki
   config retargets off `minio:9000`. Rename score resource type `placeframe-keycloak` →
   `oidc-issuer`. Sync the SaaS engineer (env contract + storage swap).
3. **Slice B — observability.** Compose twins hand-written as provisioner services
   (loki/alloy/grafana — the `compose/seaweedfs.yaml` pattern: fixed DNS names,
   `${VAR:?err}` holes, healthchecks; configs as provisioner-emitted binds of the
   committed `workloads/*/config.*` paths, inlined `$`-doubled by the converter so loki's
   `-config.expand-env=true` still sees `${S3_ACCESS_KEY}` after compose interpolation;
   initialize-loki chown sidecar). The k8s half is the **first consumer of the
   docker-devkit chart-render step**: loki/alloy/grafana via the official Grafana charts,
   digest-pinned and mirrored; chart values reference existing Secrets, never carry them.
   Ride this regeneration with the alpine pin: a patch template sets the
   wait-for-resources gate image to a mirror digest, with `alpine` declared in
   `workloads/images.yml` so the mirror job picks it up.
4. **Audit hardening — drift-class closures (from the 2026-10 dedup audit; everything
   structurally correct the audit surfaced lives here or in 5–7).** Three parts,
   order-flexible except as the next-session list sequences them:
   a. **Mechanical fixes + preflight guards.** `AUTH_AUDIENCE` added to the k3d mint
      recipe in stack/AGENTS.md (the recipe as written fails pod start —
      `CreateContainerConfigError`); `compose/oidc-issuer.yaml` keycloak image →
      `${KEYCLOAK_IMAGE:?err}` (restores "compose side carries zero digests"; key
      already declared/locked); delete the dead `BUCKET` constant in
      `workloads/api/src/routers/reconstructions.py` (unused, a trap); lease-server's
      `DEPLOYMENT_ENVIRONMENT` sourced from the config resource as api.yaml already
      does (currently ignored on both renderings); drop the
      `| default "hcloud-volumes"` fallbacks in `k8s/postgres.yaml` +
      `k8s/seaweedfs.yaml` (generate-score always exports `SCORE_STORAGE_CLASS`; a
      silent default only masks a misconfigured direct score-k8s run). Preflight
      gains two standing guards in `scripts/preflight.py`: image-digest equality
      (every literal `mirror/…@sha256:` ref under `stack/score/k8s/**`, including
      values `sha`/`digest` fields, equals its `images.lock` entry, matched by
      upstream tag) and the secrets-contract check (every `secretKeyRef` key in the
      k8s sources appears in the documented mint list). The guards stay after (b) —
      they also catch chart-value drift the lock cannot see.
   b. **docker-devkit lock-resolution.** `generate-score --target k8s` resolves
      authored image references against `workloads/images.lock` at generation (exact
      marker shape — e.g. `lock://KEYCLOAK_IMAGE` — designed in-session; must also
      flow through the chart-values pre-pass for `image.sha`/`digest` fields), making
      the lock the single digest source for both renderings and deleting the five
      hand-written digest copies as a class (keycloak, alloy, fluent-bit, loki values,
      grafana values). Ships folded into the pending 0.4.7 (authoring format +
      inclusion + lock-resolution: one push, one release, one re-pin).
   c. **Source migrations riding the re-pin commit.** The five hand-written k8s
      digests → lock refs; `values/loki.yaml` switches to the chart's `loki.config`
      full-override sourcing `workloads/loki/config.yaml` via `include-yaml:`,
      deleting the structured translation — single-sources the last large hand-copy
      (the 720h/schema/S3 block duplicated near-verbatim today). Verified at the k8s
      regen; if the chart's full-override path cannot compose with singleBinary +
      the scaffolding toggles, fall back to the structured values and add a
      semantic-diff preflight guard over the shared block instead.
5. **Bucket contract.** Flow the captures bucket through the s3 resource
   (`CAPTURES_BUCKET` output → api env), deleting the hardcoded `dev-captures` in
   `capture_sessions.py` — bucket naming becomes a provisioner-level fact as
   `reconstructions_bucket` already is, instead of a compiled-in constant. Make the
   naming decision (Open decision below) and apply it uniformly across both
   provisioners; record the bucket set in stack/AGENTS.md as load-bearing names
   beside the DNS list.
6. **Slice C — long tail.** cloudbeaver, auth-initializer, ngrok, rathole-client.
   Riders from the audit: keycloak session/lifespan constants (`3600`/`2592000`,
   currently k8s-hardcoded and mirrored in `.env.sample` + the realm export) route
   through the config provisioner / `placeframe-secrets` — no third copy; both oidc
   provisioners use `{{ .State.realm }}` where the literal `placeframe-dev` appears,
   and the realm joins the load-bearing constants in stack/AGENTS.md.
7. **Slice D — GPU services.** reconstructor + localizer workload files; `gpus: all`,
   healthchecks, localizer network alias via patch templates; `service-port` resources for
   lease-server/localizer wiring. GPU shape settled (see Settled): per-variant generated
   core — the service stays `reconstructor`, only image + device patch differ per variant.
   Riders from the audit: build the healthcheck patch-template class for workload
   services — the plan's stated mechanism ("score-compose validates probes and ignores
   them → patch templates emit healthchecks") is currently unimplemented and the
   generated compose gates nothing on workload health today (score-compose silently
   drops the api/lease-server livenessProbes); `SERVICE_VERSION` envs carrying the
   tree-sha tags (OTel `service.version` vanishes in the generated stack today);
   `LOCALIZER_CONTAINER_URL` baked `localhost:8000` → `localizer:8000` once the
   alias exists.
8. **Seam generation + multi-artifact publish (B3+B4).** `generate-score` emits one compose
   per seam (subsetted workload lists per artifact); `publish-compose` publishes the five
   artifacts. Edge-anonymous is the gateway workload with its `files:` overridden out (a
   per-seam override file) plus no keycloak provisioner — that override *is* the "auth
   snippet presence" difference between the edges. `publish-compose` loses its config
   inlining (artifacts are born hermetic); env-stubbing, digest-pinning, and the publish
   call survive.
9. **Cutover.** `lifecycle.files` → generated files; delete the hand compose files;
   Make-it-Sing re-pins to `core-cuda` + `edge-keycloak` + `tunnel-rathole`;
   `.env.sample` drops `COMPOSE_PROFILES`; `uv run up` UX unchanged; re-think preflight's
   `compose.postgres.yml` role. `compose.dev.yml` survives as the hand overlay on generated
   files, never published. The audit's hand-corpse notes die here with the corpse
   (`SERVICE_VERSION` and healthchecks are carried by Slice D instead; preflight's
   duplicated database contracts shrink to the generated stack's copies).

## Mechanics that shape execution

- Runtime `.env` holes survive only as provisioner outputs inserted verbatim — the
  `placeframe-config` provisioner is the passthrough valve.
- score-compose validates probes and ignores them → patch templates emit healthchecks.
- Generated workload services are named `<workload>-<container>` (`api-api`); patches must
  compute names, never hardcode; the gateway Caddyfile proxies by generated service name.
- Cross-workload `depends_on` is not a score concept — the auto-built `wait-for-resources`
  gate replaces it; poll-retry absorbs ordering.
- Seam tests: platform-variance → score file; docker-only detail → patch template;
  generation-time baking vs runtime `.env` hole → config provisioner.
- score-compose's files→binds materialization is bridged only by the docker-devkit
  converter (work item 1a); score-k8s needs no bridge (native ConfigMaps).

## Open decisions

- Regeneration cadence once generated compose is load-bearing (work item 9): manual
  two-commit dance until cutover — the CI staleness gate stays off because every context
  SHA re-stales artifacts. Leaning for cutover: a CI bot that regenerates and
  auto-commits (canonical-message commits, the codegen-commit pattern).
- **Bucket naming** (decide before work item 5): `dev-` prefix everywhere or nowhere.
  Today's state is the only wrong answer: k8s applies it to 1 of 3 buckets
  (`dev-captures` but `reconstructions`), compose to 2 of 3, and the api hardcodes
  `dev-captures` for both tiers. If dev- everywhere: change k8s seaweedfs
  state/outputs (`reconstructions` → `dev-reconstructions`) + regen k8s. If nowhere:
  change the compose provisioner + `.env` defaults + regen compose. Either answer
  completes the slice — the `CAPTURES_BUCKET` env flow makes whichever string chosen a
  provisioner-level fact afterward.
- **docker-devkit publishing** (post-initiative, decision-gated — the plan completes
  regardless; this decides follow-on work). The 2026-10 prior-art survey: parts are
  precedented (Score itself; Flux Mirror, Aug 2026, for org-mirroring; Compose Bridge
  for one-shot compose→k8s), but the integrated whole — committed, deterministic,
  hermetic dual compose+k8s rendering with lock-coupled mirror governance and
  fail-closed lifecycle — was found nowhere. If yes: de-org-ify first (config knobs
  for the placeframe-shaped paths and defaults; soft deps on
  bashrun/strictyaml/build-artifact-registry), frame it as "the determinism +
  governance layer for Score" (the spec community's active drift discussion is the
  entry point for proposing the determinism suite upstream), and put
  cosign/referrers mirror verification on the roadmap before Flux Mirror grows a
  consumer-side lifecycle. Known risks: Docker's first-party convergence
  (Compose Bridge/Kanvas, `--lock-image-digests`) eroding the value prop from below;
  the permanent treadmill of tracking score-compose/score-k8s output changes; niche
  ceiling (dual-runtime-from-one-source is a philosophy, not a majority practice).
