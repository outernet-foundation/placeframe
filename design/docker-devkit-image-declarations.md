# One home for third-party image declarations; docker-devkit stops parsing compose

Status note for pickup: COMPLETE. Shipped: docker-devkit 0.1.15, release-devkit
0.1.11 (both on PyPI). placeframe `dev`: `f2c94d16` (declarations conversion +
generate-score port completion), `33ddfb26` (score artifacts), `e0bcd9f8`
(prose) — preflight green. capture-tool `dev`: `ef7660d` (renames + repin),
`6025c5e` (prose) — lock round-trip stable, rig render green. All four repos
need operator pushes. Resolved during execution: the fluent-bit declaration key
is `SEAWEEDFS_AUDIT_IMAGE` (the plan's `FLUENT_BIT_IMAGE` never matched the
actual compose hole — holes stayed textually unchanged); stale `DOTNET_*`
declarations and `PYTHON_BASE`/`ZED_BASE` lock entries were pruned in placeframe
(zero consumers); `INITIALIZE_S3_IMAGE` (consumed by scripts/sweep_postprocess)
was promoted to a declaration; the generate-score console-script collision was
resolved by completing the port (config table in placeframe pyproject,
duplicate module deleted); capture-tool's bake file is `compose.bake.yml`, not
the `compose.zed.bake.yml` this plan named. NEXT: make-it-sing's own plan.md
resumes — flip its committed Stage 3 checkpoint (`6b4120c`) from
`ARG UV_BASE_DIGEST` + `FROM mirror/…${UV_BASE_DIGEST}` to
`ARG UV_BASE_IMAGE` + `FROM ${UV_BASE_IMAGE}`, repin docker-devkit >=0.1.15.

## Why this initiative exists

docker-devkit parses consumer compose files for exactly one purpose: discovering
`x-image-ref` labels (declarations of externally-pulled images) so `run_build`
can digest-lock them and `mirror-images` can mirror them. That single need dragged
in a pile of wrong-shaped machinery:

- Compose's YAML dialect tags (`!reset`) require PyYAML constructor registration,
  and PyYAML's constructor API is untyped — a type-checker fight with no clean
  resolution (the only surviving form was a suppression-boundary debate).
- The include-following logic in `run_build` serves zero org repos (the only
  compose include anywhere is make-it-sing's `oci://` one, which contributes
  nothing and was skipped anyway).
- Two declaration mechanisms exist for one need: `x-image-ref` labels in compose
  (placeframe: fluent-bit, cloudbeaver, keycloak, ngrok) and `x-base-images` in
  the bake file (placeframe: loki, alloy, grafana, and every Dockerfile base).
- The `_DIGEST` suffix lock shape (`image: path${X_DIGEST:?err}` in compose,
  lock `X_DIGEST=@sha256:…`) authors the mirror path TWICE — bake declaration +
  compose image line — a drift exposure (path drift fails loud at pull; tags
  cannot drift, but the duplication is authored).
- The Dockerfile suffix form (`FROM path${X_DIGEST}`) has a silent-unpinned
  failure mode: an empty arg yields a tagless `FROM path`, and Docker silently
  pulls `:latest`.

## The design

- **Single declaration home**: bake `x-base-images`. Keys use the `_IMAGE`
  convention (`UV_BASE_IMAGE`, `KEYCLOAK_IMAGE`, …). One authored string
  (`path:tag`) per third-party image, anywhere in the org.
- **run_build single-emits** one lock entry per declaration:
  `NAME=path:tag@sha256:…`. No dual shapes, no suffix entries.
- **Compose image lines** are pure holes: `image: "${KEYCLOAK_IMAGE:?err}"`.
- **Dockerfiles** use `ARG NAME` + `FROM ${NAME}`. An empty arg is a hard parse
  error — this fixes the silent-`:latest` foot-gun.
- **BakeDocument gains a field validator**: every `base_images` value must be
  `path:tag` or `path@digest`. The declarations half of `unpinned_references`
  moves to parse time (enforced on every command run, not a CI-only scan).
- **`collect_repo_references` splits**: `declared_references(root)` (bake
  declarations only — what mirror-images consumes) and a stray-ref scan
  (Dockerfile `FROM`/`COPY --from` literals + score yaml `image:` lines — what
  `unpinned_references` polices; it survives with that narrow job of catching
  hand-written literal refs that bypass the declaration system).
