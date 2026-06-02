# Aliasing-defense sweep on `4bd303f1`

Single-capture parameter sweep across three pair-filter axes, with replicates
per cell to measure noise. Spatial pair generation disabled throughout —
leaning entirely on sequential + covisibility-filtered retrieval as the
loop-closure infrastructure.

## Capture under test

- Capture session: `4bd303f1-d6c4-4867-8e35-f788c810ce26`
- Why this one: largest historical aliasing degeneracy across the three
  available captures.

## Fixed parameters across all 120 runs

- `spatial_neighbors = 0` — spatial pair generation off
- `sequential_window = 20`
- `keyframe_min_distance_m = 0.2`
- `retrieval_neighbors = 20`
- `retrieval_min_score = 0.35`
- `retrieval_min_distance_m = 1.0`
- `ransac_max_error = 2.0`
- baseline `ransac_min_inlier_ratio = 0.25`, `two_view_min_num_inliers = 30`
  (applies to sequential/intra-frame pairs; only the retrieval-source override
  is swept)
- no `deterministic_seed` — runs are stochastic by design, replicates measure
  the noise floor

## Sweep axes

**Axis 1: retrieval verification strictness `(retrieval_min_inlier_ratio,
retrieval_min_num_inliers)`** — coupled, treated as one strictness lever:

| label | ratio | count |
|-------|-------|-------|
| L1 | 0.25 | 30 |
| L2 | 0.35 | 40 |
| L3 | 0.45 | 60 |
| L4 | 0.55 | 80 |

**Axis 2: covisibility support `retrieval_covisibility_min_support` (K)** —
graph-level filter strength:

| label | K |
|-------|---|
| K0 | 0 (filter off) |
| K2 | 2 |
| K3 | 3 |
| K5 | 5 |

**Axis 3: covisibility window `retrieval_covisibility_window` (W)** —
half-width of the temporal neighborhood searched for supporters:

| label | W |
|-------|---|
| W2 | 2 |
| W3 | 3 |
| W5 | 5 |

W=1 deliberately skipped — with distance-based keyframes at 0.2m, ±1 keyframe
is ±0.2m of trajectory motion, which is below VIO-drift-magnitude alignment
fuzz so real loops wouldn't reliably find a supporter that close.

## K=0 dedup

When K=0 the covisibility filter is bypassed entirely, so the W setting has
no effect. Rather than run the same identical config three times under
different W labels, we run K=0 cells **once per ratio** (not once per ratio
per W). This saves 24 redundant runs.

## Matrix (4 ratio × [1 K0 + 3 K{2,3,5} × 3 W] × 3 replicates = 120 runs)

| | K0 (W ignored) | K2·W2 | K2·W3 | K2·W5 | K3·W2 | K3·W3 | K3·W5 | K5·W2 | K5·W3 | K5·W5 |
|--|--|--|--|--|--|--|--|--|--|--|
| **L1** | 3× | 3× | 3× | 3× | 3× | 3× | 3× | 3× | 3× | 3× |
| **L2** | 3× | 3× | 3× | 3× | 3× | 3× | 3× | 3× | 3× | 3× |
| **L3** | 3× | 3× | 3× | 3× | 3× | 3× | 3× | 3× | 3× | 3× |
| **L4** | 3× | 3× | 3× | 3× | 3× | 3× | 3× | 3× | 3× | 3× |

40 unique configs × 3 replicates = 120 reconstructions.

## Metrics per reconstruction

Each cell gets four numbers, two per failure mode:

| metric | direction of badness | detects |
|--------|---------------------|---------|
| `max_speed` (m/s) | high = bad | bad pairs (local tears) |
| `bad_pair_count` | high = bad | how many local tears |
| `long_range_track_count` | **low = bad** | missing loop closures |
| `p95_track_extent` | **low = bad** | scale of loop closures |

Definitions:

- **`max_speed`, `bad_pair_count`** — from `displacement-check` script. A
  "bad pair" is a consecutive-keyframe distance exceeding 2.5 m/s in recon
  space.
