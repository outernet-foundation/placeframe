# Code review — open items

> Captured 2026-05-02 during chunk 4 of Phase 3. Audit of `scripts/src/scripts/fit_calibration.py` and `scripts/src/scripts/test_placeframe_e2e.py`. Items below are real but were judged not-obvious-enough to land unilaterally; revisit when next touching either file. The cleanups that DID land are summarized at the bottom.

## 1. `_build_feature_row`'s eight Optional checks

`fit_calibration.py:128–137` — every check except `is_indoor` defends against pre-chunk-2 reconstructions whose manifests lack the map-quality fields. The intent doc explicitly calls this out as a known risk (`e2e-and-calibration-intent.md` "Risks and unknowns" → "Pre-existing reconstructions lack the new metrics").

The defense exists, but the silent skip means data drift (e.g. a chunk-5 schema change that nulls a field) shows up as "fewer rows than expected" rather than a loud error. Could swap silent-skip for a one-time warning on the first skipped row, citing the field that was missing.

Useful if you're worried about silent drift; fine as-is otherwise.

## 2. Manual pose inversion in the harness now that `pytransform3d` is in scope

`test_placeframe_e2e.py` `_localize_and_label`:
```python
estimated_camera_position = -cam_from_map_rotation.T @ cam_from_map_translation
estimated_world_from_camera = cam_from_map_rotation.T
```

`pytransform3d.invert_transform` could replace this. Tradeoff: the manual form is one-line algebra readers can follow without knowing pytransform3d; the library call is shorter but adds a small reading overhead.

Marginal — flagged but not obviously better either way.

## What already landed (for traceability)

Cleanups folded into the chunk 4 commit (`8bc86671`):

1. Removed dead `sign(len(results)) == 0` check in `main()` and the now-unused `sign` numpy import.
2. Hoisted `from json import loads` out of `CalibrationArtifact.read` (and the manual dict-building in `read`/`write`).
3. Replaced manual JSON dict construction with `model_dump_json(by_alias=True)` / `model_validate_json` using `Field(validation_alias=AliasChoices("global", "global_"), serialization_alias="global")`. The `validation_alias`/`serialization_alias` split (rather than plain `alias="global"` + `populate_by_name=True`) is what lets pyright keep `global_=...` as the constructor parameter name; plain `alias="global"` makes pyright reject `cls(global_=...)`.
4. Removed redundant `.reshape(len(...), ...)` no-ops on the non-empty branches of the `pnp_cov_arr` / `residual_arr` constructions; the empty-branch reshapes stayed because `asarray([])` defaults to shape `(0,)`.
5. Extracted Phase 6 per-iteration body into `_localize_and_label(...)` and collapsed the three `results.localizations.append(loc_result)` sites to a single append at the call site. ~80 lines moved into the helper, Phase 6's loop body shrank to a single call.

Items considered but explicitly not landing (won't touch):

- `LocalizationResult` carrying `err_t_m` + `err_r_deg` + `se3_residual` — three representations of the same residual. Kept as-is; separability of concerns wins.
- `_prepare_capture` opening the tar twice. Kept as-is; trivial I/O on a local file.
