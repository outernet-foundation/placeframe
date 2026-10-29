# Workflow Conventions

## Four workflow files split by triggering event

Verification certifies on PRs; delivery runs on the landing push. `integrate.yml` (triggers `pull_request: [dev]` + `workflow_dispatch`; concurrency `group: integrate-${{ github.ref }}` with `cancel-in-progress: true` — a superseded PR run cancels whole) runs the verify DAG. `release.yml` (triggers `push: [main, dev]`; concurrency `group: release-${{ github.ref }}` with NO cancel — the queue is the policy: the `main` group is the release mutex, and serialization makes the CalVer count-and-cut and the `dev-*` sweep safe) delivers via two composite `uses:` jobs gated by branch — `channel: dev` on the dev job, `channel: stable` on the main job. `merge-gate.yml` is the third file — the bors-model lander, woken only by the `ready-to-merge` label (`pull_request: [dev], types: [labeled]`; per-PR concurrency group `merge-gate-${{ github.event.pull_request.number }}` with no cancel), one `uses:` call to the toolkit's merge-gate reusable forwarding `merge-bot-private-key`. `cleanup-pr-releases.yml` is the fourth — an unmerged PR's close wakes one `uses:` call that sweeps the PR's `pr-{N}-*` releases (the merged path is merge-gate's sweep). github-actions-toolkit's `AGENTS.md` owns the full consumer contract; nothing here duplicates it.

Every `uses:` ref to `outernet-foundation/github-actions-toolkit` is a full 40-hex SHA, all of them the same SHA, enforced by `lint-workflows` (which the preflight reusable runs internally). Third-party actions would be pinned by SHA too — zizmor's blanket hash-pin policy — but the Integrate DAG carries no local jobs anymore (every job is a `uses:` call).

## The verify DAG

```
mirror-images ─→ preflight ─┬→ compile-check-unity ─────┐
                             └→ build-docker ───────────┴→ release-pr-builds
```

`mirror-images` is the single first root — provisioning precedes consumption: the repo-specific preflight builds the postgres wrapper image, whose `FROM` is a mirror-prefixed base from `workloads/images.lock`, so the mirror namespace must be populated before `preflight` pulls from it. Every job is a `uses:` call into the toolkit; `needs` wires across the local/called boundary freely.

- `preflight` (calling-job permissions `contents: read, packages: read` — the DB battery pulls the mirrored postgres) runs lint-workflows, validate-release-plan, and the repo battery from `scripts/preflight.py` (the python battery via `preflight-python`, then the repo checks in-process, then `generate-clients --check`).
- `compile-check-unity` forwards the `UNITY_*` secrets; its legs run on the self-hosted `unity` pool.
- `build-docker` fans out via docker-devkit's matrix (the cross-compile cohort splits into its own legs; each leg shelves its own digest-manifest shard) and embeds the compose publishing: the toolkit reusable derives the publish legs from `uv run --locked publish-compose --plan` (the devkit verb, seam mode — artifact names are the seam names) and its embedded `publish-compose` job runs the verb for all five seam artifacts (`core-{cuda,rocm}`, `gateway-{open,keycloak}`, `tunnel-ngrok`), each as `<sha>` and `<branch>` tags under `ghcr.io/outernet-foundation/placeframe/`.
- `release-pr-builds` needs the terminal build legs (`build-docker`, `compile-check-unity`).

## Delivery notes

Both delivery jobs carry `contents: write, id-token: write, packages: read` (trusted publishing; the digest-manifest shelf pull for the built-image set, derived from root `repository` presence in `docker-devkit.yaml`). `NUGET_USER` is mapped once in workflow-level `env` — the composite's NuGet login gates on its presence; the secrets context never crosses into composite-land. `NUGET_USER` is a per-repo secret (never org-level — org secrets are fleet-visible and would switch the login on everywhere). `release.yml` must never be renamed: the npm and nuget trusted publishers are bound to the filename. PyPI/npm/nuget publishers are all environment-less, matching the jobs.

The dev channel publishes immutable prereleases of every path-diff-changed package and cuts the `dev-{count}` published prerelease; stable publishes the 2.0 lines (per `publish.yml`), tags `{name}-v{semver}` per package, cuts the CalVer release, and sweeps the `dev-*` releases. `placeframe-api-client` is two config entries on one path — `placeframe-api-client` (nuget) and `placeframe-api-client-npm` (npm `org.outernet.placeframe.apiclient`) — the one-package-one-ecosystem law; both lines move together because they share the path.
