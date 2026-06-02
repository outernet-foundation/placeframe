---
updated: 2026-05-30
---

# How to validate a reconstruction against its capture

## Goal

Decide whether a finished reconstruction is good enough to ship to a
localizer client. The honest answer is "route held-out frames through
the localizer and measure," but that harness is not yet built. Until it
is, the substitute is the consecutive-frame displacement check below —
the one currently-available signal that has empirically caught
degenerate reconstructions.

This memory exists because the previous validation thread leaned on
several plausible-looking signals that all turned out to grade something
other than reconstruction quality. Future sessions arriving here cold
need to know which signals to skip on sight.

## Signals that do NOT measure reconstruction quality

Don't reach for any of these as a quality gate, individually or in
combination. Each was tried and each grades a different thing:

- **Truth-aligned residual** vs VIO priors (`prior_drift_residual_*_m`,
  Umeyama-fit rms/median/max). Measures the disagreement between recon
  and priors. On any capture whose priors are drifted — i.e. any capture
  where ZED area-memory failed to close a revisit — a correct
  loop-closed recon must disagree with the priors by several meters at
  the revisit points. The metric false-positives on exactly the recons
  we want.
- **Umeyama-fit scale** vs priors. Same failure mode as above. Path
  lengths and start/end displacements can diverge between recon and
  priors when one is correctly closing a loop the other missed; scale
  close to 1.0 doesn't imply correctness, scale far from 1.0 doesn't
  imply incorrectness.
- **Trajectory-shape agreement** (rigid Umeyama residuals as a
  percentage of trajectory length). Aggregates the prior-drift problem
  across the whole capture. Same family of mistake as Umeyama scale.
- **Convex-hull volume** of camera centers (`map_bounding_volume_m3`,
  removed in `fcee131c`). A single per-frame VIO teleport inflates the
  hull while reducing trajectory smoothness. The metric rewarded the
  exact failure mode it was supposed to detect.
- **Reprojection error** (`reprojection_pixel_error_*_percentile`).
  Sub-pixel reprojection means BA converged cleanly. It tells you
  nothing about whether BA converged to the right *global* geometry —
  a recon with a meter-scale teleport mid-trajectory still has clean
  per-pair reprojection at the teleport's endpoints.
- **Registration count and rate**. COLMAP can register 100% of images
  into a geometrically wrong reconstruction.
- **Verified-match rate** (`all_verified_match_rate`,
  `stereo_verified_match_rate`) and per-pair inlier mean/median. These
  grade pair-input quality (how often `estimate_two_view_geometry`
  accepts a pair), not the assembled map.

## The one currently-working signal: consecutive-frame displacement

**Rationale:** the only thing we can check against a physical-world
prior without invoking the localizer is "did the camera move at a
plausible walking pace?" Indoors at handheld capture, sustained speeds
above ~2.5 m/s are physically impossible. Any pair of consecutive
keyframes whose recon-side center-to-center distance implies > 2.5 m/s
is a BA local-minimum teleport.

**Procedure:**

1. Pull the recon's `sfm_model/{frames.txt, images.txt}` and the
   capture's `rig*/frames.csv` from MinIO (`mc cp` recipe in
   "Operational recipes" below).
2. Run `/tmp/recon_audit/displacement_check.py <recon_dir>
   <frames.csv>` (the script's parsing logic — quaternion-from-rig_from_world →
   world_from_rig center, image-id → timestamp via filename regex —
   is reusable; tree-store under `scripts/` if it earns its keep).
3. Compare max / p99 speed against a walking-pace ceiling of 2.5 m/s.
   Healthy captures show max around 1.5 m/s; degenerate ones show
   single-pair speeds of 5–17 m/s.

**Observed signature today** on the 5-recon validation pass after the
priors-off structural fix landed (2026-05-30):

| Capture | Max speed | Pairs > 2.5 m/s | Verdict |
|---|---|---|---|
| aacad6a9 (36 MB) | 6.56 m/s | 2 / 61 | Degenerate (teleport: 3.28 m / 0.5 s) |
| 4bd303f1 (35 MB) | 9.39 m/s | 6 / 56 | Degenerate (teleport: 9.39 m / 1.0 s) |
| 17af01a0 (51 MB) | 17.34 m/s | 5 / 91 | Degenerate (teleport: 8.67 m / 0.5 s) |
| 85c17785 (155 MB) | 1.51 m/s | 0 / 89 | Healthy |
| cb717e4b (308 MB) | 1.51 m/s | 0 / 180 | Healthy |

The user-side localization check confirmed the three "degenerate"
verdicts. The two "healthy" verdicts were not contested. The signal is
not formally graded against localization output yet, but on this
five-capture set it agreed with the human read.

**Limits.** The displacement check catches gross BA teleports. It
cannot catch:

- A reconstruction that has correct local geometry everywhere but is
  globally rotated or scaled wrong.
