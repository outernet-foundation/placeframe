# placeframe repo reorg plan

Deployment becomes the repo's third codegen pipeline: an authored tier (Score sources), a
compiled tier (rendered compose + k8s artifacts), and a CI drift gate enforcing that the
compiler is a pure function of its inputs — the same authored→derived discipline already
applied to datamodels (`database/*.sql` → `packages/generated/python/datamodels/`) and API
clients (service sources → `openapi.json` + `packages/generated/` clients). Two consequences
follow: reviewers review sources, not artifacts (artifacts ride in standalone commits with
the canonical message `Run generate-score`, skippable at review), and the compose stack and
the k8s manifests can no longer drift from each other — both are functions of one input.
The motivating pain: the hand compose stack and the Pulumi-authored reconstructor drifted
(hardcoded image SHA, mismatched bucket name) precisely because two descriptions existed.

The reorg is implemented on `repo-reorg`: `workloads/` + `stack/` trees in place, the gate
pathspec is `stack/`, and the drift gate stayed green through every move commit. The
`.score-k8s` state (the compiler's committed uid ledger) lives in the generated tier at
`stack/generated/k8s/.score-k8s/`, beside the manifests it reproduces — the score_generate
cwd change that puts it there rides the devkit release below.

## End state

```
placeframe/
  workloads/                   was docker/ — one dir per workload (Dockerfile + src + tests):
                                 long-running services (api, localizer, gateway, …), one-shot
                                 init tasks (auth-initializer, database-migrator, …), config
                                 homes for stock-image workloads (loki, alloy, grafana);
                                 neural-networks-base is the one admitted non-workload (build layer)
    images.yml                 was root compose.bake.yml — authored manifest of every image
                                 (first-party build targets + third-party x-base-images refs)
    images.lock                was root .env.lock — generated digest lock: the manifest, resolved
  stack/
    score/                     authored: workloads, provisioners, patch templates
    generated/
      compose/                 compiled compose artifacts (canonical Run generate-score commits)
      k8s/                     compiled manifests + .score-k8s state
    overlays/                  authored runtime layers (dev bind mounts, tunnels) — never
                               own image: or env contracts; those come from the generated base
```

Root contains zero compose files. `uv run up` consumes `stack/generated/compose/` +
`stack/overlays/`; Argo CD consumes `stack/generated/k8s/`. `.env.shas` is deleted outright
(see naming decisions).

The repo root is the single anchor for all relative paths: compose via `--project-directory`
(passed by the devkit), buildx via root-cwd invocation. Cross-tree dependencies flow through
the root build context (`packages/`) or through image references — never through `../` at
the compose/k8s level.

## Naming decisions

- **`stack/`** for the deployment tree. "deployments" names a k8s object type while the tree
  also owns the compose target; the repo's own vocabulary ("server stack", docker-devkit's
  "stack lifecycle") already has the right word. `deploy/` collides with today's `score/deploy`
  Argo path and reads as a verb.
- **`generated/k8s/`** — house vocabulary is k8s (`k8s_provisioners`, `.score-k8s`).
- **`workloads/`** (was `docker/`). The tree holds long-running services, one-shot init
  tasks, config homes for stock-image workloads, and one build layer — `services/` fails on
  the tasks, `images/` fails on the source and tests beside every Dockerfile. "Workload" is
  the umbrella for services-plus-jobs in both k8s (Deployment/Job) and the repo's own Score
  vocabulary (`workloads = [...]` in the generate-score table). `docker/` names the build
  tech — the same format-naming every other rename here rejects — and misdescribes the
  tech-neutral source it mostly contains. The declaration↔implementation echo with
  `stack/score/api.yaml` ↔ `workloads/api/` is a feature, not a collision.
- **`images.yml`** (was `compose.bake.yml`). The file is the repo's complete image manifest:
  first-party build targets plus every third-party ref (`x-base-images`, complete since
  f2c94d16) — and `images.lock` is its resolved form. That is the manifest→lock pair of
  `Cargo.toml`→`Cargo.lock` and `pyproject.toml`→`uv.lock`; nothing about "bake" survives in
  a subject-named pair (`bake.lock` would lie — the lock covers loki/alloy/grafana, pulled
  at runtime and never baked). `bake` remains only as the format name inside devkit code
  (`BakeDocument`, `parse_bake`). Keep `.yml` — buildx parses by extension.
- **`images.lock`** (was `.env.lock`). Role-named, not format-named: the `.env.` prefix is
  the same anti-pattern as the `compose.` prefix, and a lock is a reviewed, visible artifact
  everywhere else (nobody ships `.uv.lock`). Content and mechanism are unchanged — env
  format, consumed via `--env-file`.
