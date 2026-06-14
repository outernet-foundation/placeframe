---
updated: 2026-06-14
---

# Relocalization instability is a ~10% scale mismatch; the map's global scale is confirmed correct, so the cause is device VIO scale or local map warp

## Goal

A `feature/better-filter` field run (make-it-sing backend, demo-site outdoor courtyard scan)
still showed content that is "off when I shift perspective, then re-aligns" as the user walks.
Earlier in the session the decisive log analysis showed the felt instability is a slow,
**position-locked** swing (not fast jitter, not VIO drift) consistent with a **~10% metric-scale
mismatch** between map and device. The follow-up question — and the current state of this memory —
is *which side* the 10% is on. A reconstructor + ZED-capture code review plus a direct check of
the demo-site map's own scale answered half of it: **the map's global metric scale is correct**,
which moves the remaining cause to either the device's ARFoundation scale or **local map warp**
(non-uniform scale across the courtyard). No client-side smoothing fixes either.

## State

### Log decomposition (from earlier in the session — unchanged)

- Run: demo-site courtyard scan, current HEAD of `feature/better-filter` (single PnP, with
  per-query VIO/tracking-state + per-measurement camera-geodetic logging). Bank ran N=1 the
  whole session (no aliasing); the anti-aliasing machinery never fired.
- Alignment translation decomposition (should be constant if VIO+map were perfect):
  - measTx: slow swing range 1.66 m, fast per-step jitter std 0.078 m
  - measTy: slow swing range 0.72 m, fast per-step jitter std 0.088 m
  - measTz: slow swing range **2.03 m**, fast per-step jitter std 0.120 m
  - Fast jitter is tiny (~0.1 m); instability is the 0.7–2.0 m **slow** swing.
- Position-dependence: corr(measTz, camZ) = **+0.80**, corr(measTz, camX) = +0.35,
  corr(measTz, camY) = -0.06. The alignment error is locked to position in the map.
- ARFoundation vs map motion: per-step ratio vioDelta/‖ΔcamPos‖ ≈ 0.85–0.90 (median 0.90):
  ARFoundation reports moving ~10–15% *less* than the map says. (The slope/r regression was junk —
  poisoned by a 26 m bad-zone outlier and imperfect 83-vs-69 line pairing; median is the robust
  signal. The new inline diagnostic below replaces that fragile post-hoc pairing.)
- A ~10% scale error integrated over the ~23 m camZ traverse = ~2.3 m ≈ the observed 2.03 m measTz
  swing, and explains the position correlation. ARFoundation tracking was solid (Tracking 69/69,
  ~0.1 m per-step jitter, not random drift). Smoothing/EMA is demoted — it only touches the fast
  jitter, never the slow swing.

### Reconstruction + capture code review and the decisive baseline check (NEW)

- **Scale architecture is correct on both sides.** Metric scale rides entirely on the ZED stereo
  rig baseline: the capture writes the factory `stereo_transform` translation as `camera1`'s
  translation in the manifest (`docker/zed-capture/src/zed/zed.py:366–416`); the reconstructor
  packs it into a COLMAP `RigConfig` and **holds it fixed through all incremental SfM and global
  BA** (`constant_rigs`, `ba_refine_sensor_from_rig=False`, `docker/reconstructor/src/reconstructor/options_builder.py:69–81`;
  the rig-refining final BA pass is commented out in `colmap.py:267`). No RGBD/depth ingestion;
  the post-SfM `Sim3d` only rotates (gravity) + translates (origin), **scale component = 1.0**
  (`colmap.py:282–290`); position priors are off for stereo. `coordinate_units = UNIT.METER` is
  set explicitly (`zed.py:328`) — no mm/cm unit bug (that would be 1000×/100×, not 10%).
- **The demo-site map's actual scale is correct.** Extracted the reconstruction's own COLMAP model
  from `demo-site.tar` (`sfm_model/rigs.txt`, `cameras.txt`):
  - baseline used by COLMAP = **−0.11997 m = 119.97 mm**, vs ZED X factory **120 mm** → 0.02% off,
    dead-on.
  - both cameras' BA-refined focal lengths agree to 0.01% (`fx≈689.9/691.6`, PINHOLE 1820×1024),
    so BA did not absorb scale into focal length.
  - This **exonerates the reconstruction/capture pipeline for a global 10% scale error on this map.**
- **Latent code smells found but NOT the cause here** (magnitude came out right): the unexplained
  `x=-stereo_transform_translation[0]` negation TODO (`zed.py:412`) and the rectified-vs-raw
  calibration choice (`zed.py:365`). Worth resolving but they did not corrupt this map.
