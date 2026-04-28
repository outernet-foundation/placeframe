---
id: T98
title: Cesium combine-and-publish job fails with Unity license entitlement 404
status: open
depends_on: [T96]
---

# T98: Cesium combine-and-publish job fails with Unity license entitlement 404

## Goal

Diagnose and fix the deterministic license failure in the Cesium workflow's combine-and-publish job. The job fails 100% of the time on build-number 14 (2 consecutive failures), despite using an identical ULF, machine-id, and container image as the codegen jobs that succeed.

## Symptom

The combine-and-publish job in `build-cesium-native.yml` fails when running Unity to generate `.meta` files:

```
[Licensing::Module] Error: Access token is unavailable; failed to update
[Licensing::Client] Successfully updated license
[Licensing::Client] Error: Code 404 while processing request (status: Found 0 entitlement groups and 0 free entitlements matching requested entitlement ids)
[Licensing::Module] Error: 'com.unity.editor.headless' was not found.
No valid Unity Editor license found. Please activate your license.
```

The Unity invocation that fails is in `combine_cesium_package.py:118`:
```python
run_command(
    f"xvfb-run unity-editor -batchmode -nographics -quit -projectPath {PROJECT_PATH}"
    f" -executeMethod ConfigureNativePlugins.Configure -logFile /dev/stdout",
    stream_log=True,
)
```

## Evidence gathered

### Workflow run 23015374218 (build-number 14, feature/pulsar)

**Phase 0 — activate-license (job 66848588071)**: SUCCESS
- Container: `unityci/editor:2022.3.42f1-linux-il2cpp-3`
- LicensingClient version: `1.15.5+a2f8afb`
- Machine Id: `D7nTUnjNAmtsUMcnoyrqkgIbYdM=`
- Serial: `F4-U494-TQ59-KZ2R-86E3-XXXX`
- Sequence: `Successfully updated the access token` → `Successfully activated the entitlement license` → `Successfully activated ULF license`
- ULF pushed to ORAS: `ghcr.io/.../unity-license:v1` digest `sha256:53247959674a47ff3b4d454eae61986cb0f7f6fbe7621993bc441478f03a07c3`
- Time: 17:36:13 – 17:36:18

**Phase 1 — codegen (5 jobs, all SUCCESS)**:
- All 5 jobs restored the same ULF (same digest) and launched Unity
- All 5 had initial `Access token is unavailable; failed to update` (normal for cold ULF restore)
- All 5 then `Successfully updated license` → `Successfully resolved entitlement details` → serial assigned
- Same container image, same LicensingClient version, same machine ID
- Times: 17:36:25 – 17:43:27

**Phase 2 — native build (3 jobs, all SUCCESS)**: No Unity, no license needed.

**Phase 3 — combine-and-publish (job 66845928873)**: FAILURE (attempt 1)
- Same container image: `unityci/editor:2022.3.42f1-linux-il2cpp-3`
- Same LicensingClient version: `1.15.5+a2f8afb`
- Same machine ID: `D7nTUnjNAmtsUMcnoyrqkgIbYdM=`
- Same ULF digest: `sha256:53247959674a47ff3b4d454eae61986cb0f7f6fbe7621993bc441478f03a07c3`
- Sequence: `Access token is unavailable; failed to update` → `Successfully updated license` → **`Error: Code 404 ... Found 0 entitlement groups`** → `'com.unity.editor.headless' was not found`
- Time: 18:39:13

**Phase 3 — combine-and-publish (job 66848588783)**: FAILURE (attempt 2, re-run of failed job)
- Identical error sequence
- Same ULF digest pulled
- Time: 18:55:51

### Previous successful run 22988943705 (build-number 13)

- Phase 0 activated at 06:06, pushed ULF
- Phase 1: **4 of 5 codegen jobs hit ORAS cache and did NOT launch Unity.** Only android codegen (job 66745584897) launched Unity (it was new in T97). The other 4 had cache hits.
- Phase 3 combine succeeded at 07:05 — same `Access token is unavailable` → `Successfully updated license` → `Successfully resolved entitlement details`

### Key difference between runs

| | Build 13 (success) | Build 14 (failure) |
|---|---|---|
| Codegen cache | 4 hits, 1 miss (android) | 0 hits, 5 misses (all busted by build-number bump) |
| Unity licensing sessions in codegen | 1 | 5 |
| Total Unity licensing sessions | 3 (Phase 0 + 1 codegen + combine) | 7 (Phase 0 + 5 codegen + combine) |
| Time between Phase 0 and combine | ~59 min | ~63 min |
| Combine job result | Success | Failure (2/2 attempts) |

