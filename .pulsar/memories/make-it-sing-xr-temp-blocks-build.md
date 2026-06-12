---
updated: 2026-06-12
---

# Make-it-sing builds break when stale `Assets/XR/Temp/` blocks AR Foundation move

## Goal

When `uv run install --build` produces a make-it-sing Android APK, materials render pink on device because AR Foundation's build preprocessor failed to move `XRSimulationPreferences.asset` and `XRSimulationRuntimeSettings.asset` out of `Resources/` before the player build. The Simulation shaders (`Hidden/Simulation/URP/Synthetic`, `Simulation/URP/Room X-Ray`, `Simulation/URP/Lit`) then get scanned, `WARNING: Shader Unsupported … All subshaders removed` is emitted, and every reference to those shaders falls through to URP's `FallbackError` on device. Repro shows up reliably for CLI builds and intermittently for editor builds (first attempt pink, second attempt clean after Unity's asset-DB churn happens to clear the way).

## State

- Root cause identified: a previous failed/interrupted build left orphan copies in `MakeItSing-Unity/Assets/XR/Temp/` (dated 2026-06-07). AR Foundation refuses to overwrite, so the move-out step prints `Failed to move the asset … Destination path name does already exist` for both `.asset` files, and the post-build restore prints the symmetric `Temp/ -> Resources/` failure.
- Diagnosis came from comparing two logs at `/make-it-sing/out.txt` (broken CLI build via `uv run install --build`) vs `/make-it-sing/Editor.log` (clean second-attempt editor build). `out.txt` has the `Failed to move the asset` pair at lines 750 / 772 and the `Shader Unsupported … All subshaders removed` triple at lines 660-675. `Editor.log` has neither.
- Ruled out: the recently committed `nographics=False` change in `placeframe-unity`. `out.txt` line 123 shows `Renderer: AMD Radeon 780M Graphics` and OpenGL 4.6 init, so xvfb-run + real GfxDevice is working — texture compression is not the failure.
- Manual fix (clears the blockage for the next build): `rm -rf /make-it-sing/MakeItSing-Unity/Assets/XR/Temp /make-it-sing/MakeItSing-Unity/Assets/XR/Temp.meta`.
- Permanent fix not yet applied; user did not respond to "Want me to apply the permanent fix?" before issuing `/memorize`.

## Decisions

- **Permanent fix shape**: prepend a `ClearStaleXRTemp()` helper to both `ConfigureForAndroidMobile` and `ConfigureForMagicLeap` in `MakeItSing-Unity/Assets/App/Editor/BuildScript.cs`. The helper calls `AssetDatabase.DeleteAsset("Assets/XR/Temp")` when that folder exists. This makes AR Foundation's move-out destination clean regardless of how the previous build ended. Same vulnerability exists for both target configs, so both get the fix.
- **Why not just delete the Temp dir from a shell hook in `placeframe-unity`**: the asset is inside the Unity asset DB; deleting via filesystem leaves stale `.meta` entries. `AssetDatabase.DeleteAsset` is the supported path. Belongs in the Unity-side build script, not the Python wrapper.

## Key files

- `/make-it-sing/MakeItSing-Unity/Assets/App/Editor/BuildScript.cs` — where the permanent fix goes. `ConfigureForAndroidMobile` is around line 126; `ConfigureForMagicLeap` is around line 92. Both currently do `XRPackageMetadataStore` loader swaps, `PlayerSettings.SetGraphicsAPIs`, etc., but no cleanup of `Assets/XR/Temp/`.
- `/make-it-sing/MakeItSing-Unity/Assets/XR/Temp/` — the stale directory. Contains `XRSimulationPreferences.asset` + `.meta` and `XRSimulationRuntimeSettings.asset` + `.meta`, all dated 2026-06-07.
- `/make-it-sing/MakeItSing-Unity/Assets/XR/UserSimulationSettings/Resources/XRSimulationPreferences.asset` and `/make-it-sing/MakeItSing-Unity/Assets/XR/Resources/XRSimulationRuntimeSettings.asset` — the "real" working copies that AR Foundation tries to move into `Temp/` at build-prep and restore at build-post.
- `/make-it-sing/out.txt` and `/make-it-sing/Editor.log` — the two logs that diagnosed this. The first is the broken CLI build, the second is the successful editor build. The salient diff lives in the AR Foundation move messages and the `Shader Unsupported` triple, not in the graphics-device init.

## Pending threads

- Apply the permanent fix to `BuildScript.cs` (add `ClearStaleXRTemp()` helper, call from both `ConfigureForAndroidMobile` and `ConfigureForMagicLeap`). The user was asked but hadn't answered before context handoff.
- After applying, rebuild via `uv run install --build --project MakeItSing-Unity --target android-mobile` and confirm `out.txt` no longer contains `Failed to move the asset` or `Shader Unsupported … Simulation/URP/`.

## Adjacent context (not the bug, but live in this branch)

- This session also landed `/placeframe` `dev` commit `b2bb9e4d` (Backfill camera positions on reconstruction import — extracted `sync_camera_positions` to `docker/api/src/camera_positions.py`, called from `import_reconstruction_tar`) and `7af01df4` (Drop -nographics for Unity player builds). Both are local-only — `GITHUB_TOKEN` in this sandbox belongs to `tylershatch` and is 403 against `outernet-foundation/placeframe`; user must push from their own host.
- Make-it-sing branch `feature/demo` has two new commits: `b1d4335` (placeframe pin bumped to `7af01df4` in `pyproject.toml` + `uv.lock`) and `d91c4ce` (UI shows first loaded localization map name — `AppState.loadedMapName`, `LocalizationManager` stashes name from `GetLocalizationMaps`, `AppUI.cs` Text binds to it). The pin still points to `7af01df4`, not `b2bb9e4d`; bump it again if a consumer should pick up the camera-positions backfill.
- The demo backend currently has reconstruction `46890b09-ee89-4c47-8656-238d6b868dbc` (`demo-site`) imported with localization map `b6050f24-1835-4e53-a217-e01a4123448d` at ECEF `(0,0,0)` and 114 populated `localization_map_camera_positions` rows. `LocalizationManager.cs` line 75 hard-zeros `ecefPosition` and queries within `MAP_LOAD_RADIUS=100`, so this map will load on the first `UpdateMaps` tick after login.