- **Capture-technique degeneracy that CAN warp scale despite a perfect baseline:** the 12 cm
  baseline directly triangulates almost nothing in a courtyard. Parallax angle ≈ baseline/depth,
  and with `triangulation_minimum_angle = 3.0°` stereo only metrically constrains structure within
  **~2.3 m** of the camera (5 m→1.4°, 10 m→0.7°, 15 m→0.46°). Everything farther gets its scale
  from monocular cross-frame chains, only transitively tied to the near-field stereo anchors. The
  rig still pins each frame's two cameras 12 cm apart (so global scale stays anchored — hence the
  exact baseline), but far-field *local* scale is precision-soft and can warp across the trajectory.
  Corroborating: only **114 stereo-verified matches of 2773 total** (one stereo pair per frame).

## Decisions

- **The earlier "the real fix is the map's metric scale" conclusion is corrected.** The map's
  *global* metric scale is verifiably correct (120 mm baseline). The ~10% therefore lives in one of:
  1. **Device ARFoundation outdoor VIO scale bias** — leading candidate, because the measured
     ratio was *consistent* (~0.90) rather than region-varying, and a 5–15% monocular-inertial VIO
     scale bias in a large outdoor space is well within ARFoundation's normal envelope. This is a
     platform property, **not fixable in the reconstruction**.
  2. **Local map warp (non-uniform scale)** — mechanism is the far-field triangulation weakness
     above; fixable with better capture technique (slower walk, more loop closures, more near-field
     parallax) or reconstruction changes.
- Smoothing/EMA stays demoted: it attacks only the ~0.1 m fast jitter, never the slow swing.

## Open questions

- **Is the residual ~10% constant across the map (→ device VIO scale) or region-varying (→ map
  warp)?** This is the single discriminating question the new diagnostic (below) is built to answer.
- If VIO scale bias: is there a worthwhile mitigation (tighter correction deadband so re-anchoring
  happens more often), or is it just an accepted platform limit?
- If map warp: do the latent capture smells (`zed.py:412` x-negation, rectified-vs-raw) or capture
  technique (walk speed, loop closures, keyframe density) move the needle on a re-scan?

## Key files

- `.pulsar/memories/relocalization-multi-hypothesis-plan.md` — overarching architecture plan; its
  calibration chapter predicted exactly this map-quality/scale problem and motivates a
  two-reconstruction held-out re-localization check.
- `.pulsar/memories/relocalization-filter-findings.md`, `relocalization-false-lock-diagnosis.md`,
  `relocalization-filter-rewrite.md` — prior chapters of the initiative.
- `docker/zed-capture/src/zed/zed.py` — capture-side calibration export; baseline at `:366–416`
  (smells at `:412`, `:365`); `UNIT.METER` at `:328`.
- `docker/reconstructor/src/reconstructor/options_builder.py` — `constant_rigs`,
  `ba_refine_sensor_from_rig=False`, `ba_refine_focal_length=True`, `triangulation_minimum_angle`.
- `docker/reconstructor/src/reconstructor/colmap.py` — incremental_mapping, baseline-fixed BA,
  Sim3 (scale=1), commented-out final BA at `:267`.
- `docker/reconstructor/src/reconstructor/rig.py` — manifest baseline → COLMAP rig.
- `docker/localizer/src/localize.py` — single-PnP localizer; logs `retrieval_span`.
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/MultiHypothesisFilter.cs` — the filter;
  carries the new scale-ratio diagnostic (map-frame camera position + mapDelta + scaleRatio per
  measurement). `DriftCorrectionController.cs`, `RelocalizationConfig.cs` alongside.
- `packages/unity/Placeframe/SPEC.md` — filter behavior + diagnostics intent (line ~112).
- `scripts/src/scripts/loki_query.py` — hard-codes `placeframe-loki-1`; against the make-it-sing
  stack the loki container is `makeitsing-loki-1`, so pull logs by execing `wget` inside it directly.

## Pending threads

1. **Run the discrimination diagnostic.** The filter now logs, per accepted/spawned measurement,
   the camera position in the **map frame** (`mapX/mapY/mapZ`), the map-motion delta since that
   hypothesis was last supported (`mapDelta`), and `scaleRatio = vioDelta / mapDelta`. After the
   next walk-around run, bin `scaleRatio` by map region:
   - **scaleRatio ≈ constant (~0.90) across all regions → device ARFoundation VIO scale bias**
     (map global scale is already confirmed correct, so a uniform ratio ≠ 1 is the device side).
   - **scaleRatio varies systematically with `mapX/Y/Z` → local map warp.**
   Filter rows where `mapDelta` is tiny (standstill) — the ratio is only meaningful with motion.
2. If warp: a near-field, slow, loop-rich partial re-scan and re-test (swing shrinks → capture
   technique; swing persists → device VIO).
3. The two-reconstruction calibration / held-out re-localization check from the multi-hypothesis
   plan's calibration chapter — now well-motivated as an independent map-scale/warp probe.
