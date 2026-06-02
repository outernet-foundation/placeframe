# Pair-generation rebuild plan

Concrete proposal for fixing the office-reconstruction failure that surfaced on 2026-05-30. Hand-off doc — written so a fresh session can pick this up cold without re-reading the prior session.

## What we're trying to fix

Five test reconstructions ran end-to-end on 2026-05-30 against the just-landed structural-priors-off fix (every multi-camera capture runs BA priors-off, stereo baseline pinned). The two large captures (155 MB / 308 MB) produced healthy maps. The three small captures (35–51 MB) shipped with physically-impossible per-keyframe-pair speeds — 6 to 17 m/s between adjacent keyframes 0.5–1.5 s apart — that the user then confirmed look broken at localization time.

The failure is concentrated on small office captures: repetitive low-texture walls, ceiling tiles, similar hallways. Big captures sweep through enough scene diversity to hide the issue.

## Diagnosis

The current `docker/reconstructor/src/reconstructor/pairs.py` emits three pair sources:
1. **Sequential** — each frame paired with the next 10 frames in its rig's timestamp order.
2. **Intra-frame stereo** — every same-timestamp camera-pair within a rig.
3. **Retrieval** — top-20 by global-descriptor cosine similarity, gated by `retrieval_min_score=0.5`.

A spatial-neighbor source (k-NN by VIO position) existed in a prior redesign but was removed. The current code also nullifies `frame_poses[].translation` for any multi-camera rig (see `rig.py:Rig.__init__`), so even the residual position-driven gates (`retrieval_min_distance_m`) are silently disabled on every ZED capture.

On the known-good exhaustive control (commit context: `91068cac` against capture `17af01a0`), 35,007 verified matches landed across 354 images — ~99 verified-pair-edges per image. On today's structural-fix run of the same capture (`714dca65`), 3,460 verified matches across 184 images — ~18 edges per image. The active pair sources don't reach far enough across the capture; small office captures fall off a coverage cliff where retrieval can't compensate (textureless walls produce descriptor similarities clustered below 0.5).

The architectural insight: **priors-as-pair-gen-signal and priors-as-BA-constraint are not the same ask.** BA enforces priors as a quadratic loss, so drift of N meters in the priors injects N meters of error into the global geometry (the original `17af01a0` failure). Pair gen only uses priors to *choose candidate pairs*, and 2-view verification filters the candidates afterward. Pair gen is robust to bidirectional drift error: bad-prior pairs that have no shared content fail verification cheaply; good-prior pairs survive. The current code threw out a useful signal on the basis of a failure mode that doesn't apply to it.

## Architectural shape

Three pair sources, each strictly necessary because each compensates for the others' failure modes:

- **Sequential** (temporal, always-on). Window of ±N frames in capture order. Handles temporal continuity and motion-driven parallax. Fails on revisits and large jumps. Cheapest, most-trusted source.
- **Spatial / proximity** (pose-driven, opt-in when priors exist). Pairs every frame with every other frame whose VIO position is within `spatial_max_distance_m`, capped at top-K closest if too many qualify. No optical-axis cone, no rotation gate. Drift-robust at moderate distances because errors of a few meters don't change which frames are room-neighbors. Fails open at long range (priors said two frames were 12 m apart at the same desk on `17af01a0`) — retrieval catches those.
- **Retrieval** (content-driven, always-on). Top-K by descriptor cosine similarity, gated by `retrieval_min_score`. Specializes in cross-trajectory loop closures where VIO drifted past `spatial_max_distance_m`. With spatial carrying the local-neighborhood load, retrieval's job narrows to its strength.

Plus intra-frame stereo (existing, keeps multi-rig metric scale).

The minimum-correct algorithm:

```
for each frame F:
    sequential = [F-W .. F+W]                                            # always
    spatial    = top_k(neighbors(F, d ≤ D))                              # if positions exist
    retrieval  = top_k(descriptors, score ≥ S,
                        excluding neighbors(F, d < d_min))               # always
emit dedup(sequential ∪ spatial ∪ retrieval ∪ intra_frame_stereo)
```

Three knobs that actually matter: `sequential_window`, `spatial_max_distance_m`, `retrieval_min_score`. Default to permissive on all three for now; tighten later when there's a real localization-quality signal to grade them against.

## Code-level proposal

