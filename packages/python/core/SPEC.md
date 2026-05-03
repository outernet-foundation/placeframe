# core — shared domain types and utilities

`packages/python/core` holds Python types and pure utilities shared across the localizer, reconstructor, scripts, and other backend Python services. It deliberately doesn't depend on `neural_networks` (Docker-build constraint: `core` is small and ships in every service image; `neural_networks` is large and only ships where it's needed).

This SPEC describes the durable design surfaces. Operating instructions live in the top-level `CLAUDE.md`.

## Calibration

### Artifact format

Single JSON document. ~3 KB global, ~1 KB per-map.

```json
{
  "schema_version": 1,
  "pipeline_version": "abc123def456...",
  "fit_at": "2026-04-29T14:00:00Z",
  "fit_by": "scripts/fit_calibration.py",
  "sample_count": 8743,
  "tight": {
    "logistic_weights": [0.234, -1.83, 0.45, ...],
    "logistic_intercept": -2.14,
    "logistic_feature_names": ["log_inliers", "inlier_ratio", "reproj_err_norm", ...],
    "isotonic_x_breakpoints": [0.01, 0.05, 0.10, ..., 0.99],
    "isotonic_y_breakpoints": [0.02, 0.06, 0.12, ..., 0.97]
  },
  "loose": { "logistic_weights": [...], ... },
  "sigma_meas_alpha": 32.0,
  "sigma_meas_beta": 2.56,
  "loose_min": 0.25,
  "tight_min": 0.0
}
```

Per-map artifact has the same shape but only `tight.isotonic_*` and `loose.isotonic_*` blocks (the global logistic is the upstream).

### `Features` typed seam

`core.calibration.Features` is a Pydantic model with all 11 named float fields (`log_inliers`, `inlier_ratio`, `reproj_err_norm`, `inlier_coverage`, `log_num_matches`, `log_map_image_count`, `log_map_point_count`, `map_avg_track_length`, `log_map_bounding_volume_m3`, `map_viewpoint_diversity`, `is_indoor`). `FEATURE_NAMES` derives from `Features.model_fields` so the field set has one source of truth.

`apply_global_calibration(calibration: CalibrationArtifact, features: Features) -> Confidence` takes the typed model rather than `dict[str, float]`. Load-time `_validate_feature_names` rejects artifacts whose `logistic_feature_names` don't match. Both fit-side row construction (`fit_calibration.py`) and inference-side feature construction (`build_metrics.py`) build `Features` instances, so the fit-time and inference-time feature sets are guaranteed to match by type.

### Gate thresholds

`loose_min` and `tight_min` are fields on `CalibrationArtifact`, not localizer module constants. The localizer reads them at startup and gates per-localization (`if metrics.confidence.loose < calibration.loose_min: raise LocalizationError(...)`). Future calibration changes are artifact-only, with no localizer code edit. The localizer is decoupled from threshold-tuning.

### Storage and lifecycle

| Artifact | Path | Updated by | Cadence |
|---|---|---|---|
| Global calibration | `config/calibration/global.json` (git repo) | Engineer (PR after fit) | Manual, on demand. Refit on every pipeline-affecting change to the localizer; otherwise refit when corpus grows meaningfully. |
| Per-map calibrations (when fitter exists) | `s3://placeframe-maps/{map_id}/calibration.json` (MinIO) | Fit pipeline (automated upload) | Manual, on demand. Per-map, once sample count clears the threshold and is materially out of date. |
| Phone-side calibration data (raw logs, when dogfooding logger exists) | `s3://placeframe-calibration-data/sessions/{session_id}.json` (MinIO) | AndroidMobile app | Per session at session end. |

Updating global: run fit → `git diff` → review → PR → merge → deploy. No Docker rebuild; mounted as compose `configs:` volume.

## Image preprocessing

Two parallel preprocessing paths sit side-by-side in `core/image_preprocess.py` and `core/camera_config.py`:

- **Local features**: `canonicalize_image(buffer, orientation)` rotates to natural orientation and resizes the shorter side to `LOCAL_FEATURE_RESIZE_SHORTER_SIDE` (1024 px). Aspect ratio preserved; no padding. `canonicalize_intrinsics(camera)` applies the same per-axis resize ratio to `(width, height, fx, fy, cx, cy)` so PnP stays correct.
- **Retrieval**: `tile_image(image)` takes the shorter-side-resized image and produces M overlapping `LOCAL_FEATURE_RESIZE_SHORTER_SIDE × LOCAL_FEATURE_RESIZE_SHORTER_SIDE` square crops along the long axis. `RETRIEVAL_TILE_OVERLAP_FRACTION = 0.5` (~50% overlap); M is derived from long-axis length.

### Why scale standardization for local features

ALIKED's receptive field is a fixed pixel patch (~30×30). At native phone resolution that patch covers a tiny physical area (a few cm of a wall) and lands on sub-pixel texture; at lower resolution the same patch covers a much larger physical region and lands on coarse structure. Cross-resolution descriptors describe different scales of reality and don't match. Standardizing physical-meters-per-pixel via shorter-side resize fixes this. ALIKED is fully convolutional and consumes variable HxW directly. LightGlue absorbs portrait↔landscape via keypoint coordinates — the per-keypoint matching paradigm naturally tolerates cross-aspect query/database pairs because matching only needs *overlapping content somewhere*: keypoints in the overlap match, keypoints in the non-overlap have no counterpart and get rejected by RANSAC. No retrieval-style framing fix is needed at this layer.

### Why square-tile aggregation for retrieval

