# packages/python/core/SPEC.md

## What this is

`core` is the workspace Python package that holds the vocabulary shared between Placeframe's backend services. It contains the Pydantic schemas that travel over HTTP and through Postgres JSONB columns, the coordinate-frame primitives that bridge OpenCV-space (reconstructor / COLMAP) and Unity-space (phone clients / localizer responses), the image and intrinsics canonicalization used by both the map-builder and the query path, the HDF5 / FAISS-OPQ on-disk artifact formats, and the global confidence-calibration model. The distribution name is `core` and every import is `from core.<module>`. `docker/api/`, `docker/localizer/`, `docker/reconstructor/`, `docker/zed-capture/`, and `scripts/` declare it as a workspace dep. See `docker/SPEC.md` for the service mesh that consumes these types.

## Shape

The package is flat: 16 leaf modules under `src/core/`, no `__init__.py` re-exports, every consumer imports from a leaf. There are no tests inside `core/`; behaviour is exercised end-to-end from the consumer test suites (`docker/localizer/tests/test_build_metrics.py`, `docker/reconstructor/tests/test_rig.py`, `scripts/tests/test_fit_calibration.py`).

### Modules by role

**Wire-format schemas (Pydantic; serialize to HTTP / JSONB / the generated C# client).**

- `transform.py` — `Float3`, `Float4(x,y,z,w)`, `Transform(translation, rotation)`. Smallest building block; carried in URLs, capture manifests, and localization responses. Quaternion order is xyzw everywhere.
- `camera_config.py` — `ImageOrientation` (the 8 EXIF orientation tags as a Literal) and `PinholeCameraConfig(width, height, orientation, fx, fy, cx, cy)`. Foundational.
- `capture_session_manifest.py` — `RigCameraConfig`, `RigConfig`, `CaptureSessionManifest(axis_convention, rigs, capture_interval_seconds | None)`. The structured payload a phone client uploads alongside the image tar. `ref_sensor: bool` on `RigCameraConfig` identifies the rig origin.
- `reconstruction_options.py` — 24 optional Pydantic fields describing the reconstructor's COLMAP pipeline: pair-generation knobs, RANSAC thresholds, BA toggles, triangulation gates, OPQ params, pose-prior sigma, and `held_out_frame_timestamps` (used by calibration to exclude specific frames so they can be re-localized as held-out queries).
- `reconstruction_metrics.py` — 32 optional fields covering classic SfM metrics, match-verification counts (stereo / same-sensor / cross-sensor splits), map-quality features for the calibration model (`map_image_count`, `map_point_count`, `map_avg_track_length`, `map_bounding_volume_m3`, `map_viewpoint_diversity`), and Umeyama-alignment residuals against ground-truth poses.
- `reconstruction_manifest.py` — `MANIFEST_VERSION = 1` and `Manifest(options, metrics)`. Stored as JSONB in `reconstructions.manifest`. The version constant is stamped onto `row.manifest_version` at write time.
- `localization_metrics.py` — `LocalizationMetrics`, the per-query response payload (inlier ratio, reprojection error, inlier counts, calibrated confidences, 6x6 measurement and PnP covariances, pipeline version). Also exposes `RETRIEVAL_TOP_K_DEFAULT = 12` and `RANSAC_THRESHOLD_DEFAULT = 8.0`. Caller and fallback must read these from one source because the `(reconstruction_id, frame_timestamp, retrieval_top_k, ransac_threshold, pipeline_version)` cache key in `localization_evaluations` relies on agreement.

**Coordinate-frame math.**

- `axis_convention.py` — `AxisConvention` enum (`OPENCV`, `UNITY`) plus four pure-numpy primitives built on a single basis-change matrix `diag(1, -1, 1)`: `change_basis_opencv_from_unity_pose`, `change_basis_unity_from_opencv_pose`, `change_basis_unity_from_opencv_points`, `change_basis_unity_from_opencv_poses` (vectorized, takes xyzw quaternions). OpenCV is `+X right, +Y down, +Z forward`; Unity is `+X right, +Y up, +Z forward`. The enum is a tag, not a dispatch — callers branch on it themselves.

**Image / intrinsics canonicalization.**

- `image_preprocess.py` — the producer/consumer agreement. `canonicalize_image(buffer, orientation)` EXIF-orients then LANCZOS-resizes the shorter side to `LOCAL_FEATURE_RESIZE_SHORTER_SIDE = 1024`. `canonicalize_intrinsics(camera)` applies the matching orientation swap and rescale to `fx/fy/cx/cy` (an 8-branch match where diagonal flips swap width/height *and* fx/fy *and* cx/cy axes). `tile_image(image)` slides a 1024px window with `RETRIEVAL_TILE_OVERLAP_FRACTION = 0.5` overlap. The reconstructor runs all three at map-build time; the localizer runs them at query time. `NumImages`, `MaxTiles`, `NumQueryTiles` `NewType` brands live here.

**On-disk artifact format.**

- `h5.py` — `GLOBAL_DESCRIPTORS_FILE = "global_descriptors.h5"`, `FEATURES_FILE = "features.h5"`, gzip-compressed chunked writers and image-name-keyed readers. The reconstructor writes; the localizer reads. Dataset names `global_descriptor`, `keypoints`, `pq_codes` are constants here.
- `opq.py` — FAISS OPQ matrix and product-quantizer training, encoding, decoding, and IO. File names `opq_matrix.tf` and `pq_quantizer.pq` pinned here. `decode_descriptors` L2-normalizes its reconstructed descriptors (with a `+1e-12` float32 denominator to avoid divide-by-zero).

**Confidence-calibration model.**

- `calibration.py` — `SCHEMA_VERSION = 2`. `RawLocalizationMetrics` and `RawMapMetrics` are the per-query and per-map raw inputs. `Features.compute(localization, map_metrics)` produces a 10-feature vector: `log1p` of inlier / match / image / point counts, `reproj_error_median / image_diagonal`, plus four ratios and diversities. `ToleranceModel` carries `logistic_weights` (Features-shaped), `logistic_intercept`, and an isotonic table (`isotonic_x_breakpoints`, `isotonic_y_breakpoints`). `CalibrationArtifact` bundles a `tight` and `loose` `ToleranceModel`, `sigma_meas_alpha` / `sigma_meas_beta` for the measurement-covariance scaling `Sigma_meas = alpha * Sigma_pnp + beta * I_6`, `loose_min` / `tight_min` floors, and version metadata. `load_global_calibration(path, expected_pipeline_version)` raises `CalibrationLoadError` with a remediation message if the file is missing, the schema version mismatches, or the pipeline version mismatches. `apply_global_calibration(calibration, features)` returns `(tight, loose, True)` — the third element is always literal `True`.

**Inference glue and typing shims (torch-aware).**

- `lightglue.py` — wraps `lightglue.LightGlue`. `Keypoints` / `Descriptors` `NewType`s over `dict[str, Tensor]` (and `*Arrays` variants for numpy input) brand the matcher's positional arguments so pyright catches keypoints/descriptors swaps. `lightglue_match` batches pairs, pads variable-length keypoint sequences, masks out `-1` non-matches.
- `model_wrappers.py` — four thin closures around a "model" callable: extract global descriptor, extract local features, run the matcher on tensors, run the matcher on numpy arrays. `RetrievalDim`, `NumKeypoints`, `LocalDescDim` `NewType` brands.
- `tensor_types.py` — `TT[*Shape]`: a generic subclass of `torch.Tensor` at type-check time, collapsed to plain `torch.Tensor` at runtime via `__class_getitem__`. The runtime collapse is required because `TT[Shape...]` must evaluate inside `cast()` calls and module-level tuple aliases.
- `numpy_ops.py` — shape-typed re-exports of `numpy.zeros` (overloaded for 1D / 2D / 3D), `nonzero`, `compress`, propagating dimension brands through PEP 695 generics.

**Stub.**

- `main.py` — six-line `print("Hello from core!")`. `uv init` scaffolding; not registered as a script.

### Consumer map

Ranked by import volume:

    localizer  (30 sites)  -- localize, build_metrics, map, main, schemas, torch_ops, tests
    reconstructor (22)     -- run_reconstruction, rig, main, metrics_builder, options_builder, tests
    api (13)               -- routers/{localization, reconstructions, leases, capture_sessions}
    zed-capture (4)        -- zed/zed.py (manifest writer)
    scripts                -- fit_calibration, tune_reconstruction

The most-imported leaves are `axis_convention` and `calibration` (8 sites each), `reconstruction_metrics` (7), then `transform`, `capture_session_manifest`, and `camera_config` (6 each).

### Map / query contract

The reason this package is the hub of the stack: every artifact the reconstructor produces is read back by the localizer, byte-for-byte. The constants that pin the contract live in core:

    reconstructor                       localizer
    -------------                       ---------
    h5.write_global_descriptors    -->  h5.read_global_descriptors
    h5.write_features              -->  h5.read_features
    opq.{train,encode,write}       -->  opq.{read,decode}
    image_preprocess.canonicalize  -->  image_preprocess.canonicalize    (same constants, both sides)
    image_preprocess.tile_image    -->  image_preprocess.tile_image
    model_wrappers.RetrievalDim    -->  model_wrappers.RetrievalDim      (phantom shape brand)

Flipping `LOCAL_FEATURE_RESIZE_SHORTER_SIDE`, `RETRIEVAL_TILE_OVERLAP_FRACTION`, an HDF5 dataset name, or an OPQ file name in core without rebuilding every existing map silently degrades retrieval quality without raising.

## Constraints

**One flat package, no `__init__.py` re-exports.** Every consumer reaches into a leaf module, which makes the dependency graph immediately legible from import lines alone: `from core.opq import decode_descriptors` says exactly what the consumer touches. The cost is verbose import blocks at the call site (the localizer's `localize.py` imports from `core.model_wrappers` on two separate lines); the benefit is no parallel public-surface drift between `__init__.py` and the leaves.

**Pydantic on the schema side, pure numpy/torch on the math side.** Schemas need OpenAPI-generability and JSON round-tripping (they end up in C# via `generate-clients` and in Postgres JSONB via the API). Math functions need numpy-array-in / numpy-array-out so they compose with both the reconstructor's training loop and the localizer's per-query path with no Pydantic overhead. The two halves of the package never wrap each other.

**`AxisConvention` is a tag, not a dispatch.** The enum lives on `CaptureSessionManifest` and labels the producer's coordinate system, but core does not branch on it internally — callers do (the reconstructor's `rig.py` calls `change_basis_opencv_from_unity_pose` when the manifest is `UNITY`). Keeping the dispatch out of core means consumers can localize their own coordinate logic without paying for an indirection on every pose.

**Quaternion order is xyzw everywhere.** Matches `scipy.spatial.transform.Rotation.from_quat`'s default and the Unity / glTF convention. No `Float4`-with-wxyz ambiguity.

**`tensor_types.TT[*Shape]` runtime-collapses to `torch.Tensor`.** PEP 695 generic-class syntax is type-checker only, but `TT[Shape...]` appears inside `cast()` calls and module-level tuple aliases that *do* evaluate at runtime. `__class_getitem__` returning plain `torch.Tensor` is what lets both `cast(TT[NumKeypoints, LocalDescDim], ...)` and `LocalFeatureOutput = tuple[TT[NumKeypoints, Literal[2]], TT[NumKeypoints, LocalDescDim]]` work. The same pattern is in `numpy_ops` for ndarray shape brands.

**`NewType` brands on phantom dimension types (`RetrievalDim`, `NumImages`, `MaxTiles`, `NumQueryTiles`, `NumKeypoints`, `LocalDescDim`).** They cost nothing at runtime and let pyright catch axis-order mistakes when the reconstructor's `(NumImages, MaxTiles, RetrievalDim)` tile array is sliced or transposed against the localizer's expectation. The same brand-typing trick is applied to the matcher's positional arguments (`Keypoints` vs. `Descriptors`).

**Manifest fields default to `Optional[X] = None`.** Reconstruction is incremental: the reconstructor fills `ReconstructionMetrics` field by field during a multi-minute run, and the API accepts partial `ReconstructionOptions` blobs from clients that don't want to specify every COLMAP knob. The cost is that downstream readers must None-check; the alternative — fresh-write defaults — would either fabricate misleading numbers or split the model into write-time and read-time variants.

**The torch / lightglue dependency lives in core but is not declared in `pyproject.toml`.** A `DEP003` deptry exemption documents the asymmetry. The canonical PyTorch dep lives in `neural-networks` behind conflicting `cpu` / `cuda` / `rocm` extras, so declaring bare `torch` here would conflict. Consumers that touch the torch-aware modules (`lightglue`, `model_wrappers`, `tensor_types`) must also depend on `neural-networks` with the matching extra; the API does not depend on `neural-networks` and never imports those modules.

**Calibration is the only place with a real algorithm and the only place with a real version check.** `load_global_calibration` raises loudly on schema or pipeline mismatch. Every other versioned thing in core (notably `MANIFEST_VERSION`) trusts the caller. The asymmetry is deliberate where the calibration artifact is concerned — a wrong-version calibration silently miscalibrates every confidence in production — but is a known gap for the manifest path.

## See also

- `docker/SPEC.md` -- the service mesh that consumes these types. Core is the vocabulary on the arrows between services; that SPEC describes the arrows.
- `scripts/src/scripts/fit_calibration.py` -- the producer of `config/calibration/global.json`. Reads `core.calibration`, `core.capture_session_manifest`, and `core.localization_metrics`'s defaults.
- `packages/generated/` -- the OpenAPI client packages (Python and C#) generated from API routes that respond with `core` schemas. A schema change here requires running `generate-clients`.