- **`.env.shas` is deleted, not renamed.** Verified to have zero code readers anywhere
  (placeframe, capture-tool, Make-it-Sing, docker-devkit — live trees and all histories);
  every consumer recomputes via `compute_service_shas` and injects into the environment.
  It was a write-only memo of a pure function of the tree: describes the last build, not the
  current tree — the two-descriptions drift pathology at micro scale.

## Release window (what is left of Phase 1)

Everything below is blocked on one docker-devkit release, then lands leaves-first:

1. **Push and release docker-devkit** — branch `images-manifest-naming` carries: the
   manifest/lock resolution pair (`resolve_manifest` / `require_manifest` / `resolve_lock`:
   `workloads/images.yml` + `workloads/images.lock`, with the legacy root names still
   resolving so no repo breaks mid-window), the `declared_references` / `stray_references`
   glob updates, the `context_sha` workload-root derivation (no more `docker/` literal),
   `--project-directory` anchoring in `up`/`down`, the `.env.shas` write deletion, and the
   root-relative Score outputs (compose output + k8s output/state; the k8s half runs from
   the generated home so state lands there). Push to main; `release.yml` publishes the
   patch.
2. **Repin all three repos** after the release (`uv lock --upgrade-package docker-devkit`):
   placeframe `repo-reorg` and Make-it-Sing `ci-support` already carry their moves; their
   build/mirror CI jobs stay red until the repin lands — the deliberate single-window
   trade. placeframe's type-check rides the same pin (`require_manifest`).
3. **placeframe-capture-tool renames** — see below.

## Placeframe-capture-tool

Consumes the same conventions through docker-devkit (pins `>=0.1.15` from PyPI), so the
renames propagate in the same release window:

- Rename `compose.bake.yml` → `workloads/images.yml` and `docker/` → `workloads/`
  (`aoa-bridge`, `aoa-gateway`, `zed-capture`), move the committed lock to
  `workloads/images.lock`, delete the vestigial `.env.shas` gitignore entries, repin the
  devkit release.
- `install-zed` constants `BAKE_FILE` / `ENV_LOCK_FILE`
  (`scripts/src/scripts/install_zed/constants.py`) follow the new names — it recomputes
  service shas and parses the lock directly rather than reading any shas file.
  `compose.rig.yml` (box compose) is unchanged beyond env keys.
- Make-it-Sing's renames already landed on its `ci-support` branch (the stray mirror→
  docker.io lock edit in its working tree was resolved back to the committed mirror entry —
  identical digest, declaration system intact).
- Preflight batteries stay per-repo, composing around the fixed python-devkit battery
  (explicit prior ruling; never inside a devkit).

## Phases

- **Phase 1 — the mechanical reorg**: the moves, consumer updates, gate pathspec, and
  docs are landed on `repo-reorg` (placeframe) and `ci-support` (Make-it-Sing); the drift
  gate stayed green throughout (a `Run generate-score` commit followed every tree change
  that rotated SHAs — including the docs commit: `workloads/*/AGENTS.md` ride the
  allowlisted build context). Remaining: the release-window items above. Argo CD is out of
  scope by operator ruling.
- **Phase 2 — full compose generation** (decision-gated): port the remaining ~17 services
  per the score-poc fork; hand compose files die; GPU arch / CNPG become generation-time
  flags rendering per-arch artifacts under `stack/generated/compose/`; dev bind mounts and
  tunnels remain authored overlays under `stack/overlays/`. This is where every
  `workloads/` dir gains its Score workload declaration and the root compose files
  relocate under `stack/`.

## Open decisions

- **Option A vs B** (`design/score-poc.md`): deps as plain workloads ("Compose in Score")
  vs custom provisioners preserving managed-in-prod binding. Hinges on how pervasively
  production uses managed dependencies. Gates Phase 2; also embeds the SeaweedFS-vs-MinIO
  convergence and the localizer env-stub treatment.
- **Port baking**: score-compose bakes `--publish` literals at generation; the hand stack
  resolves ports from `.env` at up-time. Either accept ports as compiled facts
  (regeneration-triggering) or patch-template them back to `${VAR:?err}`. Affects what
  Phase 2's generated compose contains — decide before the variant layout freezes.
- **Variant layout**: `stack/generated/compose/` will hold base + per-arch renderings;
  file-per-variant vs subfolder-per-target settles during Phase 1 layout.

## Sequencing constraints

- docker-devkit changes release leaves-first (PyPI patch-auto), all three repos repin
  after — the tool-consumption pattern everywhere in this repo family.
- Codegen hygiene throughout: every regeneration is a standalone `Run generate-score`
  commit, no body, separate from source/move commits.
- Rebase-merge only, never squash.