- **`long_range_track_count`** — for each 3D point in `points3D.txt`, the
  track is the set of keyframes that observed it. Compute the temporal
  extent as `max(temporal_index) - min(temporal_index)` across the track,
  where `temporal_index` is the keyframe's position in the sorted-by-
  timestamp ordering. Count tracks with extent > 2 × `sequential_window`
  (= 40). These are tracks that cannot exist from sequential matching alone;
  their existence is evidence of loop closure pairs landing in the map.
- **`p95_track_extent`** — 95th percentile of the temporal extent
  distribution. Higher = longer / more loop closures.

**Reading the metric pair:**

- low `max_speed` + high `long_range_track_count` → good map: loops fired,
  no aliasing damage.
- low `max_speed` + **low** `long_range_track_count` → over-filtered: no
  bad pairs admitted but no good loops either; trajectory drifts unconstrained.
- high `max_speed` + any `long_range_track_count` → degenerate: bad pairs
  pulling the trajectory apart, regardless of whether good loops also fired.

## Why `prior_drift_residual_rms_m` is NOT the loop-closure metric

The reconstructor already computes a Umeyama best-fit residual between recon
frame centers and VIO `frames.csv` priors, and stores it on the reconstruction
metrics. It's tempting to use it as the "did we close loops" signal — a map
that closed correctly should match VIO closely.

The problem: on the captures we're testing, VIO itself has substantial drift
(the ZED capture bug). A *correct* reconstruction that closes loops correctly
would diverge from drifted VIO, producing a *high* residual. A *broken*
reconstruction that mirrors VIO's drift step-for-step might have a *low*
residual. The metric is anti-correlated with truth when the reference is
itself wrong.

We get tripped up by this every time we try to use it. The track-extent
metric above is VIO-independent — it reads geometric self-consistency
straight from the reconstructed map.

## Compute budget

- ~4 minutes per reconstruction (sequential lease)
- 120 runs ≈ **8 hours total**
- Driver script queues all 120 up front; reconstructor processes them in
  arrival order via the lease.

## Pipeline (work for the next session to execute)

1. **Add track-extent metric.** Extend `scripts/src/scripts/displacement_check.py`
   (or add a sibling utility) to parse `points3D.txt`, compute per-track
   temporal extent, and report `long_range_track_count` and `p95_track_extent`
   alongside the existing displacement stats. Re-smoke against a known good
   reconstruction (e.g. `8c329882`) to confirm we get nonzero long-range
   tracks on a clean map.
2. **Update the driver script** at `/tmp/recon_audit/sweep_driver.py`:
   - Generate the 120-cell list with K=0 dedup applied
   - Submit all 120 with appropriate `ReconstructionOptions` overrides
   - Wait for terminal state on all
   - Pull artifacts, run displacement-check + track-extent for each
   - Write `/tmp/recon_audit/sweep/results.csv` with columns:
     `reconstruction_id, ratio_label, k_label, w_label, replicate, ratio,
     count, k, w, status, pair_count, max_speed, max_distance, p95_speed,
     median_speed, bad_pair_count, long_range_track_count, p95_track_extent`
   - Print per-cell summary (median of each metric across replicates, plus
     spread) at the end
3. **Launch in background.** The reconstructor processes runs serially via
   lease; queueing 120 at once is safe.

## What "winning" looks like

A cell — or contiguous region of cells — where:
- median `max_speed` ≤ 2.5 m/s (no local tears)
- median `bad_pair_count` = 0
- median `long_range_track_count` is in the same order of magnitude as a
  known-clean baseline (the pre-(a) `8c329882` run on `17af01a0`, which
  we'd want to spot-check to establish what "healthy" looks like)
- spread within the cell across replicates is small relative to differences
  to neighboring cells (so we trust the read)

If no such cell exists, the conclusion is that the filter combination space
we're searching cannot defeat this scene's aliasing — and the next move is
either to look at other knobs (W=1, K up further, different retrieval
descriptors) or to accept that this capture is inherently broken and move
to fixing the input (ZED VIO bug, retrieval model).