### 1. Revert `02cb52fa Write per-frame gravity instead of pose to frames.csv for ZED captures`

The user confirmed no captures use the gravity-only schema yet, so a straight `git revert` is safe. ZED captures resume writing the 7-column `timestamp_ms,tx,ty,tz,qx,qy,qz,qw` shape but also keep gravity (the gravity-writing logic stays; the change is that positions come back alongside it).

Net post-revert behaviour on the box: every frame row carries gravity + position + rotation. The reconstructor's existing 7-column code path (rotation discarded, position kept) handles this — no parser change.

The schema documentation in `docker/reconstructor/SPEC.md` ("frames.csv schema is column-count-dispatched") may need a one-line tweak to reflect that the 3-column gravity-only case is no longer the active capture path. Keep the parser support — it costs nothing and might be useful for future single-camera capture devices.

### 2. Restore translation in `rig.py:Rig.__init__` for multi-camera rigs

Currently:

```python
pose = _parse_frame_pose(fields[1:], axis_convention)
if self.is_multi_camera:
    # Drop translation so legacy 7-field frames.csv files don't leak
    # drifted VIO positions into pair generation's retrieval-distance gate.
    pose = FramePose(translation=None, gravity_in_rig_local=pose.gravity_in_rig_local)
elif pose.translation is None:
    raise ValueError(...)
self.frame_poses[frame_id] = pose
```

Change shape: keep the translation populated regardless of rig structure. The "drifted positions poison BA" concern that motivated the nullification still holds, but the fix belongs at the BA boundary, not at parse time.

```python
pose = _parse_frame_pose(fields[1:], axis_convention)
if not self.is_multi_camera and pose.translation is None:
    raise ValueError(...)
self.frame_poses[frame_id] = pose
```

Then in `colmap.py` (the BA boundary), the existing `is_multi_camera_capture` flag continues to gate whether `PosePrior` rows are written into the COLMAP database. BA never sees the priors on multi-camera; pair gen always does.

Concretely:
- `colmap.py:90` (`for frame_id, transform in rig.frame_poses.items()`) currently writes `PosePrior` rows. This needs a guard that's already implied by the `use_prior_position` plumbing: skip the `PosePrior` write when `use_prior_position=False`. Verify the guard is present and explicit, not just relying on translation being None.
- `_registered_frames` and any downstream consumer that uses `transform.translation` for non-pair-gen purposes needs an audit — if any of them feed BA, they need the same guard.

The cleanest framing in the FramePose data shape itself: split into `pose_for_pair_gen` (always populated when capture provides it) and a guarded `pose_for_ba` (populated only when `use_prior_position`). Don't gate by `translation is None` at the consumer site — that's the kind of implicit coupling that re-bites us later. An explicit field is worth the rename churn.

### 3. Remove Lucas-Kanade keyframe selection; replace with distance-based subsampling on device priors

Delete `docker/reconstructor/src/reconstructor/keyframes.py` outright, drop the `select_keyframes_by_parallax` import and the rig-subsampling loop from `run_reconstruction.py`, and drop `keyframe_parallax_threshold_px` from `ReconstructionOptions` (codegen regenerates clients). The `opencv-python-headless` dependency in `docker/reconstructor/pyproject.toml` goes with it unless something else picked it up — check before removing.

LK was the wrong primitive: it integrates per-frame median optical flow, which sums apparent on-screen motion regardless of whether the camera actually moved. Pure rotation in place trips the threshold rapidly and emits a cluster of keyframes that all share the same world position (zero baseline for triangulation). Pure forward motion barely trips it at all (the focus of expansion sits at image center, so median flow stays small). Handheld jitter inflates the accumulator without adding parallax. Textureless walls force every frame through the `<10 valid corners` fall-through. None of these failure modes are theoretical — every one of them fires on real ZED office captures.

The replacement is the simplest thing that works: read positions from the device's own VIO (now restored to `frames.csv` by step 1 and to `Rig.frame_poses[*].translation` by step 2), walk each rig's frames in capture order, and keep a frame iff its translation from the last-kept keyframe exceeds `keyframe_min_distance_m`. The first frame of each rig is always kept.

New module `docker/reconstructor/src/reconstructor/keyframes.py`:

```python
def select_keyframes_by_distance(
    frame_ids_in_order: list[str],
    translations_by_frame_id: dict[str, NDArray[float64]],
    min_distance_m: float,
) -> list[str]:
    if not frame_ids_in_order:
        return []
    kept: list[str] = [frame_ids_in_order[0]]
    last_kept_translation = translations_by_frame_id[frame_ids_in_order[0]]
    for frame_id in frame_ids_in_order[1:]:
        translation = translations_by_frame_id[frame_id]
        if float(linalg.norm(translation - last_kept_translation)) >= min_distance_m:
            kept.append(frame_id)
            last_kept_translation = translation
    return kept
```

Call site in `run_reconstruction.py`:

```python
for rig in rigs.values():
    ordered_frame_ids = sorted(rig.frame_poses.keys(), key=int)
    translations_by_frame_id = {fid: rig.frame_poses[fid].translation for fid in ordered_frame_ids}
    kept_frame_ids = set(select_keyframes_by_distance(
        ordered_frame_ids,
        translations_by_frame_id,
        min_distance_m=options.keyframe_min_distance_m(),
    ))
    rig.frame_poses = {fid: pose for fid, pose in rig.frame_poses.items() if fid in kept_frame_ids}
```

New `ReconstructionOptions` field: `keyframe_min_distance_m: float = 0.3`. The known-good exhaustive control on `17af01a0` (354 images across roughly 2–3 minutes of office walking) sits around 0.4–0.5 m per kept frame, so 0.3 m gives a small safety margin toward more keyframes rather than fewer. Tighten or loosen later against the localization harness.

This depends on step 2 — `translation` must be populated. With single-camera (ARFoundation) captures, translations come from monocular VIO; with multi-camera (ZED) captures, from the SDK's GEN_3 tracker. Either way the input is the device's own pose stream, the same signal the prior LK selector was trying (and failing) to approximate visually.

Edge: a fully stationary capture emits only the first frame. That's correct behaviour — no spatial coverage was added, no extra keyframes are useful. Edge: a capture with all sub-threshold motion (e.g. a single 20-cm hand wobble) also emits only the first frame; surface that as `print` output the same way the count line works today.

### 4. Add the spatial source to `pairs.py`

Add `spatial_neighbors` and `spatial_max_distance_m` back to `ReconstructionOptions` (codegen will regenerate clients).

In `generate_image_pairs`:

```python
spatial_frame_pairs: list[tuple[tuple[str, str], tuple[str, str]]] = []
for rig_id, rig in rigs.items():
    frame_ids_with_translation = [
        fid for fid in rig.frame_poses
        if rig.frame_poses[fid].translation is not None
    ]
    if not frame_ids_with_translation:
        continue
    positions = stack([rig.frame_poses[fid].translation for fid in frame_ids_with_translation])
    distances = norm(positions[:, None, :] - positions[None, :, :], axis=-1)
    # For each frame, take all neighbours within spatial_max_distance_m,
    # capped at top spatial_neighbors closest. Self-pair excluded.
    for i, frame_id_a in enumerate(frame_ids_with_translation):
        in_range = where((distances[i] <= spatial_max_distance_m) & (arange(len(frame_ids_with_translation)) != i))[0]
        if len(in_range) > spatial_neighbors:
            in_range = in_range[argsort(distances[i, in_range])[:spatial_neighbors]]
        for j in in_range:
            spatial_frame_pairs.append(((rig_id, frame_id_a), (rig_id, frame_ids_with_translation[j])))
```

Cross-rig (the multi-rig handheld-bar case) handled by extending the loop over all `(rig_a, rig_b)` pairs and computing inter-rig distances. Defer until multi-rig captures actually exist; the single-rig case is what matters for the current ZED captures.

The spatial source goes into the same union/dedup at the end:

```python
return sorted({
    (a, b) if a <= b else (b, a)
    for a, b in cross_frame_image_pairs + intra_frame_image_pairs + retrieval_image_pairs + spatial_image_pairs
    if a != b
})
```

### 5. Tune the knobs

Suggested starting defaults:

- `keyframe_min_distance_m`: 0.3 — close to the known-good exhaustive control's effective spacing, slightly denser as safety margin.
- `sequential_window`: keep at 10 (existing default; works on the captures that work).
- `spatial_neighbors`: 25 — the redesign's prior value; well above what 6 m radius produces in dense indoor.
- `spatial_max_distance_m`: 6.0 — room diagonal indoors; captures cross-room pairs without becoming exhaustive in large captures.
- `retrieval_neighbors`: 20 (existing).
- `retrieval_min_score`: 0.5 (existing). Tighten later if retrieval over-emits now that spatial covers the close range.
- `retrieval_min_distance_m`: 1.0 (existing). With positions restored, this re-activates and dedups retrieval against close-range spatial/sequential coverage.

