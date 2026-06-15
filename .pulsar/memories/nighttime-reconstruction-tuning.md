---
updated: 2026-06-15
---

# Nighttime reconstruction tuning: can we improve night maps of the demo-site courtyard

## Goal

Branch `feature/better-filter`, make-it-sing backend running in this container. We have a fixed
corpus of **5 night reconstructions** of the same outdoor courtyard (`demo-site-night-1` … `-5`,
each a different scan pattern, all captured at night) plus the older daytime baseline `demo-site`.
The five night-bundle tars and `demo-site.tar` sit in the repo root and are importable as full
capture+reconstruction bundles. The question: with a fixed re-runnable corpus, can reconstruction
tuning meaningfully improve night map quality (localization rate and false-lock robustness)?

Night matters because localization works but localizes far less often than daytime, and the user
saw occasional drift-aways (suspected false locks) on night maps. Street lights are the dominant
night feature source — bright and repeatable, but near-perfect aliases (every lamp looks alike),
so night simultaneously raises inlier counts and aliasing risk.

## State

### Baseline diagnosis (the controlling fact)

Reconstruction manifest metrics, day vs the five night scans, established the bottleneck:

| scan | 3D points | % reliable (trk≥3) | mean track len | **vinl_med** (verified-match inliers, median) | reproj p50 |
|---|---|---|---|---|---|
| demo-site DAY | 40506 | 89.4% | 9.18 | **929** | 0.72 |
| night-1..5 | 10k–42k | ~50% | 3.5–3.8 | **135–264** | 0.77–0.83 |

Key findings, all cross-validated against COLMAP text models and the manifest jsonb `metrics` block:

- **Night maps are not geometrically *wrong*, they are *thin*.** Reprojection error is ~identical
  day vs night (0.72 vs 0.77–0.83 px) — the points that triangulate at night are just as accurate.
  SfM produced *less* geometry, not sloppier geometry. Rules out garbage triangulation.
- **The collapse is in track length / observations, not raw point count.** Day points seen in ~9
  images; night ~3.5. Only ~50% of night points clear the ≥3-view reliability bar (vs 89% day).
  night-2 has *more* raw points than day yet only 50% reliable — raw point count is a trap.
- **The decisive discriminator is `vinl_med`** (median verified-match inlier support = "how strongly
  two images actually agree"). Day 929, night 135–264 — a 3.5–7× collapse, falling monotonically
  n1→n5. Same substrate the live localizer draws correspondences from, which is why localization is
  rarer at night. This is the metric every subsequent experiment is judged on.
- **Viewpoint diversity is *higher* at night** (0.91–0.97 vs 0.81 day) — the varied scan patterns
  worked; coverage is good. The limit is per-frame feature scarcity (photons/texture), not scan
  path. Rescanning with a different pattern will not fix it.
- Extraction is **not** keypoint-starved: `features.h5` is ~the same size day vs night (~2500
  ALIKED keypoints/image both). The night keypoints exist but are lower-repeatability — they don't
  match across views, so fewer survive two-view verification and triangulate into long tracks.

Pipeline facts: extractor is **ALIKED** (capped 2500 kp/image), retrieval is **DIR** cosine,
matcher LightGlue. Reconstructions are re-runnable via `POST /reconstructions`
(`capture_session_id` + `ReconstructionOptions`); the queued row is leased by the running CUDA
reconstructor. The capture sessions are present in this backend's DB so all five are re-runnable.

### Image-enhancement experiment — RUN, CONCLUSIVELY NEGATIVE, code now expunged

We built a default-off `image_enhancement` reconstruction option (CLAHE, then `denoise_clahe`),
A/B-ran both variants across all five night captures, and **falsified enhancement properly**:

- **Plain CLAHE** (L-channel only, clipLimit 2.0, 8×8 tiles): match *rate* and *count* up in 4/5,
  but **`vinl_med` down in 5/5 (−6% to −21%)** and track length down in 4/5. CLAHE trades match
  quality for quantity — it manufactures extra low-repeatability correspondences by amplifying
  sensor noise into weak keypoints. Wrong trade for both goals (the extra weak matches are aliasing
  fuel, making false-lock robustness *worse*).
- **denoise → CLAHE** (non-local-means denoise on luminance before the contrast lift): beat plain
  CLAHE on `vinl_med` in 4/5 and improved track length in 4/5 — **the noise hypothesis was correct**,
  denoise stopped CLAHE manufacturing noise-keypoints (point counts dropped as junk got cleaned out).
  **But `vinl_med` was still below baseline in all five (−10% to −13%).** denoise+clahe is the
  *least-bad* enhancement, not a win.
- **Verdict: the raw, unprocessed night frames already produce stronger matches than any
  enhancement we apply.** Two variants × five captures × consistent direction, with the failure
  *mechanism* confirmed. This is the cleanest possible "no." Image enhancement is **dead for this
  corpus** and effectively ruled out.

Per the user's explicit instruction, **all CLAHE/denoise code was expunged completely** (not left
in default-off) immediately after this memory was captured. As of writing, the expunge is verified:
no `image_enhance.py`, no `image_enhancement`/`ImageEnhancement`/`clahe`/`denoise` in
`core/reconstruction_options.py`, no `opencv-python` in the reconstructor `pyproject.toml`, and the
regenerated clients no longer carry the field (stale `build/lib/` copies are git-ignored, not source).
The expunge touched: `packages/python/core/src/core/reconstruction_options.py` (the option +
`ImageEnhancement` literal), `docker/reconstructor/src/reconstructor/image_enhance.py` (deleted),
its wiring in `run_reconstruction.py` and `options_builder.py`, the `opencv-python` dep, regenerated
api-client + lease-server-client, and the `--image-enhancement` flag on the reconstruction `create`
script command. Note: a `create` command was added to the reconstruction run-script for enqueuing
tuning variants — that command is the reusable A/B tool and is wanted for Tier-1 below; only the
enhancement flag on it was part of the expunge.