DIR (and any CNN-backbone global retrieval — EigenPlaces, NetVLAD, SALAD, DINOv2-GeM) produces *one descriptor per image*, summarizing all framed content. Cross-aspect query/database pairs summarize *different* framed content even when the underlying scene is identical: a portrait query of a building and a landscape database image of the same building include/exclude different left/right/top/bottom strips. The global descriptors describe different overall framings and don't match well — and reshaping the input (resize, distort, letterbox) can't recover content that wasn't framed in the first place.

The fix isn't preprocessing — it's giving each image *multiple framings* so at least one tile pair frames similar content.

- **Database side** (reconstructor): store M descriptors per database image. OPQ index size and storage scale by M.
- **Query side** (localizer): tile the query the same way; produce M descriptors per query.
- **Similarity**: max over `M_query × M_db` pairs (default; mean is the alternative — left as a tuning surface for the parameter sweep). Per-database-image similarity is the max over all `(query_tile, db_tile)` pairs for that image.
- Top-K retrieval picks database images with at least one tile-pair scoring highly, regardless of how the query and database images were originally framed.

Cost: M× retrieval index storage (OPQ matrix and PQ codes), M× DIR forward passes per image (one-time at indexing, recurring per-query), `M_query × M_db` similarity work per (query, db-image) pair. Bounded — typical M = 3 to 5.

A previous design tried to address cross-aspect framing with an in-DIR letterbox + mean padding. That was the wrong fix: reshaping the input can't recover content that wasn't framed in the first place. The letterbox was reverted in favor of square-tile aggregation. `DIR.forward` is now a thin wrapper around the dirtorch model; tile preparation is the caller's responsibility.

### Open tunables (image preprocessing)

| Parameter | Default | Where used |
|---|---|---|
| `LOCAL_FEATURE_RESIZE_SHORTER_SIDE` | 1024 px | `canonicalize_image`, also defines tile size |
| `RETRIEVAL_TILE_OVERLAP_FRACTION` | 0.5 | `tile_image` |
| `RETRIEVAL_TILES_PER_IMAGE` (M) | derived from long axis + overlap; min 1, typical 3–5 | `tile_image` |
| Tile similarity aggregation | `max` (alternative: `mean`) | retrieval similarity computation |

## Static tensor shape typing

The codebase uses static tensor-shape typing (PEP 646 + NumPy 2.1 generics) at function and assignment boundaries throughout the localizer, reconstructor, and shared `core` / `neural_networks` packages. Catches dim-mismatch bugs at type-check time without runtime overhead, library dependency, or CI cost.

### Shim and brand placement

- **`core/tensor_types.py`** holds only the `TT[*Shape]` torch shim. ~17 lines; no other contents.
- **Dim brands live next to the concept that defines them**:
  - `NumImages`, `MaxTiles`, `NumQueryTiles` in `core/image_preprocess.py`
  - `RetrievalDim`, `NumKeypoints`, `LocalDescDim` in `core/model_wrappers.py`
  - `NumMatches` in `core/lightglue.py`
- **`core/lightglue.py`** is fully off `NDArray` and exports `Keypoints` / `Descriptors` / `KeypointsArrays` / `DescriptorsArrays` `NewType` brands so positional swaps at the matcher are caught statically.

### Wrappers in `core`, not `neural_networks`

`core/model_wrappers.py` houses four `make_*` factories — `make_global_descriptor_extractor` (DIR), `make_local_feature_extractor` (ALIKED), `make_local_feature_matcher_for_tensors`, `make_local_feature_matcher_for_arrays` (LightGlue, tensor-input and numpy-input variants). Both `localize.py` and `run_reconstruction.py`'s `load_models()` consume them.

Wrappers live in `core` (not `neural_networks.models`) because `neural_networks` deliberately doesn't depend on `core` (Docker-build constraint). The `make_*` helpers take `Any` for the raw model; the typed callable they return recovers full brand info at the seam.

### Numpy and torch operation wrappers

- `core/numpy_ops.py` — numpy sibling (`zeros` per rank; rank-1 `nonzero` and `compress`).
- `docker/localizer/src/torch_ops.py` — thin per-rank torch wrappers typed via `@overload` so output shape flows from runtime args. See `docker/localizer/SPEC.md` "Tensor operations" for the rationale on per-rank `@overload` sets.

### What's intentionally not done

- **No runtime shape checking** (jaxtyping / phantom-tensors). Out of scope. Static checking at boundaries plus the natural runtime errors torch / numpy throw on mismatched shapes are sufficient.
- **No per-element shape arithmetic** (e.g. `reshape` propagating literal sizes through computed dims). Not expressible in Python's type system today.
- **No tensor-library dependency**. Bare NumPy 2.1 generics + the small `tensor_types.py` shim cover the use case without depending on a small or unmaintained project.
- **`ndarray[tuple[int, int], ...]`** (rank-known, sizes-unknown) remains a legitimate escape hatch for dicts-of-arrays where each entry has a different `N`. `TID251` on `NDArray` plus `reportExplicitAny` cover ~95% of the value with no false positives.

### Pyright support

We're a pyright-only shop in basedpyright strict mode. Pyright's PEP 646 support has rough edges on advanced unifications (variadic middle dims with literal endpoints) but works for the patterns this codebase needs. `from torch import from_numpy` has one residual `reportUnknownVariableType` because torch's stub declares `from_numpy(ndarray) -> Tensor` with no parameter annotation; the wrapper consumes it and returns a fully-typed `TT[A, B, C]` so the unknown does not propagate to consumers.

The workspace venv syncs with `--extra cpu` (`uv sync --all-packages --extra cpu`) so torch resolves locally — without it, other `reportUnknown*` errors drown out real signal.
