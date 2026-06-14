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
**That question is now answered: it is the device (ARFoundation outdoor VIO), not the map.** The
remaining work is *how to fix it* — two complementary threads (online compensation, and a
source-side camera-config change).

## State

### Decisive second device run — answers "map or device?" (NEW, this session)

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

### Code shipped this session (already committed)

- `scaleRatio` per-measurement diagnostic in `MultiHypothesisFilter.cs` + a `SPEC.md` note.

## Decisions

- **The "is it map or device?" open question is closed: it is the device.** Uniform `scaleRatio` ≈
  0.93 with zero spatial correlation + confirmed-correct 120 mm map baseline ⇒ ARFoundation outdoor
  monocular-inertial VIO scale bias.
- Smoothing/EMA stays demoted for *jitter* — but an EMA **of the scale ratio** is now the core of
  the proposed online fix (Thread A below), a different use entirely.

### Thread A — online VIO-scale compensation (PROPOSED, not built)

- The filter already computes `scaleRatio` per segment. The fix: maintain a **per-session EMA** of
  it and scale VIO motion deltas by **1/ratio** (≈ 1.075 here) when `DriftCorrectionController`
  propagates the published frame between corrections.
- **Must be online (self-estimating), NOT a hardcoded constant.** This is the key reason online >
  constant: it is **device-agnostic**. This phone converges to ~7%; a Magic Leap 2 (better tracker)
  converges to ~1.0 and does nothing; it adapts per device and per environment. A hardcoded ~1.075
  would be this-phone-specific and *wrong* on ML2 and other hardware.
- Status: PROPOSED. Diagnose-first; not implemented.

### Thread B — theorized source-side fix to camera-config selection (PROPOSED, not built)

- Audit of `CameraProvider.cs` config selection (`PrepareCamera`, lines ~156–184): it picks purely
  the **highest resolution** (max `width*height`), **ignoring frame rate**.
- On ARCore the max-res config often runs at a **lower fps**, and ARCore tracking/scale
  observability is **better at higher fps** — so we may be throttling tracking fps for **no benefit**,
  because the **server downsamples every image to a 1024 px shorter side anyway**
  (`canonicalize_intrinsics`).
- **Proposed source fix:** select the config that is just big enough to survive the 1024 px
  downsample but at the **highest available frame rate**.
- Ruled NOT-the-cause but worth recording from the audit:
  - Auto-focus is disabled — **correct** (keeps intrinsics stable; minor far-scene blur risk only).
  - pose↔image timing lag (reads `Camera.main` pose after acquiring the image) → motion-proportional
    *noise*, not a scale bias.
  - The live-localization path correctly uses the raw full-6DoF `Camera.main` pose, **not** the
    level-reference anchored path (that anchored path is disk-recording only).
- **Honest caveat:** outdoor monocular-inertial scale bias is partly **fundamental** (far scenes,
  little parallax). The fps fix would likely **shrink** the 7% but not zero it.

### How A and B relate

- **Complementary, not either/or.** Do the source fix (B) first to shrink the bias, then compensate
  the residual (A). Only compensation (A) covers ML2 and other devices.

## Open questions

- Does the max-res config actually cost fps on the *target ARCore device*? (Decides whether Thread B
  is real for this hardware.) — see immediate next step.
- For Thread A: EMA time constant / warm-up behavior, and how to gate the ratio estimate during
  standstill (`mapDelta` ≈ 0 segments are meaningless and must be filtered).

## Key files

- `packages/unity/Placeframe/Assets/Package/ARFoundation/Runtime/CameraProvider.cs` — `PrepareCamera`
  config selection at lines ~156–184: currently max `width*height`, ignores frame rate (Thread B
  target). Auto-focus disabled here too.
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/MultiHypothesisFilter.cs` — the filter;
  carries the `scaleRatio` diagnostic (map-frame camera position + `mapDelta` + `scaleRatio` per
  measurement). Source of the per-segment ratio that Thread A's EMA would consume.
- `DriftCorrectionController.cs` (alongside) — where Thread A would scale VIO deltas by 1/ratio when
  propagating the published frame between corrections. `RelocalizationConfig.cs` alongside.
- `packages/unity/Placeframe/SPEC.md` — filter behavior + diagnostics intent (line ~112).
- `docker/zed-capture/src/zed/zed.py` — capture-side calibration; baseline at `:366–416` (smells at
  `:412` x-negation, `:365` rectified-vs-raw); `UNIT.METER` at `:328`.
- `docker/reconstructor/src/reconstructor/options_builder.py` / `colmap.py` / `rig.py` — rig-baseline
  fixed through BA, Sim3 scale = 1, `triangulation_minimum_angle`.
- `docker/localizer/src/localize.py` — single-PnP localizer; `canonicalize_intrinsics` 1024 px
  downsample (the reason Thread B's fps-over-resolution argument holds); logs `retrieval_span`.
- `scripts/src/scripts/loki_query.py` — hard-codes `placeframe-loki-1`; against make-it-sing the
  loki container is `makeitsing-loki-1`, so pull logs by execing `wget` inside it directly.
- `.pulsar/memories/relocalization-multi-hypothesis-plan.md`, `relocalization-filter-findings.md`,
  `relocalization-false-lock-diagnosis.md`, `relocalization-filter-rewrite.md` — prior chapters.

## Pending threads

1. **Immediate next step (before either fix):** add a diagnostic log of available camera configs +
   their frame rates in `CameraProvider.cs`, to verify whether max-res actually costs fps on the
   target ARCore device. This decides whether Thread B is worth doing on this hardware.
2. **Thread B (source fix):** select the smallest config that survives the 1024 px server
   downsample at the highest available frame rate; re-run, re-measure `scaleRatio` (expect it to
   shrink toward 1.0 but not reach it).
3. **Thread A (online compensation):** per-session EMA of `scaleRatio`, scale VIO deltas by 1/ratio
   in `DriftCorrectionController` between corrections; device-agnostic, covers the residual + ML2.
4. The two-reconstruction calibration / held-out re-localization check from the multi-hypothesis
   plan's calibration chapter — still a useful independent map-scale probe, now lower priority since
   the map is exonerated.