## Hypotheses investigated

### 1. Transient Unity server failure (REJECTED by user)

GameCI's issue tracker documents transient licensing failures: [unity-builder#611](https://github.com/game-ci/unity-builder/issues/611) (80% failure rate), [unity-builder#597](https://github.com/game-ci/unity-builder/issues/597) (10-20% failure rate). GameCI's v4 `unity-builder` action added retry logic (5 retries with backoff) for this. Our scripts call Unity directly without retry.

However: the failure reproduced 100% (2/2 attempts), which is inconsistent with a random transient issue. User rejected this as root cause.

### 2. Seat exhaustion from concurrent sessions (REJECTED)

Initial theory: Unity serial licenses have 2-seat limits, and 5+ concurrent sessions exhausted them. **This is wrong.** GameCI hardcodes `/etc/machine-id` to `576562626572264761624c65526f7478` in all Linux Docker images. All containers appear as one machine to Unity's licensing server. This is the entire design of GameCI's licensing model — 5+ parallel builds share 1 activation slot. Research in `.pulsar/research/win64-container-machine-identity.md` documents this.

### 3. ULF overwritten by Unity workflow (PARTIALLY CORRECT — see root cause)

The Unity workflow (`build-unity.yml`) also pushes to the same `unity-license:v1` ORAS tag. This workflow triggered at 17:52 (between Cesium codegen and combine). The ULF digest was NOT overwritten (verified: combine pulled the same digest as Cesium Phase 0 pushed).

However, the investigation missed the critical fact: the `main` branch's `build-unity.yml` is an **older version** with no separate `activate-license` job. Each build job does its own inline `-serial` activation AND `-returnlicense`. The `-returnlicense` is what killed the Cesium workflow's activation.

### 4. Server-side access token state corrupted by concurrent refreshes (REJECTED — superseded by root cause)

The concurrent sessions were a red herring. The real variable wasn't the number of codegen sessions — it was whether the Unity workflow ran between Phase 1 and Phase 3.

## Root cause (CONFIRMED)

**The Unity workflow on `main` returned the Cesium workflow's license activation via `-returnlicense`.**

### The `main` branch's `build-unity.yml`

The `feature/pulsar` branch refactored `build-unity.yml` to use a single `activate-license` job with no per-job return. But the `main` branch (commit `ebbf7e5c`) still has the **old version** where each of 5 build jobs:
1. Does its own `-serial F4-U494-TQ59-KZ2R-86E3-XXXX` activation (same serial as Cesium)
2. Runs the build
3. Calls `-returnlicense` in an `if: always()` step

All 5 build jobs share the same GameCI machine-id (`D7nTUnjNAmtsUMcnoyrqkgIbYdM=`) as the Cesium workflow.

### Timeline

| Time | Event |
|------|-------|
| 17:36 | Cesium Phase 0: `-serial F4-U494-...` activates seat on machine Y |
| 17:36–17:43 | Cesium Phase 1: 5 codegen jobs use the ULF — all succeed |
| 17:52–17:57 | Unity workflow (main, run 23016182778): 5 build jobs each do `-serial F4-U494-...` with Unity 6000.0 |
| 17:59–18:03 | Unity workflow: 5 build jobs each `-returnlicense` → **deactivate serial on machine Y** |
| 18:39 | Cesium Phase 3: combine restores ULF → serial is deactivated → "Found 0 entitlement groups" → FAILS |
| 18:55 | Re-run: same ULF, serial still deactivated → FAILS again |

### Proof from Unity workflow logs (run 23016182778)

All 5 jobs successfully returned the license:
```
Outernet.Client (linux64)     17:59:57  Successfully returned ULF license with serial number : "F4-U494-TQ59-KZ2R-86E3-XXXX"
Outernet.Client (magicleap)   18:00:36  Successfully returned ULF license with serial number : "F4-U494-TQ59-KZ2R-86E3-XXXX"
Outernet.Client (android)     18:01:01  Successfully returned ULF license with serial number : "F4-U494-TQ59-KZ2R-86E3-XXXX"
AndroidMobile (android)       18:02:07  Successfully returned ULF license with serial number : "F4-U494-TQ59-KZ2R-86E3-XXXX"
MapRegistrationTool (linux64)  18:03:41  Successfully returned ULF license with serial number : "F4-U494-TQ59-KZ2R-86E3-XXXX"
```

