---
id: T117
title: Investigate MagicLeap_PipelineAsset.asset mutation during Unity builds
status: plan-needed
depends_on: []
---

# T117: Investigate MagicLeap_PipelineAsset.asset mutation during Unity builds

## Goal

Determine exactly what changes in `MagicLeap_PipelineAsset.asset` during Unity builds, why it changes, and whether the change can be prevented or committed once so it stabilizes.

## Context

During CI Unity builds on `feature/ci-cd`, the staleness check (`BuildUtility.VerifyNoNewChanges()`) detects that `legacy/Outernet.Client/Assets/Settings/MagicLeap_PipelineAsset.asset` is modified by the build process. This happens on the **win64** and **linux64** Outernet.Client builds — platforms that don't even target MagicLeap.

Key observations from CI run 23274471263:
- `SaveAssets()` + `SnapshotChangedFiles()` correctly captures `ProjectSettings.asset` as an expected mutation (from configure methods + InjectVersion).
- `MagicLeap_PipelineAsset.asset` is NOT in the snapshot — it is clean after `SaveAssets()` and before `BuildPipeline.BuildPlayer()`.
- After `BuildPipeline.BuildPlayer()` completes, `VerifyNoNewChanges()` detects it as a new mutation.
- This means `BuildPipeline.BuildPlayer()` itself (or Unity's internal build pipeline) is dirtying and serializing this asset during the build.

The asset is a URP (Universal Render Pipeline) configuration asset. It contains rendering settings (shadow resolution, MSAA, shader variant stripping, etc.) and has a `k_AssetVersion: 12` field. URP uses an internal version-based upgrade system (`ISerializationCallbackReceiver`) that can bump `k_AssetVersion` and mark assets dirty during deserialization.

Hypothesis: the mutation may be deterministic (e.g. URP adding a new field with a default value, or normalizing serialization order). If so, committing the post-build state should stabilize the file. If the mutation is non-deterministic (e.g. contains a timestamp or hash that changes per build), a different approach is needed.

The broader staleness check system (snapshot → build → verify → restore) was introduced in commit `220db8ed`. The current workaround options are: soften the verify to a warning, or unconditionally restore all changes post-build. But we want to understand the root cause first.

## Key files

- `legacy/Outernet.Client/Assets/Settings/MagicLeap_PipelineAsset.asset` — the URP pipeline asset being mutated
- `legacy/Outernet.Client/Assets/Settings/MagicLeap_PipelineAsset_ForwardRenderer.asset` — companion renderer asset (may also be affected)
- `packages/unity/Placeframe/Assets/Package/Core/Editor/BuildUtility.cs` — staleness check implementation
- `legacy/Outernet.Client/Assets/OuternetClient/Editor/BuildScript.cs` — build scripts that configure MagicLeap/Android settings
- `build/src/build_scripts/placeframe/ci/build_unity.py` — Python CI orchestration

## Approach

Replicate the CI build locally to capture the exact diff. Then analyze whether the change is deterministic and committable.

## Done when

- We know exactly what bytes/fields change in `MagicLeap_PipelineAsset.asset` during the build
- We know whether the change is deterministic (same input → same output) or varies per build
- If deterministic: the post-build state is committed so subsequent builds produce no diff
- If non-deterministic: the mechanism is documented and a decision is made on how to handle it (warn-and-restore, exclude from verify, etc.)
- The staleness check passes for all Outernet.Client build targets in CI

## Environment notes

- Unity batchmode builds (cold project open + IL2CPP/Mono build) take well over 10 minutes in the sandbox container. All Unity build commands must be run with no timeout or a very long timeout (30+ minutes). The default 2-minute tool timeout will kill the build mid-flight.

## Next step

Replicate CI locally in the sandbox container (Unity 6000.0.66f1 is available at `/opt/unity/`). Steps:

1. Install dotnet SDK (`bash /placeframe/build/src/build_scripts/third-party/dotnet-install.sh --channel 8.0`) — **done**
2. Run `dotnet tool restore && dotnet nugetforunity restore legacy/Outernet.Client` — **done**
3. Write `.build-version.json` stub — **done**
4. Run Unity batchmode targeting StandaloneLinux64 with `-executeMethod Outernet.Client.Build.BuildForLinux64` (matching CI). **Must use a long timeout or run in background.**
5. After Unity exits, run `git diff legacy/Outernet.Client/Assets/Settings/MagicLeap_PipelineAsset.asset` to see the exact changes
6. Commit the diff and run the build again — does the file change a second time?
7. If it stabilizes: commit the post-build state and verify in CI
8. If it changes again: inspect the diff for non-deterministic fields (timestamps, hashes, random IDs) and investigate URP's `k_AssetVersion` upgrade path
