# CI bring-up for Make-it-Sing

Status note for pickup: this plan was authored mid-initiative, and one problem
discovered during planning is being fixed OUT OF BAND in the docker-devkit repo
(see "Disentangled: docker-devkit" at the bottom). Its outcome changes details
of Stage 3 and Stage 6. A future session MUST AUDIT CURRENT STATE before
executing: check whether the docker-devkit fix has been released and what
version this repo pins, what workflow SHA placeframe's ci.yml currently pins,
whether any stage below has already landed on this branch, and whether
feature/unity-ci has already been harvested.

## Why this initiative exists

CI in this repo has never passed. Every run on `dev` back through July 2026
fails in 0 seconds with "workflow file issue": `makeitsing-ci.yml` pinned
`placeframe/.github/workflows/unity-build.yml@c331312…` and that file does not
exist at that SHA (the workflow moved to unity-devkit before the pin was
made). Beyond the dead pin, the repo has no check job, no image builds, no
release flow, and its pyproject dev group pins pre-consolidation placeframe
git subdirectories (`placeframe-bash`, `placeframe-unity`, `scripts`
@26844545), dragging the whole placeframe toolchain into the venv.

## Reference shape

`placeframe-capture-tool/.github/workflows/ci.yml` + `release.yml` is the
sibling consumer repo to imitate: check (python-devkit `preflight-python`) →
mirror (release-devkit `mirror-images` + `build/publish-config.json`) → unity
(unity-devkit reusable workflow, SHA-pinned, `secrets: inherit`) → docker
build (docker-devkit bake) → `ensure-release-pr` on dev pushes; release.yml
apps-only variant on main.

## Stages

### Stage 1 — make CI run at all

- pyproject dev group → `bashrun>=0.1.2`, `unity-devkit>=0.1.5` (PyPI);
  regen `uv.lock`.
- `makeitsing-ci.yml` → `uses:
  outernet-foundation/unity-devkit/.github/workflows/unity-build.yml@85726f37…`
  (placeframe's current pin at authoring time — re-verify on pickup).
- Harvest the two-file essence from local branch `feature/unity-ci` (it is 158
  commits behind `feature/modularization`; do NOT merge or rebase it; drop its
  TEMPORARY build-air-gapped-on-branch hack).
- Verify `UNITY_EMAIL`/`UNITY_PASSWORD`/`UNITY_SERIAL` secrets exist on the
  repo and that self-hosted `["self-hosted","unity"]` runners pick it up —
  never exercised, since every run died at workflow validation. One dispatch
  to confirm.

### Stage 2 — check + mirror jobs

- Root pyproject becomes a uv workspace: `members = ["docker/livekit-token"]`;
  basedpyright include paths for the service src. No tests exist yet; the
  battery still checks sync/lint/lock.
- `check` job: `uvx --from python-devkit preflight-python`.
- `mirror` job + `build/publish-config.json` (org mirror prefix) so
  `livekit/livekit-server` and `caddy` ride the org mirror; move them to
  `.env.lock` digest pins over time.

### Stage 3 — build the livekit-token image in CI

- Add a bake file for the service; CI runs
  `uv run build --bake-file … --targets livekit-token`.
- FILENAME: at authoring time it must NOT be `compose.bake.yml` — docker-devkit
  as released flips `up`/`down` into its hardcoded "native" assembly on that
  exact filename. Capture-tool precedent: `compose.zed.bake.yml`. Plan of
  record: `compose.services.bake.yml`. IF THE DISENTANGLED DOCKER-DEVKIT FIX
  (below) HAS LANDED AND THIS REPO PINS IT: the filename marker no longer
  exists; prefer the canonical `compose.bake.yml` plus a declared
  `[tool.docker-devkit.lifecycle]` table (`files = ["compose.yml"]`).

### Stage 4 — compose render check (minimal, droppable)

- One job: `docker compose --env-file .env.sample -f compose.yml config
  --quiet` — verified passing 2026-09-23 against the pinned
  `placeframe-cuda@sha256:22b5014…` digest. Catches this repo's own
  overlay/env drift only; deliberately insufficient for upstream-contract
  validation (known, accepted).

### Stage 5 — release tier

- `MakeItSing-Unity/unity-build.json`: add `tag_prefix` (`makeitsing`); same
  prefix in the publish-config apps entry.
- Port placeframe's `BuildUtility.cs` `.build-version.json` reader into the
  `Outernet.Build` scripts — grep-verified nothing in MakeItSing-Unity reads
  it today; without this, `tag_prefix` is decorative and releases ship
  unversioned APKs.
- `build/publish-config.json`: apps-only (`MakeItSing-Unity`), `ci_workflow:
  makeitsing-ci.yml`, mirror prefix, `compose_files: [the bake file]`.
- `ensure-release-pr` job (needs all others; dev pushes only) — requires repo
  secrets `PLACEFRAME_CI_APP_ID` / `PLACEFRAME_CI_PRIVATE_KEY`.
- `release.yml`, apps-only variant: fetch-ci-artifacts → publish-packages
  `--with-apps` → create-release. No publish-dev job (nothing is published to
  registries).
- Flow: dev → auto-created release PR → fast-forward to main; `makeitsing-v*`
  tag ledger drives versions.

### Stage 6 — `uv run up` / `down`

- Add `docker-devkit` to the dev group (its `up`/`down`/`build` entry points
  land in the venv).
- Default `up` runs `compose.yml` (the OCI-include graph) against `.env`;
  `uv run up --compose-file compose.local.yml` is the sibling-checkout loop.
- Reconcile AUTH_MODE/PUBLIC_URL validation with the demo `.env`s:
  docker-devkit rejects keycloak over cleartext `http://`, and `.env.sample`
  is exactly that combination (`AUTH_MODE=keycloak`, `PUBLIC_URL=http://…`).
  Decide what the LAN and tunnel `.env`s actually set before wiring docs.

## Disentangled: docker-devkit up/down mode fork

docker-devkit as released picks `up`/`down` behavior by sniffing for a file
named `compose.bake.yml`, and its "native" branch hardcodes placeframe's
layout (`-f compose.yml -f compose.postgres.yml -f compose.<gpu>.yml -f
compose.dev.yml`) — placeframe's shape embedded in a supposedly generic
package, with semantics changed at a distance by an unrelated filename. That
is being fixed as a separate initiative in the docker-devkit repo: compose
assembly becomes declared data (`[tool.docker-devkit.lifecycle]` in the
consumer's root pyproject), one code path, and a loud error when a bake file
exists without a declaration. OUTCOME AFFECTS Stages 3 and 6 — audit
docker-devkit's released version and this repo's pin at pickup.

## Operational unknowns

- `UNITY_*` secrets and self-hosted runner availability (Stage 1).
- `PLACEFRAME_CI_APP_ID` / `PLACEFRAME_CI_PRIVATE_KEY` (Stage 5).
- Branch protection on `dev` (release-PR flow assumes merges are CI-gated).