- A reconstruction that places camera centers correctly but builds a
  point cloud full of phantom 3D points the localizer can't match against.
- Any failure mode that doesn't manifest as a per-pair velocity spike.

Treat the check as a necessary condition for shipping, not a sufficient
one. The held-out localization harness below is what makes "good
enough" actually defensible.

## The not-yet-built signal: held-out frame localization

This is the unblocking infrastructure investment. Until it exists,
every reconstructor change is graded by proxy.

**Smallest useful version:** hold out N frames (random 10%, or every
Nth) from SfM via `ReconstructionOptions.held_out_frame_timestamps` —
which is already wired through the pipeline. Build the map from the
remainder, then route each held-out frame's image through the
localizer's `/localize` endpoint against the resulting map. Record
`(position_error, rotation_error)` per held-out frame, where "truth" is
the held-out frame's `frames.csv` prior pose (knowingly drifted, but
drifted *the same way* for every reconstruction of the same capture, so
relative comparisons across reconstructions of one capture are
defensible).

**The metric is prior-relative**, with the same false-positive mode as
the Umeyama residual on drifted-prior captures. It's still useful
because (a) the relative ranking across reconstructions of the same
capture survives the prior drift, and (b) on captures whose priors are
clean (ZED area memory closed the loop, or ARFoundation with
multi-anchor handover), the absolute numbers are meaningful too.

Pieces needed: the harness driver script (Python in `scripts/`),
a slot in the localizer or API for receiving a query-image without
needing it pre-uploaded as a capture, and a results aggregator
(median / p95 over the held-out batch). The `held_out_frame_timestamps`
option already works.

## Current pipeline failure mode worth knowing

The 2026-05-30 validation found three of five recent ZED captures
producing teleport-class BA failures. The hypothesis the data
supports: `pairs.py` is structurally under-emitting candidate pairs on
small / dense captures.

**Pair sources currently emitted** (`pairs.py`):

1. Sequential, `sequential_window=10` — each frame pairs with the next
   10 frames in its rig's timestamp order.
2. Intra-frame stereo — every same-timestamp camera-pair within a rig.
3. Retrieval — top `retrieval_neighbors=20` by global-descriptor
   cosine similarity, gated by `retrieval_min_score=0.5`. The
   `retrieval_min_distance_m` dedup gate is disabled for multi-camera
   captures (the priors-off structural fix nulls `frame_poses.translation`).

**What's missing:** there is no spatial-neighbor pair source. A prior
session redesign included k=25 nearest-recon-pose-neighbors
(`spatial_neighbors`, `spatial_max_distance_m=6.0`) but that source
isn't in the current code.

**Comparison to a known-good baseline.** On capture `17af01a0`, the
exhaustive-matching control (`91068cac`, every-to-every from 354
images) produced 35,007 verified matches and a hull-correct recon.
Today's recon on the same capture (`714dca65`, sequential + intra-frame
+ retrieval) produces 3,460 verified matches — ~10× fewer — and
contains the teleports listed above.

The two big captures (155 MB / 308 MB) don't show teleports because
their longer trajectories generate enough retrieval-survivable
cross-room pairs from sheer scene diversity to keep BA constrained;
small / dense captures fall off a coverage cliff.

**Lever options** (none committed):

1. Loosen retrieval gates: `retrieval_neighbors=20→40` or `→60`;
   `retrieval_min_score=0.5→0.3`. Cheapest experiment.
2. Re-add a spatial-neighbor source that operates on recon-pose
   neighbors after an initial pass (the chicken-and-egg problem the
   previous redesign struggled with, since VIO translations aren't
   available on the priors-off path).
3. Restore exhaustive matching as the default for stereo captures.
   Expensive matching phase but a known-good fallback while the
   coverage problem is investigated.

## Operational recipes

**Pull SfM artifacts + capture priors from MinIO** (assumes
`mc alias set local http://localhost:9000 admin password` has been run
inside `placeframe-minio-1`):

```
RID=<recon_id>
CID=<capture_session_id>
WORK=/tmp/recon_audit/$RID
mkdir -p "$WORK/sfm" "$WORK/cap"
for f in frames.txt frame_poses.npz rigs.txt cameras.txt images.txt; do
  docker exec placeframe-minio-1 mc cp \
    local/dev-reconstructions/$RID/sfm_model/$f /tmp/$f
  docker cp placeframe-minio-1:/tmp/$f "$WORK/sfm/$f"
done
docker exec placeframe-minio-1 mc cp local/dev-captures/$CID.tar /tmp/cap.tar
docker cp placeframe-minio-1:/tmp/cap.tar "$WORK/cap.tar"
tar -xf "$WORK/cap.tar" -C "$WORK/cap" manifest.json rig0/frames.csv
```

**Inspect a recon's options + key metrics from Postgres:**

