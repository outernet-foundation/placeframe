---
updated: 2026-06-14
---

# Relocalization instability is a constant ~7% device-side VIO scale bias (ARFoundation outdoors); the map is confirmed correct

## Goal

A `feature/better-filter` field run (make-it-sing backend, demo-site outdoor courtyard scan)
showed content that is "off when I shift perspective, then re-aligns" as the user walks. Earlier
analysis decomposed the felt instability into a slow, **position-locked** swing (not fast jitter,
not VIO drift) consistent with a **~7–10% metric-scale mismatch** between map and device. The
question driving this memory was *which side* the mismatch is on — device VIO, or local map warp.
**That question is now answered: it is the device (ARFoundation outdoor VIO), not the map.** A
follow-up question — could the bias be an artifact of a poorly-chosen (frame-rate-throttling)
camera config? — is **also now answered: no, not on this hardware (Pixel 9).** The one fix that was
left — **online per-session scale compensation (Thread A)** — is **now IMPLEMENTED in the working
tree (uncommitted, and per explicit user instruction NOT yet compiled or tested — unverified).**

## State

### Thread A IMPLEMENTED (uncommitted, unverified — NOT compiled, NOT tested) (NEW, this session)

Online VIO-scale compensation was built across the Placeframe Unity package
(`packages/unity/Placeframe/Assets/Package/Core/Runtime/`). The user explicitly asked to stop
before compiling/testing, so **none of this has been run** — treat it as draft until
`compile-unity` + the Unity tests pass and a field run confirms it.

**Conceptual framing (the user worked through this; it matters):** this fixes a *genuine VIO
deficiency* (monocular-inertial metric-scale bias), it does not paper over one. `DriftCorrectionController`
already exists to correct VIO's *pose* drift; this adds the *scale* dimension to that same loop,
using the server fixes as metric truth — i.e. sensor fusion. Without a correcting layer, ARFoundation
monocular VIO in a large outdoor space swims from both pose drift (already handled) and scale bias
(this change). It is **device-agnostic by construction**: a zero-bias tracker converges to ratio 1.0
→ offset 0.

**What was built:**

- `RelocalizationConfig.cs` — new compensation consts: `CompEnabled` (true, but **`#if MAGIC_LEAP`
  → false** — ML2 defaults OFF because its stereo tracker is expected metric and on a near-zero-bias
  device the estimate would be dominated by map/PnP noise; stays off until its scaleRatio is
  characterised), `CompDeadzone` (0.03 — suppress the offset entirely below 3% estimated bias so a
  metric device gets exactly zero compensation), `CompWarmupSamples` (6), `CompEmaAlpha` (0.1),
  `CompScaleRatioMin/Max` (0.80/1.25 clamp band — out-of-band = VIO jump, never reaches the EMA),
  `CompMaxOffsetMeters` (3.0 safety rail), `CompOffsetEaseSeconds` (0.25).
- `MultiHypothesisFilter.cs` — exposes `LastValidScaleRatio` (nullable double): set only on a matched
  segment with `mapDelta > 1e-3`, cleared at the start of `ApplyMeasurements` and in `Reset()`. It is
  the EMA input; **the filter still only measures, never applies.**
- `DriftCorrectionController.cs` — the core change. Split into a raw-VIO-anchored `_base` (the control
  law — residual/deadband/slew/motion-accumulation all run on this; residual now computed from `_base`,
  not the published frame) and a published `Current = _base ⊕ offset` (via `Republish()`/`ComposeOffset`).
  New state: per-session EMA of scaleRatio (`_scaleEma`, `_scaleSamples`), `_compAnchorVio`,
  `_offsetTarget`, `_offsetPublished`. `Observe` gained a `double? scaleRatio` param. The offset =
  `(1 - biasInverse)·(vio - compAnchor)`, clamped; `biasInverse = 1/ema` once warmed AND past the
  dead-zone AND `CompEnabled`, else 1.0 (→ zero offset). **Continuity at corrections via two
  independently-eased quantities:** `_base` slews `base_old→bestEstimate` while `_offsetPublished`
  eases toward the new (regrowing-from-zero) target — composed, the published frame is continuous (no
  jump). The offset *target* is set at `Observe` (localization) cadence and eased per-frame in
  `Advance` (which gets only `deltaTime`), so the `ICameraProvider` abstraction is untouched — no live
  `Camera.main` in Core.