## Decisions

- **Judge every tuning experiment on `vinl_med`** (median verified-match inlier support), with track
  length / reliable-point count as the supporting signals. "More matches but weaker" is a *loss*,
  not a win — it is aliasing fuel and worsens false-lock robustness. This is the lesson the CLAHE
  experiment paid for.
- **Image enhancement is ruled out** for this corpus. Do not revisit CLAHE/denoise without new
  evidence.
- **Expunge, don't shelve.** The user chose full removal over keeping the option default-off.
- **Tier 1 ran and WON — adopted.** `keyframe_min_distance_m` 1.0 → 0.5 lifted `vinl_med` on **5/5**
  night captures (+10% to +28%, mean ~+18%), track-length mean +18%, point count ~doubled (+69% to
  +113%), at a trivial reproj cost (every variant rose +0.03–0.06 px, all still sub-pixel). The two
  *thinnest* baselines (night-4 162→207, night-5 134.5→160) gained the most — the lever helps the
  maps that needed it most. The default was changed 1.0 → 0.5 in
  `core/reconstruction_options.py` (commit `8ddf0925`) + codegen (`6b35be50`).
- **`sequential_window_m` 3.0 → 5.0 is inert-to-harmful — NOT adopted, left at 3.0.** The Phase-A
  decomposition (night-3 2×2: baseline / kfd-only / window-only / both) showed kfd is the *entire*
  effect (+8.7% `vinl_med` alone) while the window alone *dropped* `vinl_med` −2% and, stacked on
  kfd, added only +1.3% (noise) **and produced the worst reproj of the four cells** (0.851 → 0.887).
  Bonus reason to drop it: fewer pairs = less aliasing exposure.
- **Don't push kfd below 0.5 — near frame-count saturation.** At 0.5 we already register **76–86% of
  every raw frame** (raw frame counts: n1 253 / n2 402 / n3 135 / n4 238 / n5 317; registered =
  mapped-images ÷ 2 since stereo). kfd 0.25 buys at most ~15–24% more frames, all near-stationary
  duplicates the 3° triangulation gate culls. The 1.0→0.5 win was a one-time doubling of frame
  utilization (~40% → ~80%); there is no second doubling available.
- **Verdict scope:** all of the above is validated on **map richness only** (`vinl_med`, track
  length, points) — NOT on localization / false-lock robustness. The 5×5 cross-localization +
  cycle-consistency test is still the real gate before calling kfd=0.5 a *localization* win. Daytime
  impact is also untested (the day regression was skipped — `demo-site` had no capture tar), and the
  default change is global (no day/night flag in the pipeline; ~2× keyframes ≈ ~2× reconstruct compute).
- **Capture-side tuning is now on the table** (it was previously deemed off-limits). The night
  bottleneck is gain-noise from photon starvation, which is a *capture* problem; the device-side
  camera knobs (ZED X / ML2 / ARFoundation) are captured in
  `.pulsar/memories/night-camera-tuning-knobs.md`. Capture changes can't be A/B'd on the existing
  corpus — they need new scans.

## Open questions

- **Does kfd=0.5 hold up on the *localization* axis** (success rate, false-lock robustness), not just
  map richness? Answered "yes" on richness 5/5; the 5×5 cross-localization is the localization gate.