```
docker exec placeframe-postgres-1 psql -U postgres -d placeframe -c "
  SELECT manifest->'options', manifest->'metrics'->'all_verified_matches',
         manifest->'metrics'->'map_image_count'
  FROM reconstructions WHERE id='<rid>';"
```

**Queue a rerun unchanged** (e.g. to test against a rebuilt image):

```
docker exec placeframe-postgres-1 psql -U postgres -d placeframe -c "
  INSERT INTO reconstructions (tenant_id, capture_session_id, status,
    manifest_version, manifest)
  SELECT tenant_id, capture_session_id, 'queued'::reconstruction_status,
    manifest_version, manifest
  FROM reconstructions WHERE id='<source_recon_id>'
  RETURNING id;"
```

**Override a single `ReconstructionOptions` field** on a rerun without
a code change:

```
docker exec placeframe-postgres-1 psql -U postgres -d placeframe -c "
  INSERT INTO reconstructions (tenant_id, capture_session_id, status,
    manifest_version, manifest)
  SELECT tenant_id, capture_session_id, 'queued'::reconstruction_status,
    manifest_version,
    jsonb_set(manifest, '{options,<field>}', to_jsonb(<value>))
  FROM reconstructions WHERE id='<source_recon_id>';"
```

**Frame-rate file layouts** (in case the displacement script is lost):

- `frames.csv` (capture priors, `world_from_rig` in OPENCV axis):
  3 columns `timestamp_ms,gx,gy,gz` (gravity-only — current ZED),
  6 columns adding `tx,ty,tz` before gravity, or 7 columns adding
  quaternion. See `docker/reconstructor/SPEC.md` "frames.csv schema".
- `sfm_model/frames.txt` (COLMAP rig output, `rig_from_world`): per
  non-comment line `FRAME_ID RIG_ID QW QX QY QZ TX TY TZ NUM_DATA_IDS
  [SENSOR_TYPE SENSOR_ID DATA_ID]…`. Hamilton quaternion `QW QX QY QZ`.
  Recon rig center in world = `-R(rig_from_world).T @ t(rig_from_world)`.
- `sfm_model/images.txt`: pairs of lines per image; odd lines are
  `IMAGE_ID QW QX QY QZ TX TY TZ CAMERA_ID IMAGE_NAME`. Map IMAGE_ID
  to timestamp via the path pattern `rig\d+/camera\d+/(\d+)\.jpg`.

## How we got here in three sentences

The original `17af01a0` capture has ~12 m of accumulated VIO drift on a
revisit to the same physical desk. For months the framework treated the
drifted priors as ground truth and mis-diagnosed each correct
loop-closing recon as broken via Umeyama residual and hull-volume
metrics. Three diagnostic experiments — JPG visual confirmation of the
revisit, a tight-prior BA control that pulled the recon into the bad
priors, and a held-out-end recon that recovered the loop closure
without the disputed frames — closed that thread; the validation
methodology in this file is what survived.

## Pending threads

### Build the held-out-frame localization harness

The single most-unblocking infrastructure investment for every
reconstructor-quality question. `held_out_frame_timestamps` works;
need the driver + localizer query path + aggregator.

### Decide what to do about the pair-coverage failure mode

Cheapest first move is loosening retrieval gates and re-running the
five-capture validation pass with the displacement check. If that
doesn't recover the small-capture cases, the next move is the
two-pass spatial-neighbor source (recon-pose neighbors after an
initial SfM pass).

### Promote `displacement_check.py` from `/tmp` to `scripts/`

If the next session reaches for it again, tree-store it under
`scripts/src/scripts/` with a proper Typer CLI so it's not perpetually
rebuilt from the recipe above.

## Key files

- `docker/reconstructor/src/reconstructor/pairs.py` — `generate_image_pairs`,
  the under-emitting generator. Knobs: `sequential_window`,
  `retrieval_neighbors`, `retrieval_min_distance_m`, `retrieval_min_score`.
- `docker/reconstructor/src/reconstructor/colmap.py:198-217` —
  Procrustes truth-alignment residual computation. Diagnostic, not a
  quality gate; see `docker/reconstructor/SPEC.md` "Map-frame alignment"
  for the rationale.
- `docker/reconstructor/src/reconstructor/rig.py` — keyframe selector
  (`keyframe_min_translation_m`, `keyframe_min_rotation_deg`) and
  multi-camera rig structural-priors-off detection (`is_multi_camera`).
- `packages/python/core/src/core/reconstruction_options.py` — the
  `ReconstructionOptions` schema. `held_out_frame_timestamps` is the
  hook the localization harness will use.
- `docker/reconstructor/SPEC.md` — the durable design constraints. The
  pair-generation, priors-off-structural, and Umeyama-as-diagnostic
  rationales are all there.
- `docker/localizer/` — the localizer service. Boundary where the
  held-out-frame harness will plug in.
