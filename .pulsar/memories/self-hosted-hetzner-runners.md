---
updated: 2026-06-06
---

# Switch CI to self-hosted Hetzner runners

## Goal

Make-it-Sing's Unity build CI cannot run on GitHub-hosted runners: the repo is private, so `ubuntu-latest` jobs get the standard runner with ~14 GB free disk, and the `unityci/editor:6000.0.66f1-android-*` image (~8 GB compressed, ~14 GB extracted) fails during "Initialize containers" with `no space left on device` — before any workflow step runs, so no in-container or first-step cleanup can help. The decision (user, verbatim intent): **we need to switch to self-hosted Hetzner runners. There is an in-progress repo for infra that we will use for this, but the user needs to switch to a different workstation to make the changes.**

## State

- Diagnosed Make-it-Sing run 27067516496 (`feature/unity-ci`): `unity / matrix` and `unity / activate-license` pass; both build jobs (`MakeItSing-Unity (android-mobile)` and `(magicleap)`) die at "Initialize containers" — Docker pull of the android editor image exhausts disk.
- Measured (not assumed) runner disk: placeframe's successful `CaptureTool (android-mobile)` job on `feature/ci-refactor` (run 27050647934) shows `df -h` → `overlay 145G ... 96G avail` — public-repo runners get 4-core/150 GB machines. Private-repo `ubuntu-latest` gets ~14 GB free. Same workflow, same image; the runner class is the only difference.
- Historical context: MakeItSing used to build inside placeframe's CI matrix (removed in `f3d286c7`) on those 145 GB runners, where it built fine. Placeframe's historical disk failures were *build-phase* (post-pull) and were solved by the `/to_clean` volume-mount + `free_disk_space()` trick (introduced in `b38204f3`, March 2026). That machinery structurally cannot fix a *pull-phase* failure: `container:` jobs pull the image before step 1 runs.
- `free_disk_space()` (`packages/python/placeframe-unity/src/placeframe_unity/setup.py`) has a host-mode branch (proven in `build-docker` jobs) that frees ~25-30 GB, but every Unity call site runs it in container mode. It is not exposed as a CLI entry point. Alternative fixes considered before the Hetzner decision: drop `container:` and clean the host before a `docker run` (structural), pay for larger GitHub runners, or make Make-it-Sing public.
- Earlier in the session, a separate bug was fixed: ORAS cache references built from `ghcr.io/${{ github.repository }}/cache` break for repos with uppercase names (`Make-it-Sing`) because OCI repository names must be lowercase. Fixed in `placeframe_unity/cache.py` — `restore()` and `save()` now lowercase the registry argument. Committed as `92067808` on placeframe `feature/ci-refactor`. Verified working: `activate-license` went green on the next Make-it-Sing run.
- Make-it-Sing's git pins (`pyproject.toml` + `uv.lock`) bumped to `92067808862df986b902c2d1217b0dabe113f769`, committed as `529dabf` on its `feature/unity-ci` branch.
- Both commits are local to the sandbox. The sandbox `GITHUB_TOKEN` reports `push: true`/`admin: true` via the API but actual `git push` gets 403 ("denied to tylershatch") — likely fine-grained token without Contents: write or org SSO; user pushes from the host.

## Decisions

- Self-hosted Hetzner runners are the chosen fix for Make-it-Sing CI disk exhaustion (user decision; supersedes the GitHub-larger-runner and make-repo-public options).
- The infra work happens in the in-progress infra repo, from a different workstation — not this one.
- The lowercase-registry fix lives in `placeframe-unity` (the package), not per-consumer workflows, so every git-referencing consumer repo inherits it.

## Key files

- `/placeframe/infra/` — the in-progress infra repo (standalone, seeded inside placeframe; origin `outernet-foundation/infra`). Currently a Pulumi program provisioning a Hetzner rathole relay VPS + per-engineer floating IPs for MakeItSing tunnels; this is the repo that will grow the self-hosted runner provisioning. See its `README.md` and `plan.md`.
- `/placeframe/.github/workflows/unity-build.yml` — reusable Unity workflow consumed by both placeframe and Make-it-Sing; `runs-on: ubuntu-latest` and `container:` directives are what need to target the self-hosted runners.
- `/placeframe/packages/python/placeframe-unity/src/placeframe_unity/setup.py` — `free_disk_space()` (container/host/Windows modes); GitHub-runner-specific cleanup that may be irrelevant or wrong on Hetzner machines.
- `/placeframe/packages/python/placeframe-unity/src/placeframe_unity/cache.py` — registry-lowercasing fix (`92067808`).
- `/placeframe/Make-it-Sing/` — checkout of the private consumer repo, branch `feature/unity-ci`, pin-bump commit `529dabf` unpushed.

## Pending threads

- Provision self-hosted Hetzner runners via the infra repo (blocked: user must switch workstations).
- Point Make-it-Sing's CI (and decide whether placeframe's Unity jobs too) at the self-hosted runners; revisit whether `container:` + `/to_clean` mounts and `free_disk_space()` still make sense there.
- Push placeframe `feature/ci-refactor` (must land before Make-it-Sing CI re-runs — `uv sync` fetches rev `92067808` from GitHub) and Make-it-Sing `feature/unity-ci` (`529dabf`). If placeframe history gets rebased/tidied, the SHA pin needs re-bumping.
- Secondary cleanup noted during diagnosis: `cache.py`'s `restore()` treats "invalid reference" errors as a cache miss instead of distinguishing them from "tag not found" — a config bug masquerades as a miss.
