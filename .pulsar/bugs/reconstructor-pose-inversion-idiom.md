# Reconstructor hand-rolls SE(3) inverse at three sites instead of calling `Rigid3d.inverse()`

**Severity**: low — readability only. No behavior change; the hand-rolled math is arithmetically correct.

**Location**: Three sites in the reconstructor compute `world_from_X = X_from_world⁻¹` as `rot.matrix().T` plus `-rot.matrix().T @ trans` instead of `pycolmap.Rigid3d.inverse()`:

- `docker/reconstructor/src/reconstructor/colmap.py` — Umeyama diagnostic site, `rig_from_world` → camera center.
- `docker/reconstructor/src/reconstructor/colmap.py` — npz writer site, `rig_from_world` → `world_from_rig` for export.
- `docker/reconstructor/src/reconstructor/metrics_builder.py` — `rig_from_world` → viewing-direction column for `map_viewpoint_diversity`.

**Symptom**: A reader scanning these sites has to recognize the SE(3) inverse formula by sight (`R.T`, `-R.T @ t`) and trust the sign + transpose are right. The `.inverse()` call would read as "obviously the inverse."

**Mechanism**: `pycolmap.Rigid3d` exposes `.inverse()`, which returns a new `Rigid3d` whose `.rotation.matrix()` and `.translation` are the inverted components. The three sites predate the inverse call being used elsewhere in the file; they were written by reaching into the components and applying the formula directly.

**Fix sketch**: At each site, replace the hand-rolled formula with `world_from_X = X_from_world.inverse()` and read `.rotation.matrix()` / `.translation` off it. Single drive-by commit covering all three sites. No behavior change; no test changes; same arithmetic, more legible call.

**Verification**: Per-site, write the hand-rolled and `.inverse()`-based results into matching arrays and assert elementwise equality on a representative reconstruction before committing the cleanup, then remove the assertion.
