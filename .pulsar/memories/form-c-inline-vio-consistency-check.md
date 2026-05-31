---
updated: 2026-05-31
---

# Form C: inline VIO-consistency check during COLMAP incremental mapping

## Goal

Implement "Form C" — an inline VIO-consistency rejector that fires *during*
COLMAP's incremental registration loop, deregisters any newly-registered
frame whose pose disagrees with its local VIO neighborhood, and continues
the mapper with that frame skip-listed. This is the architectural reactive
defense against retrieval-pair aliasing failures that survive (or bypass)
all preventive filtering — the failure shape described in
`.pulsar/memories/reconstruction-aliasing-failure-modes.md`.

Form C is being implemented *now* (this initiative). Form A (offline
diagnostic) and the preventive drift-aware retrieval filter remain pending
as separate threads. The build-order debate has been settled: user explicitly
chose to do Form C, not "A first then maybe C." Do not re-litigate.

## Why Form C and not Form A/B

User-decision context as of 2026-05-31:

- **Form A** alone only *diagnoses* a broken map — it produces a
  flagged-frame list but does not change the reconstruction. User does not
  want a diagnostic-only mechanism as the primary fix.
- **Form B** (two-pass: reconstruct → run Form A → filter flagged-frames'
  retrieval pairs → re-reconstruct) was rejected because it pays ~1.5–2×
  wall-clock on *every* capture even when the first pass was clean. User
  doesn't love the wasteful tax.
- **Form C** runs the check inline so the bad pose never enters BA. Roughly
  ~1.5–1.7× *faster* than Form B (one reconstruction pass, with a small
  per-registration check overhead). User picked it explicitly.
- Preventive drift-aware retrieval filter remains pinned as a separate
  pending thread — complementary to Form C, not redundant. Form C is the
  correctness mechanism; the preventive filter is the efficiency
  mechanism. Order: ship Form C first, add the preventive filter after.

## The mechanism (what's being built)

Same VIO-consistency body as the Form A spec in
`reconstruction-aliasing-failure-modes.md`:

For each newly registered image, fit a local Umeyama (Sim3) transform over
its N≈10 nearest-in-time VIO neighbors that have *already been registered*
in the recon, predict the new image's recon position from its VIO position
via that local transform, and compare against the position COLMAP just
assigned. If disagreement exceeds a threshold (~0.5–1.0 m, calibrated
against a known-clean recon's 99th percentile), the registration is
rejected: deregister the frame, add its image-id(s) to a Python-side
skip-list, continue the loop. The skip-list is needed because
`register_next_image() → True` followed by manual `deregister_frame()`
does *not* increment COLMAP's internal `reg_trials` counter — without
the skip-list, `find_next_images()` happily re-suggests the same image.

This works *despite* secular VIO drift because the local Umeyama absorbs
whatever drift exists at that point in the trajectory; the prediction is
a high-confidence claim about where the frame should be *relative to its
local context*, not absolute position. Over a ~5 s / N=10 keyframe window,
drift is millimeter-scale even on the buggy capture.

## Where the code lives (settled architecture)

User asked whether Form C is entirely inside `colmap.py` or touches
elsewhere. Decision after answering:

- **New file `docker/reconstructor/src/reconstructor/incremental_loop.py`.**
  Contains the forked `reconstruct_sub_model` / `reconstruct` /
  `main_incremental_mapper` adapted from
  [`pycolmap/python/examples/custom_incremental_pipeline.py`](https://github.com/colmap/colmap/blob/main/python/examples/custom_incremental_pipeline.py)
  (~350 lines upstream). The VIO-check insertion point is between a
  successful `register_next_image()` and the subsequent `triangulate_image()`
  + local BA call (see the exact location quoted in `response.md`).
- **VIO consistency helper.** Either a sibling file
  `docker/reconstructor/src/reconstructor/vio_consistency.py` or folded
  into `incremental_loop.py`. Same body Form A would use. Pure Python.
- **`docker/reconstructor/src/reconstructor/colmap.py`** — modified at the
  single `incremental_mapping(...)` call site (around line 175 — verify
  with `grep`). The image_id → VIO position map is fully derivable inside
  `colmap.py` from the `rigs` and `colmap_image_ids` it already has, so no
  upstream plumbing changes are required.

**Nothing outside `colmap.py` needs to change for v1.** Specifically:
`run_reconstruction.py`, `pairs.py`, `keyframes.py`, `options_builder.py`,
`database/*.sql`, the API routes, generated client packages — all
untouched.

## Configuration: skip the knob for v1

Hardcode the disagreement threshold (Umeyama-predicted vs registered
position) initially. Calibrate against a known-clean recon's 99th
percentile, same calibration approach Form A's spec calls for. Gate on
"VIO data present" — single-cam captures still have priors, so the
distinguishing condition is "this capture has `frames.csv` rotation +
translation columns populated," not "is_multi_camera."

Add the threshold to `ReconstructionOptions` only after Form C is running
on real captures and the per-capture variance in noise floors actually
justifies tuning. Promotion path if needed later: `database/*.sql` schema
change → `generate-datamodels` → API route → `generate-clients` →
`options_builder.py` reads it. That's two source commits and three
codegen commits; not worth paying upfront.

## What pycolmap exposes (verified in 4.0.4 in this repo)

The earlier worry about a hypothetical `verify_pose_callback` was wrong —
pycolmap exposes no decision callbacks, only three no-arg progress
callbacks (`INITIAL_IMAGE_PAIR_REG_CALLBACK`, `NEXT_IMAGE_REG_CALLBACK`,
`LAST_IMAGE_REG_CALLBACK`). **But we do not need a callback.** Every
primitive `IncrementalPipeline.run()` builds on is Python-bound, and
COLMAP ships an official reference implementation of the entire loop
([`custom_incremental_pipeline.py`](https://github.com/colmap/colmap/blob/main/python/examples/custom_incremental_pipeline.py),
added in [colmap/colmap#2478](https://github.com/colmap/colmap/pull/2478)).
We fork that file.

Confirmed-present primitives (all in our pycolmap 4.0.4):

- `IncrementalMapper.find_next_images(options, structure_less) → list[int]`
  (already sorted by `image_selection_method`, internal retry tracking)
- `IncrementalMapper.register_next_image(options, image_id) → bool`
- `IncrementalMapper.register_next_structure_less_image(...)` —
  structure-less fallback (this is what's registering our suspect frames
  at near-zero connectedness today)
- `IncrementalMapper.triangulate_image(...)`, `complete_tracks()`,
  `complete_and_merge_tracks()`, `merge_tracks()`, `retriangulate()`
- `IncrementalMapper.adjust_local_bundle(...)`,
  `iterative_local_refinement(...)`, `adjust_global_bundle(...)`,
  `iterative_global_refinement(...)`
- `IncrementalMapper.filter_frames(...)`, `filter_points(...)`
- `Reconstruction.deregister_frame(frame_id)` — *"De-register an existing
  frame, and all its references."* The unwind primitive.
- `Reconstruction.images[image_id].frame_id`, `frame(frame_id)`,
  `reg_frame_ids()`, `reg_image_ids()`

**We do NOT need** `custom_bundle_adjustment.py` — the mapper's native
`adjust_global_bundle`, `iterative_local_refinement`, etc. are all bound.
That upstream module only demonstrates pyceres BA customization, which
this initiative doesn't need.

`IncrementalPipeline` itself exposes `initialize_reconstruction`,
`reconstruct_sub_model`, `reconstruct`, `check_run_global_refinement`,
`check_reached_max_runtime` — those are the orchestration steps, not the
hook point. The hook point is *inside* the per-image loop in
`reconstruct_sub_model`.

## The exact hook point

In the forked `reconstruct_sub_model()`, insert between the successful
`register_next_image()` and the subsequent `triangulate_image()` /
local-BA call. Shape (annotated from `response.md`):

```python
if reg_next_success and next_image_id is not None:
    # VIO-consistency check insertion point.
    # if check fails:
    #     frame_id = reconstruction.images[next_image_id].frame_id
    #     reconstruction.deregister_frame(frame_id)
    #     skipped_image_ids.add(next_image_id)
    #     reg_next_success = False
    #     continue
    image = reconstruction.images[next_image_id]
    for data_id in image.frame.image_ids:
        mapper.triangulate_image(options.get_triangulation(), data_id.id)
    custom_bundle_adjustment.iterative_local_refinement(...)
```

Total insertion is 5–10 lines. The check body is the shared Form A body.

## Risks to verify before committing

1. **Frame ID vs image ID for multi-camera rigs.** ZED stereo writes one
   `Frame` per `(rig, timestamp)` and two `Image` rows per frame (left +
   right). `deregister_frame` operates on the frame and per docstring
   removes "all its references" — should cleanly remove both stereo
   images. Verify with a tiny test (register a frame, deregister, confirm
   both image IDs are no longer in `reg_image_ids()`) before relying on it.
2. **Skip-list discipline.** As noted above, manual `deregister_frame`
   doesn't bump COLMAP's `reg_trials`. We need a Python-side
   `skipped_image_ids: set[int]` filtered from `next_images` each
   iteration. Trivial but easy to forget.
3. **Track residue.** Hooking *before* `triangulate_image` (the
   recommendation) means the frame had only pose-estimation, no new 3D
   points, no neighbor BA touched. The "and all its references" cleanup
   should be enough. Hooking *after* local BA (to catch failures only
   visible post-refinement) makes residue cleanup harder — don't.
4. **pycolmap version drift.** The upstream example uses
   `align_reconstruction_to_orig_rig_scales`,
   `create_default_bundle_adjuster`, `BundleAdjustmentConfig`,
   `BundleAdjustmentGauge`, `reset_initialization_stats`,
   `init_num_trials`, `multiple_models`,
   `structure_less_registration_fallback`. All verified present in our
   pycolmap 4.0.4. Should transplant cleanly.

## Effort estimate (revised after pycolmap research)

| Subtask | Effort |
|---|---|
| Lift `custom_incremental_pipeline.py`, adapt to repo conventions (no docstrings, full-word vars, classes-at-top, callers-before-callees, plain `#` comments) | ~half day |
| Plumb VIO data: load `frames.csv`, key by timestamp, build `image_id → (timestamp, vio_position)` map by parsing image names `<rig>/<camera>/<frame_id>.jpg` | ~half day |
| Implement the local-Umeyama VIO check (shared body with Form A) | ~half day |
| Test on the three office captures (`4bd303f1-d6c4-4867-8e35-f788c810ce26` is the worst-aliasing one), tune threshold, verify suspects A + B get rejected without killing good loop closures | 1–2 days |
| **Total** | **~3 days** |

This collapsed from the earlier "best 1–2 days / medium 1–2 weeks / hard
multi-week" estimate once the official reference implementation was
located.

## Pre-implementation state of the repo (2026-05-31)

Current branch: `misc-fixes`. There's uncommitted work that user wants
landed before Form C implementation starts — explicit user request was
"we need to commit some stuff and get to a relatively clean repo before
we implement this work."

Uncommitted / orphaned material that needs sorting before implementation:

- `docker/reconstructor/src/reconstructor/pairs.py` —
  `PAIRS_WITH_SOURCE_FILE` constant + `write_pairs_with_source()`
- `docker/reconstructor/src/reconstructor/run_reconstruction.py` —
  imports + two artifact-upload calls for `pairs_with_source.csv` and
  `database.db`
- `docker/reconstructor/SPEC.md` — two artifact-table rows (separate prose
  commit per repo convention)
- `scripts/src/scripts/sweep_postprocess.py` and `scripts/pyproject.toml`
  entry-point — durable replacements for the lost /tmp/recon_audit driver
- `sweep-output/.gitignore` and the analysis outputs under
  `sweep-output/4bd303f1-d6c4-4867-8e35-f788c810ce26/`
- `scripts/src/scripts/displacement_check.py` — still dirty from earlier
  session work
- Top-level `sweep-matrix.md`, `response.md`, `response2.md`,
  `response3.md`, `response4.md`, `Make-it-Sing/`, `bug-aoa-permission-dialog-respawns.md`
- `.pulsar/memories/reconstruction-aliasing-failure-modes.md` may have a
  newer version landed by the most recent memorize subagent
  (commit `4ad05e9d` was the version this initiative branched from).

Commit hygiene reminders: prose-only commits separate from code commits;
codegen commits separate with canonical messages; no Co-Authored-By
trailers; no force-push.

## Decisions

- **Build Form C now**, not "Form A first, then maybe C." User chose
  explicitly. Do not relitigate.
- **`incremental_loop.py` is a new module**, not a function inside
  `colmap.py`. The fork is ~350 lines and earns its own file.
- **VIO consistency helper** lives in `incremental_loop.py` or a sibling
  `vio_consistency.py` — implementation detail, not load-bearing for the
  initiative shape.
- **No `ReconstructionOptions` schema change in v1.** Hardcode threshold;
  promote later only if real captures demand per-capture tuning. This
  avoids two codegen commits up front.
- **Hook insertion point: after successful `register_next_image`, before
  `triangulate_image` / local BA.** Cleanup is simplest there; later-stage
  hooks have residue problems.
- **Skip-list lives in Python**, not in pycolmap state. Mapper's
  `reg_trials` counter is unreliable for our use.
- **Clean the repo before starting.** Commit the pending pairs/SPEC/
  scripts/displacement work in conventional shapes before writing
  `incremental_loop.py`.

## Open questions

- **Exact `colmap.py` line number** of the `incremental_mapping(...)`
  call site. The number `175` is from the response draft; verify with
  `grep -n 'incremental_mapping' docker/reconstructor/src/reconstructor/colmap.py`
  before editing.
- **Threshold value.** "0.5–1.0 m" is a calibration range, not a number.
  First implementation pass should log per-frame disagreement values on a
  known-clean recon and pick the threshold from the 99th percentile of
  that distribution, not invent a fixed number.
- **Whether to also gate `register_next_structure_less_image` calls.**
  The suspect frames in the failure mode register via structure-less PnP.
  An aggressive policy refuses structure-less fallback entirely for
  retrieval-linked images; a conservative one applies the same VIO check
  to both. Conservative is safer for v1.
- **What happens when N=10 nearest-in-time VIO neighbors aren't all
  registered yet.** Early in the reconstruction, the local-Umeyama fit
  may be under-constrained. Fallback options: skip the check until ≥N
  registered neighbors exist; relax to N=4 minimum with looser threshold;
  global Umeyama as a fallback. Pick one before writing code.

## Key files

- `docker/reconstructor/src/reconstructor/colmap.py` — the single call
  site that needs to change. Verify line number of `incremental_mapping(...)`.
- `docker/reconstructor/src/reconstructor/pairs.py` — has the
  `(rig, camera, frame_id).jpg` naming convention the new module must
  parse to map `image_id → VIO timestamp`.
- `docker/reconstructor/src/reconstructor/rig.py` — `Rig` and `FramePose`
  types; the `rigs: dict[str, Rig]` value that `colmap.py` receives
  contains everything needed to build the `image_id → vio_position` map.
- `.pulsar/memories/reconstruction-aliasing-failure-modes.md` — the
  parent memory. Reread before implementation; it has the full mechanism
  derivation, the suspect-frame data, and the build-order rationale.
- `.pulsar/memories/reconstruction-validation.md` — displacement-test
  rationale + held-out-frame harness pointer.
- `response.md` (repo root) — the pycolmap research dump. Lists every
  primitive verified present, the exact hook point shape, and the
  effort-estimate breakdown. Likely commits-pending or gets folded into
  this memory; either way, read it first.
- [`custom_incremental_pipeline.py` upstream](https://github.com/colmap/colmap/blob/main/python/examples/custom_incremental_pipeline.py)
  — the file we fork. Match against the pycolmap version installed
  locally before lifting (4.0.4 in this repo per `uv.lock`).
- [`pycolmap` docs](https://colmap.github.io/pycolmap/index.html)
  for the bound-primitive signatures.

## Pending threads

1. **Land the pre-existing uncommitted work** (pairs / SPEC / scripts /
   displacement / sweep outputs / response markdowns) in conventionally
   separated commits before starting Form C implementation. User
   explicitly asked for this first.
2. **Fork `custom_incremental_pipeline.py`** into
   `docker/reconstructor/src/reconstructor/incremental_loop.py`, adapt
   to repo conventions (no docstrings, full-word variables,
   classes-at-top, callers-before-callees, plain `#` comments,
   relative imports for intra-package).
3. **Build the VIO-position lookup** (`image_id → (timestamp, position)`)
   from `rigs` and `colmap_image_ids` inside `colmap.py`, pass into the
   new loop.
4. **Implement local-Umeyama check** with skip-list and `deregister_frame`
   unwind. Verify the multi-camera-rig deregistration removes both
   stereo images for the same frame (Risk #1 above).
5. **Calibrate threshold** from a known-clean recon's per-frame
   disagreement distribution (99th percentile). Don't invent a number.
6. **Validate on `4bd303f1-d6c4-4867-8e35-f788c810ce26`**: suspects
   t=…865015 (exposure collapse) and t=…859015 (repeated-scene aliasing)
   should be rejected; the recon's `max_speed` should fall below
   2.5 m/s; no good loop closures should be killed.
7. **Promote threshold to `ReconstructionOptions`** only if real captures
   demand per-capture tuning. Two codegen commits + one source commit if
   so.