- **`version_coupling_violations` is unchanged** — it guards a genuinely
  non-derivable agreement (pyproject `tool.uv.required-version` ↔ image tag; the
  tag carries suffixes like `-python3.13-trixie-slim` that pyproject doesn't
  hold). Two authored truths that must agree is a different problem from one
  truth scattered; the check is correct, keep it.

## Changes

### docker-devkit (this repo) — release 0.1.15

- `image_refs.py`: delete `compose_image_refs`, `ComposeDialectLoader`, both
  `add_constructor` registrations, and the compose branch of
  `collect_repo_references`; implement the `declared_references` / stray-scan
  split. `bake_base_image_refs` and `version_coupling_violations` stay.
- `documents.py`: add the `base_images` field validator.
- `build_docker.py`: delete the third-party `x-image-ref` resolution block;
  single-emit lock entries from `x-base-images`; wire all bake consumption
  through `parse_bake`/`BakeDocument` (typed access replaces dict plumbing —
  including `compute_service_shas(repo_root, bake: BakeDocument)` and
  `compute_default_targets(bake: BakeDocument, …)` signatures, with `up.py`,
  `down.py`, `score_generate.py` parsing at their call sites); loud guard:
  `--mode ci` requires `x-registry-cache`.
- Tests: delete the compose-dialect tests; add validator + split-function tests;
  existing fixtures via `BakeDocument.model_validate`.
- `types-pyyaml` stays as a dev dependency (it types `parse_bake`'s PyYAML
  surface; with the dialect code gone, zero suppressions are needed anywhere).
- AGENTS.md: update the `image_refs.py` row and any compose-parsing references
  (separate prose commit from the code).
- Release via the normal tag-ledger flow; operator push (App token cannot push).

### release-devkit — next patch (0.1.11)

- `mirror_images.py`: switch from
  `collect_repo_references(Path.cwd(), dockerfile_glob=None)` to
  `declared_references(root)` — same refs, declarations-only source.

### placeframe — one PR

- `compose.bake.yml`: add declarations for the 4 `x-image-ref` services
  (`CLOUDBEAVER_IMAGE`, `KEYCLOAK_IMAGE`, `FLUENT_BIT_IMAGE`, `NGROK_IMAGE`,
  values = today's label strings); rename every existing `_DIGEST` declaration
  key to the `_IMAGE` convention; `x-base-args` keys follow the renames.
- `compose.yml`: delete the 4 labels (their image lines are textually unchanged —
  they were already `${X_IMAGE:?err}` holes); flip loki×2 / alloy / grafana from
  `path${X_DIGEST:?err}` to `${X_IMAGE:?err}`; inventory every `${…_IMAGE}` hole
  (at minimum `SEAWEEDFS_AUDIT_IMAGE`) and ensure a declaration exists for each.
- Dockerfiles: convert every base `FROM` to `ARG NAME` + `FROM ${NAME}`.
- Version-coupling site registry (consumer preflight): rename `base_image` site
  names to the new declaration keys — locate the registry during execution.
- Regenerate `.env.lock` (`uv run build --lock-only`); preflight green; repin
  docker-devkit `>=0.1.15`.
- AGENTS.md mentions of `x-image-ref` updated (separate prose commit).

### capture-tool

- 3 Dockerfiles + `compose.zed.bake.yml` `x-base-args` key renames; regen
  `.env.lock`; repin docker-devkit.

### make-it-sing — NOT this initiative

Its own `plan.md` resumes AFTER this one lands (its Stage 3/5 consume the new
pattern). Its committed Stage 3 checkpoint (`6b4120c`) still carries the suffix
form (`ARG UV_BASE_DIGEST` + `FROM mirror/…${UV_BASE_DIGEST}`) — flip to
`ARG UV_BASE_IMAGE` + `FROM ${UV_BASE_IMAGE}` when resuming that plan.

## Ordering

docker-devkit 0.1.15 → release-devkit 0.1.11 → placeframe PR → capture-tool.
All releases are operator pushes; the sandbox App token has Contents:read only.

## Verification

- docker-devkit: pytest + ruff + basedpyright all green (the checkpoint's known
  failures must be gone — their absence is the proof the deletion was complete).
- placeframe / capture-tool: `uv run build --lock-only` round-trip, preflight
  battery, `docker compose config` render.

## Deliberately out of scope

- Score yaml scanning changes.
- Renaming the `x-base-images` key itself (it now covers runtime images too —
  placeframe's loki already made that de facto; note it in a bake-file comment).
- make-it-sing CI stages (owned by its own plan).