### Why build 13 succeeded

Build 13's combine finished at 07:07. The next Unity workflow (22991509674) started at 07:39 — its `-returnlicense` calls happened at 07:50–08:41, well after the combine succeeded.

### Why the original "concurrent sessions" correlation was misleading

The apparent correlation between "7 licensing sessions" (failure) and "3 sessions" (success) was coincidental. The actual variable was timing: whether the Unity workflow's `-returnlicense` calls ran between Cesium's Phase 1 and Phase 3. Build 14 had all caches cold, making Phase 1 take longer, which widened the window for the Unity workflow to slot in between phases.

### Two independent problems exposed

1. **Immediate cause**: `main`'s old `build-unity.yml` returns the shared serial via `-returnlicense`, deactivating Cesium's activation
2. **Structural problem**: Both workflows share the same serial AND the same ORAS tag (`unity-license:v1`), creating race conditions even after fixing the immediate cause

## Investigation results (previously "things not yet investigated")

1. **GameCI's `unity-builder` v4 license lifecycle**: Researched. GameCI does activate → build → return-license for EVERY build. Each invocation is a complete license cycle. They also have retry logic (5 retries with exponential backoff: 15s, 30s, 60s, 120s, 240s) on Linux only. Our approach (activate once, share ULF) is fundamentally different from GameCI's per-job model.

2. **License return**: This was the root cause. The `main` branch's `build-unity.yml` returns the license after each build job. Our Cesium workflow never returns it, which is correct for the "activate once, share ULF" model — but the Unity workflow's returns deactivate the shared serial.

3. **Access token expiry**: The `Access token is unavailable; failed to update` message is normal for a restored ULF. The LicensingClient refreshes it online and succeeds ("Successfully updated license"). The access token behavior is not the problem — the serial deactivation is.

4. **Codegen license need**: Still relevant as a cleanup item. Codegen only needs a license when the ORAS cache misses and Unity actually runs. On cache hits, the ULF restore is wasted.

5. **ORAS tag `v1` collision**: Confirmed as a structural problem. The `main` branch's `build-unity.yml` doesn't push to ORAS (it uses inline activation), but the `feature/pulsar` version does push to `unity-license:v1`, creating a collision with the Cesium workflow. Needs version-specific tags.

6–8. **Not investigated** — superseded by root cause discovery.

## Key files

- `.github/workflows/build-cesium-native.yml` — Cesium workflow (Phase 0 → codegen → native → combine)
- `.github/workflows/build-unity.yml` — Unity workflow (also pushes to `unity-license:v1`)
- `.github/workflows/codegen-cesium.yml` — reusable codegen workflow
- `.github/actions/activate-unity-license/action.yml` — activation + optional ORAS push
- `.github/actions/restore-unity-license/action.yml` — ORAS pull + .NET setup
- `build/src/build_scripts/combine_cesium_package.py:117-128` — the failing Unity invocation
- `.pulsar/research/win64-container-machine-identity.md` — prior research on GameCI machine-id model

## Related tickets

- T96 — Cesium from-source build (parent ticket)
- T97 — Android codegen speed fix (caused the build-number bump that triggered this)
- T79 — Unity license activation observability (may have relevant prior work)

## Reproduction

Trigger the Cesium workflow (any build-number) while the Unity workflow is running or has recently completed on `main`. The Unity workflow's `-returnlicense` deactivates the serial, causing the combine job to fail. The cache-busting behavior that originally correlated with the failure was a red herring — it only mattered because it extended the window between Phase 1 and Phase 3, giving the Unity workflow time to run in between.

## Fix applied

Converted `activate-unity-license` to a restore-or-activate pattern: try `restore-cache` from ORAS first, only activate a fresh license on cache miss, only save on fresh activation. Both `activate-unity-license` and `restore-unity-license` now use the shared `restore-cache`/`save-cache` scripts instead of inline `oras` commands.

The ULF becomes a long-lived cached artifact. Recovery: `oras delete ghcr.io/<repo>/cache/unity-license:v1` to force re-activation.

## Done when

- Root cause identified with definitive evidence (not speculation) — **DONE**
- Fix applied and verified: full Cesium pipeline (all caches cold) completes successfully
