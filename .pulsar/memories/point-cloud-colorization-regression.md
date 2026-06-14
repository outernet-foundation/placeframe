---
updated: 2026-06-14
---

# Reconstruction point cloud lost colorization — all points render white

## Goal
The reconstruction point-cloud map used to render with per-point color; sometime
around 2026-06-10 to 06-12 every point started rendering uniformly white. Find the
regression and fix it. This memory captures a git-history-only diagnosis (no build was
run); the fix still needs to be implemented and tested on-device.

## State
- Full color pipeline traced end to end (reconstructor → API → Unity parse → render);
  every stage except the render swap was ruled out as unchanged in the regression window.
- Culprit identified by elimination: commit **`5dce11ac` "Render point cloud as
  billboarded quad mesh instead of ParticleSystem"** (2026-06-10). It replaced the
  Unity `ParticleSystem` renderer (which set `particles[i].startColor = point.color`,
  known-good) with a hand-rolled quad mesh plus a brand-new custom unlit shader
  `Placeframe/PointCloud`.
- The new code *looks* correct, which is why it compiled and slipped through:
  `LocalizationMap.cs:BuildPointMesh` writes `colors[...] = point.color` and calls
  `mesh.SetColors(colors)`; the shader declares `half4 color : COLOR` and the fragment
  returns `input.color * _Tint`.
- Suspected root cause: the new shader's **vertex `COLOR` stream is not reaching the
  fragment shader at render time**. When the `COLOR` semantic gets no data it defaults
  to `(1,1,1,1)` = white — exactly matching "was colored, now all white". This is a
  GPU/binding bug, not a data bug.
- Ruled out (all unchanged or color-irrelevant in the window):
  - Color generation: `docker/reconstructor/.../colmap.py` (`point_cloud_colors[...] =
    point.color`) last changed ~Jun 1.
  - Server serialization: `docker/api/.../reconstructions.py` — commit `048bfb87`
    (Jun 10) only buffered the binary response for Content-Length; the uint8 color byte
    format is identical.
  - Unity parse: `VisualPositioningSystem.cs` `ParseReconstructionPointPayload`
    (offset `4 + positionsByteCount`, `Color32(r,g,b,255)`) — parse logic unchanged.
  - Point-size commits `b2be9f0a` / `c3313124` (Jun 12–13) only flip `_PointSize`
    (0.0075 → 0.02); they don't touch color.
  - `PointCloud.mat` `_Tint` is `(1,1,1,1)` (correct) and `SetColor()` (which writes
    `_Tint`) has no callers, so the tint is never forced — output == raw vertex color.
  - The `LocalizationMap.prefab` `MeshRenderer` correctly references `PointCloud.mat`.

## Decisions
- The fix lives entirely in `5dce11ac`'s shader/mesh path. The reconstructor, API, and
  Unity parser need no changes — the data path is provably unchanged.

## Open questions
- Is `SetColors(Color32[])` actually binding to the `COLOR` semantic the shader expects,
  or is the channel being dropped? Confirm whether vertex colors reach the fragment shader
  on-device — e.g. temporarily route a corner UV or a constant into the fragment to prove
  the channel is the missing link, vs. the points simply being uncolored.

## Key files
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/LocalizationMap.cs` — `BuildPointMesh` builds the quad mesh and sets vertex colors via `mesh.SetColors`.
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/Assets/PointCloud.shader` — new `Placeframe/PointCloud` unlit shader; declares `half4 color : COLOR`, fragment returns `input.color * _Tint`. Prime suspect for the COLOR-stream binding bug.
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/Assets/PointCloud.mat` — `_Tint` = `(1,1,1,1)`, `_PointSize` = 0.02.
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/VisualPositioningSystem.cs` — `ParseReconstructionPointPayload`; parse offsets confirmed correct/unchanged.

## Pending threads
- Draft and test the shader/mesh fix in `5dce11ac`'s path so vertex colors reach the
  fragment shader. Build with `uv run compile-unity --project CaptureTool --build
  android-mobile` and verify on-device that points render colored again.