### 6. Validate by re-running the 5-capture audit

The 5 captures from the 2026-05-30 run are still in MinIO (`dev-captures/*.tar`). Queue fresh reconstructions against them after the code change lands (`uv run up --build --quiet-pull` to rebuild, then either re-queue via the existing capture rows or use the SQL recipe in `.pulsar/memories/reconstruction-validation.md`). Run the consecutive-frame displacement check on each (`displacement_check.py` is in `/tmp/recon_audit/` from the prior session; same script applies). All five should have max keyframe-pair speeds under ~2.5 m/s. If the three previously-broken captures still teleport, the pair-coverage hypothesis is wrong and the next move is a held-out localization harness.

## What we're explicitly rejecting and why

- **Two-pass pair generation with recon-pose spatial expansion.** Architecturally clean but unnecessary if priors are restored as pair-gen input. The user reconsidered the priors-off-everywhere position; two-pass was the workaround for not having priors. Single-pass with restored priors is structurally simpler.
- **Loosening retrieval gates alone** (`retrieval_neighbors=40, retrieval_min_score=0.3`). Cheapest experiment but the wrong shape: retrieval is content-similarity, and on office scenes content similarity is genuinely low across the descriptor — loosening to 0.3 admits aliased pairs (descriptor-similar but spatially-distant) faster than it admits real loop closures. Pose-driven spatial is the right primitive.
- **Default to exhaustive matching on small captures.** Considered as a known-good fallback. Doesn't scale to large captures (308 MB capture's C(362,2)≈65k pairs × 0.5 s/pair ≈ 9 h matching) and adds a size-based branch we'd then have to maintain.
- **Optical-axis cone filter on spatial pairs** (110° was the prior default). Removes legitimate looking-back loop closures where two cameras face each other across the same scene. The prior redesign got bitten by this. Verification step filters bad-geometry pairs; let it do its job.
- **Distance-stratified spatial sampling** (5 within 0–1m, 10 within 1–3m, 10 within 3–6m). Was floated as a fix for spatial k-NN degenerating in dense indoor. The simpler "all-within-distance capped at top-k" achieves the same result because sequential already covers the close range. Less parameters.
- **Keeping the LK parallax keyframe selector around as a fallback.** It is being deleted, not gated behind a flag. It conflates rotation-driven pixel flow with translation-driven parallax: pure rotation emits a dense cluster of zero-baseline keyframes, pure forward motion barely emits any, and textureless surfaces force every frame through. Distance-based selection on device priors is strictly better whenever priors exist — and priors now always exist after step 1. If a future capture device ships without VIO, the right replacement is essential-matrix-decomposition or stereo-rectified-disparity thresholding, not LK.

## What we still don't know

The displacement check is a necessary-but-not-sufficient gate on reconstruction quality. It catches gross BA teleports but can't grade a recon that has correct local geometry but is globally rotated wrong, or one that places camera centers correctly but builds a 3D point cloud the localizer can't match against.

The actual quality signal we want is held-out-frame localization error, and the harness for that doesn't exist. Building it is the unblocking move for every reconstructor-quality question; the current plan is the cheapest-effective-fix we can make against a proxy signal. Once the harness exists, every parameter in this proposal becomes tunable against a real metric rather than against "did the displacement check pass."

This is the durable Pending thread to flag for the next session: build the held-out-localization harness against the priors-restored pipeline.

## Short history of what's been tried

Captured tersely so the next reader doesn't have to dig through commit messages.

