---
updated: 2026-06-14
---

# Relocalization instability is a ~10% map↔device scale mismatch, not VIO drift or jitter

## Goal

A `feature/better-filter` field run (make-it-sing backend, demo-site outdoor courtyard scan)
still showed content that is "off when I shift perspective, then re-aligns" as the user walks.
The session asked: is this fast jitter (fixable by smoothing the alignment with an EMA), VIO
drift (a moving target that caps how hard you can smooth), or a map problem? The decisive log
analysis answered it: the felt instability is a slow, **position-locked** swing caused by a
**~10% metric-scale mismatch between the reconstruction map and the device's ARFoundation
frame** — not jitter, not VIO drift. No client-side filter can fix this; it is baked into the
map↔device scale relationship.

## State

- Run analyzed: demo-site courtyard scan against the make-it-sing stack (current HEAD of
  `feature/better-filter`, which had reverted per-cluster solving back to single PnP and added
  per-query VIO/tracking-state + per-measurement camera-geodetic logging).
- Logs pulled from `makeitsing-loki-1` (NOT placeframe-loki — see Decisions). Client service
  name `capture-tool`; ~69 VIO lines, ~63 match lines, ~83 server camPos lines.
- **Decomposition of alignment translation (should be constant if VIO+map were perfect):**
  - measTx: slow swing range 1.66 m, fast per-step jitter std 0.078 m
  - measTy: slow swing range 0.72 m, fast per-step jitter std 0.088 m
  - measTz: slow swing range **2.03 m**, fast per-step jitter std 0.120 m
  - Fast jitter is tiny (~0.1 m). Instability is dominated by the 0.7–2.0 m **slow** swing.
- **Position-dependence (warp signature):** corr(measTz, camZ) = **+0.80**, corr(measTz, camX)
  = +0.35, corr(measTz, camY) = -0.06. The alignment error is locked to position in the map.
- **ARFoundation vs map motion:** per-step ratio vioDelta/‖ΔcamPos‖ ≈ 0.85–0.90 (median 0.90):
  ARFoundation reports moving ~10–15% *less* than the map says. (slope=0.024, r=0.28 are junk —
  poisoned by a 26 m bad-zone outlier and imperfect 83-vs-69 line pairing; the **median ratio**
  is the robust signal.)
- **Composition:** a ~10% scale error integrated over the ~23 m camZ traverse = ~2.3 m ≈ the
  observed 2.03 m measTz swing, and explains why it correlates with position. The alignment
  pins the camera at its VIO position each frame, so the registration error gets pushed out to
  far-field content and changes with viewpoint — exactly the "off when I shift perspective" feel.
- **ARFoundation tracking is solid here:** ~0.1 m per-step jitter (not random drift), tracking
  state Tracking 69/69. Ruled out as the cause.
- **Ruled out: smoothing/EMA as the fix.** A low-pass attacks only the fast jitter (already
  ~0.1 m → ~0.05 m) and is transparent to a slow swing by definition. It cannot touch the
  dominant slow swing. Demoted to nice-to-have polish, not the fix.

## Decisions

- The user's intuition was confirmed: ARFoundation alone keeps content glued in a bounded
  courtyard with revisits (modern ARFoundation is VI-SLAM with local BA + loop closure, not
  open-ended dead-reckoning VIO). Between corrections, Placeframe content already rides
  ARFoundation's session frame, so the shifting is the corrections re-anchoring to a varying
  localizer estimate — not VIO drift bleeding through.
- Therefore the real fix is **map↔device metric-scale consistency**, most likely the map's
  metric scale. A reconstruction ~10% too large produces exactly this signature. An
  ARFoundation 10% scale error outdoors is possible but less likely than a reconstruction
  scale problem.
- The smoothing/EMA debate is closed: not the lever. Reconstruction scale is the lever.

## Open questions

- Is the ~10% mismatch on the **map** side (reconstruction metric scale) or the **device**
  side (ARFoundation outdoor scale error)? Evidence favors the map.
- Does the reconstructor actually apply **stereo baseline scale** and **global bundle
  adjustment**? (Long-standing open question; a missing/incorrect metric scale step would
  produce this exactly.)

## Key files

- `.pulsar/memories/relocalization-multi-hypothesis-plan.md` — the overarching architecture
  plan (server collapses ambiguity; client multi-hypothesis filter-bank → calibration →
  Gaussian-sum endpoint). The calibration chapter predicted this map-quality problem.
- `.pulsar/memories/relocalization-filter-findings.md` — prior field-test findings/tuning.
- `.pulsar/memories/relocalization-false-lock-diagnosis.md` — earlier (pre-revert) diagnosis;
  note current HEAD reverted per-cluster solving and added VIO/tracking-state logging since.
- `.pulsar/memories/relocalization-filter-rewrite.md` — the complementary-filter chapter
  (06-12) preceding the multi-hypothesis rewrite.
- `docker/reconstructor/` — read to check whether stereo baseline scale and global BA are
  actually applied (suspect #1 for the scale mismatch).
- `docker/localizer/src/localize.py` — current single-PnP localizer; logs `retrieval_span`.
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/MultiHypothesisFilter.cs`,
  `DriftCorrectionController.cs`, `RelocalizationConfig.cs` — the client filter/control law
  (RelocalizationFilter.cs was deleted and replaced by these).
- `scripts/src/scripts/loki_query.py` — hard-codes `placeframe-loki-1`; unusable as-is against
  the make-it-sing stack (container is `makeitsing-loki-1`). Logs were pulled by execing
  `wget` inside the loki container directly.

## Pending threads

For a `/diagnose` pickup, investigate in this order:

1. **Pin the scale number precisely.** Measure vioDelta vs ‖ΔcamPos‖ over one clean straight
   walking segment of the existing logs, excluding the 26 m bad-zone outlier, to get a tight
   scale figure instead of the noisy ~0.85–0.90 median.
2. **Read `docker/reconstructor/`** to verify whether stereo baseline scale and global bundle
   adjustment are actually applied — the most likely root cause if the map is ~10% too large.
3. The **two-reconstruction calibration / held-out re-localization** check (from the
   multi-hypothesis plan's calibration chapter) is now well-motivated — it would catch a map
   scale error directly.
