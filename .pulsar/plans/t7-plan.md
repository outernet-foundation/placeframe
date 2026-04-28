# T7 Plan: Unity CI Workflow

## Context

Placeframe has 3 active Unity projects that need automated CI builds. Foundation work is complete (T62: local builds, T69: Cesium native plugin, T73: batchmode fix, T4: branch-based CI pattern). This ticket wires everything into a GitHub Actions workflow with the full 7-build matrix.

## Approach

### 1. Rewrite `build_unity.py` — platform enum + executeMethod dispatch

**File:** `scripts/src/scripts/build_unity.py`

Replace the current `BUILD_TARGETS = ["android", "linux64"]` with the full platform enum and build matrix:

```python
PLATFORMS = ["android-mobile", "magicleap", "linux64", "win64"]

BUILD_MATRIX: dict[str, list[str]] = {
    "Outernet.Client": ["android-mobile", "magicleap", "linux64", "win64"],
    "MapRegistrationTool": ["linux64", "win64"],
    "AndroidMobile": ["android-mobile"],
}
```

Remove `MakeItSing` from `UNITY_PROJECTS` (not in build matrix).

**Execute method dispatch table** — maps (project, platform) to fully qualified C# method:
```python
EXECUTE_METHODS: dict[str, dict[str, str]] = {
    "Outernet.Client": {
        "android-mobile": "Outernet.Client.Build.BuildForAndroidMobile",
        "magicleap": "Outernet.Client.Build.BuildForMagicLeap",
    },
    "AndroidMobile": {
        "android-mobile": "Placeframe.Client.Build.BuildForAndroidMobile",
    },
}
```

**Build command construction** by platform:
- `android-mobile` / `magicleap`: `-buildTarget Android -executeMethod <method>` (looked up from dispatch table)
- `linux64`: `-buildLinux64Player <output_path>`
- `win64`: `-buildWindows64Player <output_path>`

**Dual-environment editor discovery** — `UNITY_EDITOR` env var override for GameCI containers (where Unity is at a different path), falling back to `/opt/unity/<version>/Editor/Unity` for COI.

**CLI update** — rename `--target` to `--platform`. When both `--project` and `--platform` are specified, validate against `BUILD_MATRIX`. When iterating all builds, only iterate valid (project, platform) pairs.

### 2. Create `BuildScript.cs` for AndroidMobile

**File:** `apps/AndroidMobile/Assets/Editor/BuildScript.cs` (new)

Follows the pattern from `legacy/Outernet.Client/Assets/OuternetClient/Editor/BuildScript.cs`:
- Namespace: `Placeframe.Client` (matches app convention)
- Class: `Build` (static)
- Method: `BuildForAndroidMobile()` — configures ARCore, OpenGLES3, ARM64, ASTC, then builds
- Scene: `Assets/Scenes/Main.unity`
- Output: `Build/AndroidMobile/AndroidMobile.apk`
- Includes build report JSON serialization (same pattern as legacy)

Simpler than the legacy version — no Magic Leap, no platform switching, no render pipeline swaps. Do NOT create a `.meta` file (Unity generates those).

### 3. Create `.github/workflows/unity.yml`

**File:** `.github/workflows/unity.yml` (new)

**Triggers:** same T4 pattern — push to `main`/`dev`, PRs targeting both, `paths-ignore: [".env.lock"]`.

**Matrix:** 7 explicit includes (not a cross-product):
| project | platform | module |
|---|---|---|
| legacy/Outernet.Client | android-mobile | android |
| legacy/Outernet.Client | magicleap | android |
| legacy/Outernet.Client | linux64 | linux-il2cpp |
| legacy/Outernet.Client | win64 | windows-mono |
| apps/MapRegistrationTool | linux64 | linux-il2cpp |
| apps/MapRegistrationTool | win64 | windows-mono |
| apps/AndroidMobile | android-mobile | android |

**Container:** `unityci/editor:ubuntu-6000.0.66f1-${{ matrix.module }}-3.1.0`

All builds run on `ubuntu-latest` with GameCI containers (win64 cross-compiles via `windows-mono` module; T75 tracks switching to Windows runners later).

**Steps per job:**
1. **Checkout** — `actions/checkout@v4`
2. **Activate Unity license** — direct CLI activation inside container (`unity-editor -batchmode -serial ...`), NOT the `game-ci/unity-activate` action (which uses Docker internally and doesn't work inside container jobs)
3. **Cache Unity Library** — `actions/cache@v4`, keyed per project + `Packages/manifest.json` hash
4. **Setup UV** — `astral-sh/setup-uv@v5`
5. **Build** — `uv run build-unity --project <name> --platform <platform>`
6. **Upload artifacts** — `actions/upload-artifact@v4`
7. **Return license** — `unity-editor -returnlicense` with `if: always()` (serial licenses have finite activations)

**No `.env.lock` commit** — this workflow doesn't produce Docker images.

### 4. Tests for `build_unity.py`

**File:** `scripts/tests/test_build_unity.py` (new)

Mock `run_command` to verify command construction. Test cases:
- `linux64` → command includes `-buildLinux64Player`
- `win64` → command includes `-buildWindows64Player`
- `android-mobile` → command includes `-executeMethod ...BuildForAndroidMobile` + `-buildTarget Android`
- `magicleap` → command includes `-executeMethod ...BuildForMagicLeap` + `-buildTarget Android`
- Invalid (project, platform) combo → error
- `UNITY_EDITOR` env var overrides default editor path
- Default editor path is `/opt/unity/<version>/Editor/Unity`

## Key files

| File | Action | Notes |
|---|---|---|
| `scripts/src/scripts/build_unity.py` | Rewrite | Platform enum, executeMethod dispatch, dual-env editor discovery |
| `apps/AndroidMobile/Assets/Editor/BuildScript.cs` | Create | Android mobile build script following legacy pattern |
| `.github/workflows/unity.yml` | Create | 7-build matrix, GameCI containers, license activation |
| `scripts/tests/test_build_unity.py` | Create | Command construction tests |

**Reference files (read-only):**
- `legacy/Outernet.Client/Assets/OuternetClient/Editor/BuildScript.cs` — pattern for C# BuildScript
- `.github/workflows/build.yml` — pattern for workflow triggers/concurrency
- `packages/python/common/src/common/run_command.py` — `run_command` API (stream_log param)
- `scripts/tests/test_tidy_commits_wrapper.py` — testing pattern (mock run_command)

## Risks

1. **GameCI image availability** — `unityci/editor:ubuntu-6000.0.66f1-*-3.1.0` may not exist. If not, the tag suffix or Unity version may need adjustment. This is a deployment-time concern; the workflow is correct regardless.
2. **License activation inside container** — direct CLI activation (`unity-editor -serial ...`) should work since GameCI containers have the editor pre-installed, but needs manual verification in CI.
3. **Disk space** — GameCI images are 5-10 GB. Each job runs independently so disk pressure is per-job, should fit within runner limits.

## Verification

**Verifiable now:**
- `uv run ruff check .` — passes
- `uv run ruff format --check .` — passes
- `uv run basedpyright` — passes on modified files
- `uv run pytest scripts/tests/test_build_unity.py` — all tests pass
- `uv run build-unity --help` — shows updated CLI
- Workflow YAML is syntactically valid

**Requires GitHub Actions (manual):**
- Full build matrix passes
- License activation works
- Library cache reduces build times