- **Pose-nearest pair generator with rotation + baseline gates**: deleted before the recent debugging started; pre-existing failure mode unrelated to the current work.
- **Sequential + ungated retrieval**: the shape that shipped during the original `17af01a0` saga. Produced a tight loop closure on the desk-revisit but the framework was reading hull volume as a quality metric and incorrectly diagnosed it as "hull collapsed." The recon was actually correct; the metric was wrong.
- **Exhaustive matching control** (`91068cac` on `17af01a0`): 62,481 input pairs, 35,007 verified. Hull-correct by the metric of the day. Real production cost: ~9 minutes matching phase on a 354-image capture. Used as a known-good reference but never as a default.
- **Sequential + spatial k-NN(25) + pose-gated retrieval + intra-frame stereo**: the prior redesign. Removed from the current code. The session that wrote it concluded it failed because of hull collapse; the diagnostic memory written later (`reconstruction-quality-evaluation.md`, since folded into `reconstruction-validation.md`) reversed that conclusion — the redesign was actually producing smoother trajectories than the exhaustive control, with no per-frame teleports, but the validation framework couldn't see it.
- **Structural priors-off everywhere (commit `9158cd61` and the rig.py translation nullification)**: the just-landed change. Correctly disables BA priors for multi-camera but overshoots by also disabling pair-gen priors. The plan above corrects the overshoot while keeping the BA half.
- **LK parallax keyframe selector (commit `1dda77e2`)**: replaced a VIO-based keyframe selector at a moment when device priors had been declared untrustworthy. The replacement integrates per-frame median optical flow as a "parallax" proxy, but parallax requires baseline translation, not apparent motion — so rotation in place trips the threshold rapidly with zero baseline, forward motion barely trips it, and textureless walls force-keep every frame. Being deleted by this plan and replaced with distance-based subsampling on the now-restored device priors.
- **Gravity-only `frames.csv` (commit `02cb52fa`)**: dropped position columns from new ZED captures on the (now-superseded) assumption that priors were useless if BA can't consume them. Reverted by this plan.

## Reading order for cold rehydration

1. This file (you're in it).
2. `.pulsar/memories/reconstruction-validation.md` — the validation methodology, including which signals don't measure quality. Specifically the "What signals do NOT measure reconstruction quality" section, because that's the trap most easily re-fallen-into.
3. `docker/reconstructor/SPEC.md` — current pipeline design. The "Pair generation is sequential + retrieval; pair acceptance is not gated by priors" section captures the current shape; this plan updates that section as part of step 3.
4. `docker/reconstructor/src/reconstructor/pairs.py` — current pair-gen source. Step 4's spatial source slots into `generate_image_pairs`.
5. `docker/reconstructor/src/reconstructor/rig.py` — `Rig.__init__` and `_parse_frame_pose` are where step 2's translation-restore lives.
6. `docker/reconstructor/src/reconstructor/keyframes.py` + `run_reconstruction.py` rig-subsampling block — what step 3 deletes and replaces.
7. `docker/zed-capture/src/zed/zed.py` — capture-side `update_pose` + CSV writer. Where the position columns go back in (step 1).

## Action items

In order. Each is one-commit-sized:

1. `git revert 02cb52fa` and verify the ZED capture path writes 7 columns again. Update `docker/zed-capture/SPEC.md` if the gravity-only narrative is described there.
2. Restore translation in `Rig.__init__` and the explicit BA-side guard (separate field or comment guard on the PosePrior write). Update `docker/reconstructor/SPEC.md`'s priors-on-vs-priors-off paragraph to reflect the new shape ("priors-off in BA, priors-on in pair gen").
3. Replace LK keyframe selection with distance-based subsampling: rewrite `keyframes.py`, drop `keyframe_parallax_threshold_px` and add `keyframe_min_distance_m` on `ReconstructionOptions`, swap the call in `run_reconstruction.py`, remove the `opencv-python-headless` dep from `docker/reconstructor/pyproject.toml` if nothing else uses it. Update `docker/reconstructor/SPEC.md`'s keyframe-selection paragraph.
4. Re-add `spatial_neighbors` and `spatial_max_distance_m` to `ReconstructionOptions` and wire the spatial source into `pairs.py`. Update `docker/reconstructor/SPEC.md`'s pair-generation constraint paragraph.
5. `uv run generate-clients` to regenerate clients for the new ReconstructionOptions fields. Separate commit (`Run generate-clients`).
6. Rebuild stack (`uv run up --build --quiet-pull`), re-queue the 5 captures, run the displacement check on each. If all 5 pass: ship. If not: surface what failed and consider whether the localization harness needs to come first.

Code commits and prose commits separate per project convention. SPEC.md updates from steps 1–4 can land as a single prose commit folded into the appropriate position via `git commit --fixup` + `git rebase --autosquash`.