- `VisualPositioningSystem.cs` — `Localize` reads `LastValidScaleRatio` gated on
  `frame.TrackingState == Tracking` (frozen/null otherwise) and passes it into `Observe`; `Set` now
  takes a vioPosition (bootstrap passes the frame's; operator override passes `_lastVioPosition`). Also
  this session: `VisualPositioningSystem.Log{Debug,Warn,Error}` were widened `internal`→`public`
  (recorded under the camera-config diagnostic below) so the sibling ARFoundation assembly logs to the
  same Loki sink.
- New tests `Core/Tests/Editor/DriftCorrectionControllerTests.cs`: sign, warmup, null/standstill,
  dead-zone, correction-continuity, and offset-never-inflates-residual. **Not yet run; no `.meta` yet**
  (Unity generates it on import).

**New diagnostics (Loki, `step=key=value` via `VisualPositioningSystem.LogDebug`):**
`step=reloc.scale` (sample/inBand/ema/samples/biasInverse — EMA convergence) and extended
`step=reloc.frame` hold/correct lines (offsetMag/offsetTargetMag/anchorDist/biasInverse).

**Success-metric note (preserve):** the filter's raw `scaleRatio` keeps reading ~0.93 after this
ships — it measures the *unchanged* device and is the EMA input, **NOT** the success signal. Success =
`residM` staying small and `action=correct` frequency dropping vs the baseline session.

### Camera-config diagnostic run — rules out Thread B on Pixel 9

- The camera-config diagnostic (Thread B's first step from the prior memory) was **implemented and
  shipped in a new APK**, then run on a **Pixel 9**.
- Diagnostic logic lives in `CameraProvider.cs` `PrepareCamera`: it logs **every** available
  `XRCameraConfiguration` as `step=camera.config.available index=N width=W height=H framerate=F`,
  plus a `step=camera.config.selected` line. To reach Loki alongside `scaleRatio` (the package's
  single log facade), `VisualPositioningSystem.LogDebug/LogWarn/LogError` were widened from
  `internal` to `public` so the sibling `Placeframe.Core.ARFoundation` assembly can log to the same
  sink (no `InternalsVisibleTo` exists; widening the three levels together keeps the facade
  coherent).
- **Loki result:** 9 available configs — three resolutions (640×480, 1280×720, 1920×1080), each
  exposed 3 times (ARCore's usual triplication for CPU-image/GPU-texture/depth combos) — and
  **EVERY config reports framerate=30.** Selected config was **1920×1080@30**.
- **DECISIVE — Thread B is empirically RULED OUT on Pixel 9:** max resolution costs **zero** frame
  rate (all configs are 30 fps; there is no higher-fps config to switch to). A frame-rate-aware
  selection change would be a **no-op** here, and dropping resolution would only lose detail (some of
  which survives the server's 1024 px downsample) for **no** fps gain. The premise behind Thread B
  ("max-res throttles tracking fps") is false on this device.
- **Consequence:** this confirms the ~7% scale bias is the **fundamental ARFoundation outdoor
  monocular-inertial scale limitation**, NOT an artifact of a throttled-tracking-fps config choice.
  → **Thread A (online per-session EMA scale compensation) is now THE fix**, not just the
  device-agnostic catch-all. There is no cheaper source-side win hiding behind it on this hardware.
- **Caveat to preserve:** this is **Pixel-9-specific** evidence. A different ARCore phone *could*
  expose a 1080p@30-vs-720p@60 split where Thread B would matter — the diagnostic is now
  **permanently in the build** to catch that if it shows up. On ML2 the question is moot (different
  tracker entirely).

### Decisive second device run — answers "map or device?"

- A **second device run** was captured with the new `scaleRatio` diagnostic baked into the filter
  (new APK). 133 new-format match lines, ~189 s, ~131 m walked across a ~28 m (X) × 30 m (Z) flat
  courtyard. The per-measurement diagnostic logs, in the **map frame**: `mapX/mapY/mapZ` (camera
  position), `mapDelta` (map-frame motion since that hypothesis was last supported), and
  `scaleRatio = vioDelta / mapDelta`.
- **DECISIVE RESULT — the ratio is constant across the whole map:**
  - `scaleRatio` median ≈ **0.93**, and it is **flat everywhere**.
  - mapX-quartile medians: 0.921 / 0.933 / 0.930 / 0.924. mapZ-quartile medians: 0.926 / 0.927 /
    0.923 / 0.956. Quadrant medians span 0.911–0.947.
  - Correlations are all ≈ 0: corr(scaleRatio, mapX) = −0.08, corr(·, mapY) = −0.10,
    corr(·, mapZ) = +0.06, corr(·, radius) = +0.15.
  - Spatial variation is ±0.02; offset-from-1.0 is ~0.07. The signal is an **offset**, not a
    gradient → the **constant-ratio signature of device-side ARFoundation VIO scale bias, NOT map
    warp.**
- This, combined with the prior turn's confirmed-correct map baseline (119.97 mm = ZED X 120 mm),
  **rules out both map warp and global map-scale error.** The two remaining candidates from the
  prior memory are now collapsed to one.
- **Server corroboration that the measurement is trustworthy:** 159 clean PnP solves, a coherent
  `camPos` trajectory, retrieval spanning ~22 m (the expected courtyard center-facing geometry).

### Conclusion

- **ARFoundation outdoor VIO underreports motion by ~7%**: when it thinks you walked 0.93 m you
  actually walked 1.0 m. Content rides the under-scaled frame between corrections, drifts, then
  snaps back at the next correction.
- **Not fixable in reconstruction** (the map is correct). **Not fixable by smoothing** (this is a
  scale offset, not jitter).

### Reconstruction + capture baseline check (from prior turn — still holds)

- Metric scale rides entirely on the ZED stereo rig baseline; the reconstructor holds the rig
  baseline fixed through all SfM and BA, post-SfM `Sim3d` scale = 1.0, `UNIT.METER` set explicitly.
- Extracted the demo-site reconstruction's own COLMAP model from `demo-site.tar`: baseline used by
  COLMAP = **119.97 mm** vs ZED X factory **120 mm** (0.02% off, dead-on); both cameras' BA-refined
  focals agree to 0.01%, so BA did not absorb scale into focal length. **Exonerates the
  reconstruction/capture pipeline for a global scale error on this map.**
- Latent code smells noted but NOT the cause (magnitude came out right): the
  `x = -stereo_transform_translation[0]` negation TODO (`zed.py:412`) and the rectified-vs-raw
  calibration choice (`zed.py:365`). The far-field stereo-triangulation weakness (12 cm baseline,
  `triangulation_minimum_angle = 3.0°` → metric structure only within ~2.3 m, only 114/2773 matches
  stereo-verified) was the *warp* mechanism — now ruled out by the flat `scaleRatio`.

### Code shipped this session

- **Committed** (`a5586994` and earlier): `scaleRatio` per-measurement diagnostic in
  `MultiHypothesisFilter.cs` + a `SPEC.md` note; camera-config diagnostic in `CameraProvider.cs`
  `PrepareCamera` (logs every available config's width/height/framerate + the selected one) and the
  `internal`→`public` widening of `VisualPositioningSystem.LogDebug/LogWarn/LogError` so
  `CameraProvider` (sibling `Placeframe.Core.ARFoundation` assembly) can log to the Loki sink. **The
  camera-config diagnostic is a retained probe**, not scaffolding — keep it to catch a fps-split on a
  different ARCore device.
- **Uncommitted, unverified** (Thread A; see the IMPLEMENTED section above): `RelocalizationConfig.cs`,
  `MultiHypothesisFilter.cs` (`LastValidScaleRatio`), `DriftCorrectionController.cs`,
  `VisualPositioningSystem.cs`, and the new `DriftCorrectionControllerTests.cs`. Not compiled, not run.

## Decisions

- **The "is it map or device?" open question is closed: it is the device.** Uniform `scaleRatio` ≈
  0.93 with zero spatial correlation + confirmed-correct 120 mm map baseline ⇒ ARFoundation outdoor
  monocular-inertial VIO scale bias.
- Smoothing/EMA stays demoted for *jitter* — but an EMA **of the scale ratio** is now the core of
  the proposed online fix (Thread A below), a different use entirely.

### Thread A — online VIO-scale compensation (THE fix; IMPLEMENTED, unverified)

- **Built this session; see State above for the full design.** Code is in the working tree,
  uncommitted, and **not yet compiled or tested** (user asked to stop before that). Rollout decision:
  **ship ON for ARFoundation, compare to baseline.**
- The filter computes `scaleRatio` per segment (`LastValidScaleRatio`). The applied fix: a
  **per-session EMA** of it, and the published frame is shifted by `(1 - 1/ema)` of the distance
  walked since the last re-anchor (`1/ema ≈ 1.075` here). The shift lives as an **offset on top of a
  raw-VIO-anchored base** — the offset never enters the residual, so it cannot inflate the deadband or
  change correction frequency.
- **Online (self-estimating), NOT a hardcoded constant** — this is the device-agnostic property: this
  phone converges to ~7%, a metric tracker (ML2) converges to ~1.0 and the offset vanishes via the
  dead-zone. A hardcoded ~1.075 would be this-phone-specific and *wrong* elsewhere.

### Thread B — source-side camera-config/frame-rate fix (RULED OUT on Pixel 9; diagnostic shipped)

- The original audit of `CameraProvider.cs` config selection (`PrepareCamera`, ~lines 156–184): it
  picks purely the **highest resolution** (max `width*height`), **ignoring frame rate**. The theory
  was that on ARCore the max-res config might run at a **lower fps**, throttling tracking/scale
  observability for **no benefit** (the server downsamples every image to a 1024 px shorter side
  anyway, `canonicalize_intrinsics`).
- **This theory is now empirically dead on Pixel 9** (see State above): all 9 available configs are
  30 fps, so there is no higher-fps config to switch to. The fps-aware selection change would be a
  no-op. The diagnostic that proved this is **retained in the build** as a probe for other ARCore
  devices that *might* have a fps split.
- Ruled NOT-the-cause but worth recording from the audit:
  - Auto-focus is disabled — **correct** (keeps intrinsics stable; minor far-scene blur risk only).
  - pose↔image timing lag (reads `Camera.main` pose after acquiring the image) → motion-proportional
    *noise*, not a scale bias.
  - The live-localization path correctly uses the raw full-6DoF `Camera.main` pose, **not** the
    level-reference anchored path (that anchored path is disk-recording only).

## Open questions

- Thread A's design questions (EMA time constant, warm-up, standstill gating) are now **answered in
  code** — `CompEmaAlpha=0.1`, `CompWarmupSamples=6`, and `LastValidScaleRatio` is null on
  standstill/`mapDelta ≤ 1e-3` segments. What remains is *empirical*: do the chosen constants behave
  on a real walk? Resolve by compiling, running the tests, and field-testing (see Pending threads).

## Key files

- `packages/unity/Placeframe/Assets/Package/ARFoundation/Runtime/CameraProvider.cs` — `PrepareCamera`
  config selection at lines ~156–184: picks max `width*height`, ignores frame rate. Now also carries
  the retained camera-config diagnostic (`step=camera.config.available` per config +
  `step=camera.config.selected`). Auto-focus disabled here too. Lives in the
  `Placeframe.Core.ARFoundation` assembly.
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/VisualPositioningSystem.cs` — the package's
  log facade; `LogDebug/LogWarn/LogError` are now `public` (were `internal`) so the sibling
  ARFoundation assembly can log to the same Loki sink.
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/MultiHypothesisFilter.cs` — the filter;
  carries the `scaleRatio` diagnostic and now exposes `LastValidScaleRatio` (nullable; set only on a
  matched segment with `mapDelta > 1e-3`, cleared in `ApplyMeasurements`/`Reset`). Source of the
  per-segment ratio Thread A's EMA consumes. Still only measures, never applies.
- `DriftCorrectionController.cs` (alongside) — Thread A's core: raw-VIO-anchored `_base` (control law)
  + published `Current = _base ⊕ offset`; per-session scaleRatio EMA; offset eased in `Advance`,
  target set in `Observe`. `RelocalizationConfig.cs` alongside carries all `Comp*` consts
  (`#if MAGIC_LEAP` gates `CompEnabled` off on ML2).
- `packages/unity/Placeframe/Assets/Package/Core/Tests/Editor/DriftCorrectionControllerTests.cs` —
  new (untracked, no `.meta`); covers sign, warmup, null/standstill, dead-zone, correction-continuity,
  offset-never-inflates-residual. Not yet run.
- `packages/unity/Placeframe/SPEC.md` — filter behavior + diagnostics intent (line ~112).
- `docker/zed-capture/src/zed/zed.py` — capture-side calibration; baseline at `:366–416` (smells at
  `:412` x-negation, `:365` rectified-vs-raw); `UNIT.METER` at `:328`.
- `docker/reconstructor/src/reconstructor/options_builder.py` / `colmap.py` / `rig.py` — rig-baseline
  fixed through BA, Sim3 scale = 1, `triangulation_minimum_angle`.
- `docker/localizer/src/localize.py` — single-PnP localizer; `canonicalize_intrinsics` 1024 px
  downsample (the reason Thread B's fps-over-resolution argument holds); logs `retrieval_span`.
- `scripts/src/scripts/loki_query.py` — hard-codes `placeframe-loki-1`; against make-it-sing the
  loki container is `makeitsing-loki-1`, so pull logs by execing `wget` inside it directly.
- `relocalization-multi-hypothesis-plan.md`, `relocalization-filter-findings.md`,
  `relocalization-false-lock-diagnosis.md`, `relocalization-filter-rewrite.md` — prior chapters.

## Pending threads

1. **Verify Thread A — THE next action.** The code is written but **unverified**. (a) `uv run
   compile-unity` and run the new Editor tests (`DriftCorrectionControllerTests.cs`); (b) field-test on
   the Pixel 9 and compare **residual / correction-rate** to the baseline session — success = `residM`
   small and `action=correct` frequency dropping, NOT the raw `scaleRatio` (which stays ~0.93). Then
   commit (the four `Core/Runtime/*.cs` changes + the test file).
2. **Before enabling compensation on ML2, run the existing scaleRatio diagnostic on it** to learn
   whether its ratio is ~1.0/tight (leave off — dead-zone handles it), ~1.0/noisy (tune the dead-zone),
   or genuinely biased (flip `CompEnabled` on for ML2). `CompEnabled` is `#if MAGIC_LEAP` → false until
   then; the scaleRatio diagnostics still log on ML2.
3. **Thread B — closed on Pixel 9, no action.** Reopen only if the retained camera-config diagnostic
   ever shows a fps split (e.g. 1080p@30 vs 720p@60) on a different ARCore device.
4. The two-reconstruction calibration / held-out re-localization check from the multi-hypothesis
   plan's calibration chapter — still a useful independent map-scale probe, now lower priority since
   the map is exonerated.