- Does kfd=0.5 help or hurt **daytime**? Untested (no daytime capture tar present).
- For the 5×5 cross-localization / cycle-consistency "are these the same place / which map is broken"
  experiment: can the localizer be aimed at an arbitrary map in a batch call? (Map-selection wiring
  in the localizer/API was never confirmed.) All five maps have **identity georeg**, so every check
  is *relative* (map-to-map), never map-to-Earth — cross-localization (levels 1–2) and
  cycle-consistency (level 3, the broken-map detector) need no georeg and are fully intact; the only
  thing off the table is "is the map georegistered correctly," which is N/A for identity maps.

## Pending threads

- **Tier 1 is DONE** (kfd=0.5 adopted, window rejected — see Decisions). The reusable A/B tool now
  exists: `uv run reconstruction create <capture-name-or-uuid> --options-json '{...}'` (commit
  `181d2036`) — enqueues a re-reconstruction with arbitrary `ReconstructionOptions` overrides,
  validated through the client model; the running CUDA reconstructor leases the queued row. GPU stays
  clear by keeping `localizer-cuda` stopped (localizer + reconstructor co-resident OOMs the 8 GiB GPU).
- **Density-curve trace (proposed, NOT run):** kfd 1.5 + 2.0 on night-2 (densest capture) to map the
  density→quality curve. We know 1.0→0.5 is still climbing steeply (+18%); tracing the sparser end
  tells us whether the curve is plateauing — i.e. whether *denser capture* (new scans) would keep
  paying or just saturate. This informs the capture-side decision (see camera memory).
- **5×5 cross-localization validation** of kfd=0.5 (the localization gate) — see below.
- The remaining reconstruction tuning menu, re-ranked by the CLAHE lesson + the kfd result, with
  calibrated odds (≥10% move in localization-relevant metrics; n=5 corpus, treat as guesses). Note
  the reconstruction-side vein is now **largely mined out** — kfd was the big win and is saturated,
  window is dead; further upside likely comes from *capture-side* changes, not these knobs:
  - **Tier 2 — looser thresholds** (`two_view_min_num_inliers` 30→20, `triangulation_minimum_angle`
    lower, retrieval loosening `retrieval_min_score`↓ / `retrieval_neighbors` 20→30): **~25% / ~25%
    / ~50% — weighted toward harm.** The CLAHE run was a natural experiment in "more, weaker matches"
    and it read as aliasing fuel; `two_view_min_num_inliers` was raised *to* 30 specifically to
    reject repetitive-structure false clusters, and night maximizes repetitive structure (street
    lights). Contrarian sub-lever: `triangulation_minimum_angle` *raised* (not lowered) → fewer,
    cleaner points → could *reduce* false locks at a density cost (flips the sign).
  - **Tier 3 — more keypoints** (`max_keypoints_per_image` 2500 → 4096/8192): **~10% / ~72% / ~18%
    — most likely a no-op.** `features.h5` evidence says extraction isn't the binding constraint.
    Cheapest to falsify, lowest expected payoff.
- **The 5×5 cross-localization matrix** (the bigger session-two goal): localize each capture's query
  frames against each of the 5 maps → grid of (success rate, inlier support, recovered pose). Answers
  "are these all the same place" via three converging relative signals — cross-localization success,
  **cycle consistency** (`T(i→j)∘T(j→k)∘T(k→i) ≈ identity`, the strongest same-place evidence and
  the **broken-map detector**, since a night SfM can internally alias / fold two lamp-lit regions
  together and only cycle-consistency catches that), and relative-geometry agreement. Blocked on the
  map-selection-wiring open question above.

## Key files

- `.pulsar/memories/relocalization-scale-mismatch-diagnosis.md` — the parallel/prior initiative on
  this branch (VIO-scale compensation, hypothesis grading, GNSS diagnostic). Read for full branch
  context.
- `packages/python/core/src/core/reconstruction_options.py` — `ReconstructionOptions` (the tuning
  knobs: `keyframe_min_distance_m`, `sequential_window_m`, `two_view_min_num_inliers`,
  `triangulation_minimum_angle`, `max_keypoints_per_image`, retrieval params).
- `docker/reconstructor/src/reconstructor/run_reconstruction.py` — extraction loop;
  `canonicalize_image` from `core.image_preprocess` is the per-image preprocessing point (was the
  enhancement insertion site).
- `docker/reconstructor/src/reconstructor/options_builder.py` — `OptionsBuilder` exposing options to
  the COLMAP run.
- `docker/reconstructor/SPEC.md` — reconstructor design rationale (e.g. why
  `two_view_min_num_inliers` was raised to reject false clusters).
- The reconstruction run-script (`uv run reconstruction`) — `list` / `export` / `import` / `create`;
  `create` enqueues a re-reconstruction with options and is the A/B tool for the tiers above.
  Capture+reconstruction bundle export/import (commit `37e71b06`) keeps them DB-connected.
