# packages/python/placeframe-unity/SPEC.md

## What this is

`placeframe-unity` is the Unity build toolkit: project discovery, local builds, CI builds, license activation, the `install` command (download or build-then-install onto a device), and the ORAS cache/setup helpers those need. It is a standalone workspace package precisely so that other repositories can consume it via a git URL + subdirectory reference and get the same Unity CI and install flow placeframe has — paired with the reusable `.github/workflows/unity-build.yml` workflow, which invokes only this package's entry points. Within placeframe, `build-scripts` depends on it for CI helpers (`ci_step`, `cache`, `setup`); `scripts` no longer depends on it now that `install` has moved here. The inverse never holds.

## Shape

One flat module per concern under `src/placeframe_unity/`:

| `uv run` command | Module | Notes |
|---|---|---|
| `compile-unity` | `compile_unity.py` | Local Unity build (APK or platform binary, suitable for `adb install`). Required flags: `--project <name>` and `--build <target>`, matching a discovered `unity-build.json` manifest. Streams the editor log, prints output paths under `<project>/Build/`. |
| `install` | `install.py` | Install a Unity build onto an `adb`-connected device or launch a linux executable. Default: download the latest GitHub Actions artifact for `(project, target)` on the current branch (overridable with `--branch` / `--run`), cache it under `~/.placeframe/builds/{run_id}/`, `adb install` the APK (or `bash_handoff` the linux64 executable). With `--build` / `-B`, skips the artifact fetch and calls `compile-unity` locally instead, funneling the produced APK / executable through the same install path. Honours the manifest's `package` (for pre-install uninstall) and `grant_permissions` (post-install `adb shell pm grant`). |
| `lock-unity` | `lock_unity.py` | Lock Unity package versions for reproducible builds. |
| `test-unity` | `test_unity.py` | Run Unity editmode / playmode tests. |
| `activate-unity-license` | `license.py` | Activate the Unity Editor license (locally or with `--oras-push` for the CI cache). |
| `unity-license-tag` | `license_restore.py` | Print the license cache tag (CI pins it via `LICENSE_CACHE_TAG`). |
| `unity-matrix` | `matrix.py` | Emit the CI build matrix (CI-only). |
| `build-unity` | `build_unity.py` | CI build with library cache restore/save and version stamping (CI-only; assumes `GITHUB_WORKSPACE`, OCI registry, runner environment). |

Supporting modules: `projects.py` (manifest schema + discovery), `unity.py` (editor lookup, platform configs, batchmode command), `git_tags.py` (generic git-tag helpers), `cache.py` (ORAS restore/save), `ci_step.py` (GitHub Actions `::group::` step wrapper), `setup.py` / `setup_oras.py` (CI runner provisioning), `third-party/dotnet-install.sh` (vendored — see its sibling README for provenance).

## Constraints

**This package must never depend on `build-scripts` or `common`.** It is consumed cross-repo via git URL, and uv's `tool.uv.sources` are not transitive: a consumer resolves this package's dependencies by name, from PyPI, unless the consumer declares its own source for them. Every dependency must therefore be PyPI-resolvable — except `placeframe-bash`, which consumers declare a git source for alongside this package (both live in the placeframe repo; distinctive names keep PyPI squatting out of the resolution path). `common` is doubly excluded: an unrelated `common` exists on PyPI, and it drags boto3/litestar/opentelemetry that build tooling doesn't need.

**Unity project discovery is manifest-driven, not catalog-driven.** The Unity commands discover projects by scanning the working-directory tree for `unity-build.json` manifest files (pruning `Library`, `Temp`, `obj`, `Build`, `node_modules`, `.git`, and dot-directories). A manifest marks its directory as an opted-in Unity project; the project name is the directory name; the manifest carries only intent the project cannot otherwise express (`builds`, `execute_methods`, `package`, `grant_permissions`, `tag_prefix` — schema in `projects.py`). There is no central catalog: a project's build identity lives inside the project, so it travels with the project if it moves between repositories, and the commands run unchanged in any repo containing manifests. Discovery anchors at the current working directory — run commands from the repo root.

**`unity-matrix` prints `$GITHUB_OUTPUT`-format lines, not bare JSON.** Its stdout is two `key=value` lines — `matrix=<JSON with an include array>` and `license-image=<unityci/editor tag>` — so the workflow step is exactly `uv run --no-sync unity-matrix >> "$GITHUB_OUTPUT"` with no shell logic. Each matrix entry carries an `editor-image` tag composed from the project's `ProjectSettings/ProjectVersion.txt` editor version, the platform's unityci module, and the `UNITYCI_IMAGE_REVISION` constant in `unity.py`; `license-image` uses the highest discovered editor version with the `linux-il2cpp` module. Nothing else pins an editor version: upgrading a project's editor in `ProjectVersion.txt` automatically switches its CI container, and `unity-build.yml` stays free of repo-specific values.

**Entry-point names are the workflow contract.** `.github/workflows/unity-build.yml` (and `cesium.yml`) invoke `unity-matrix`, `unity-license-tag`, `activate-unity-license`, and `build-unity` by name via `uv run`. Consumers pin the workflow by ref and this package by git revision independently; the two pins stay compatible as long as the entry-point names and flags hold, so treat those as a public API.

**Version stamping is opt-in via `tag_prefix`.** `build-unity` writes `.build-version.json` (consumed by the project's build `executeMethod`) only when the project's manifest declares `tag_prefix`; the version is the latest `<tag_prefix>-v*` git tag plus a run-number suffix. Projects without the field build unversioned. The placeframe release jobs keep their own name→prefix map (`build_scripts/placeframe/ci/git_tags.py`) — the two must agree for projects that release.

**`dotnet-install.sh` is vendored, not downloaded.** Downloading it via curl inside CI containers is unreliable (timeouts) — the same reason `actions/setup-dotnet` bundles it. It ships as package data inside `src/placeframe_unity/third-party/` and is resolved `__file__`-relative, which works in editable installs, wheels, and git checkouts alike.

## See also

- `build/SPEC.md` — the `build-scripts` package that remains: docker-stack lifecycle, codegen, release machinery, cesium. It imports this package's `ci_step`/`cache`/setup helpers.
- `.github/workflows/CLAUDE.md` — how `unity-build.yml` is wired and why it must stay self-contained.
