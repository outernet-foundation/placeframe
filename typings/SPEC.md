# typings/

## What this is

Hand-vendored `.pyi` stub overrides for third-party C-extension packages whose upstream type information is wrong or missing. Pyright/basedpyright reads `./typings/` as `stubPath` by default, ahead of any stubs the wheel ships, so anything in this tree shadows the package's bundled stubs. The point is to keep static analysis honest when an upstream wheel and its bundled stubs disagree with each other.

## Shape

```
typings/
├── multipart.pyi       # python-multipart, no upstream stubs
├── pycolmap/           # upstream stubs ship stale
├── pyzed/              # Stereolabs ZED SDK Python bindings, no upstream stubs
└── usb1/               # libusb1, no upstream stubs
```

Two categories live here:

1. **Packages that don't ship stubs at all.** `multipart`, `pyzed`, `usb1`. These exist because the package is untyped upstream and we want imports of it to type-check. They're stable and rarely change.
2. **Packages whose shipped stubs are wrong.** `pycolmap`. The wheel includes its own `.pyi` files, but those stubs drift from the actual C++ binding between releases. Our override is regenerated from the live binding via `pybind11-stubgen` so the signatures match runtime.

## Constraints

### Why we override pycolmap even though it ships stubs

`pycolmap` bundles a `_core/__init__.pyi` inside the wheel. That file is produced by `pybind11-stubgen`, but upstream's release process bakes the stubs from an older binary and ships them alongside the newer one — so the stub and the binding can disagree on method signatures. Two effects make this dangerous:

- Static analysis silently lies. Basedpyright validates calls against the stub; if the stub still describes an old signature, the type checker happily approves a call that the runtime will reject with a `pybind11::cast` error.
- The breakage surfaces only in production, in whichever code path first hits the affected method. There is no compile-time warning.

We avoid this by regenerating the stubs ourselves from the *installed* binding and committing them under `typings/pycolmap/`. The runtime `__doc__` / `__signature__` produced by the active C extension is the source of truth, not the wheel's pre-baked `.pyi`.

### Regenerating pycolmap stubs

After bumping pycolmap in `docker/localizer/pyproject.toml` and `docker/reconstructor/pyproject.toml`:

```bash
rm -rf typings/pycolmap
uv run --package placeframe-reconstructor pybind11-stubgen pycolmap \
  --numpy-array-wrap-with-annotated -o typings/
```

Notes:

- `--package placeframe-reconstructor` is what makes `pybind11-stubgen` resolvable — it's declared as a dev dep there (and pinned to the `sarlinpe/pybind11-stubgen` fork in the root `pyproject.toml`, which carries fixes for pycolmap-specific quirks).
- `--numpy-array-wrap-with-annotated` matches the style of the existing stubs: numpy arrays render as `typing.Annotated[NDArray[float64], "[3, 1]"]` instead of the alternative `NDArray[tuple[Literal[3], Literal[1]], dtype[float64]]` form.
- The stubgen run emits `[ERROR] Invalid expression` warnings for a handful of methods whose default values are raw C++ enums (`<FeatureMatcherType.SIFT_BRUTEFORCE: 0>`) or whose return types reference Ceres types (`ceres::Problem`). These are pybind11 binding quality issues upstream — stubgen falls back to `...` placeholders and exits 0. The warnings are non-fatal and the produced stubs are correct for everything we actually call.
- **After regen, post-process `typings/pycolmap/_core/__init__.pyi`:** the fork emits `os.PathLike` (instead of the parameterized `os.PathLike[str]`) and silently drops the matching `import os` from the file header. Both are stubgen bugs that fail basedpyright in strict mode. Add `import os` to the import block, then do an exact-text replace of `os.PathLike | str | bytes` → `os.PathLike[str] | str | bytes` across the file. If the fork is ever updated and starts emitting both correctly, drop this post-step.
- Reviewing the diff after a regen is worthwhile: any signature change you didn't expect is either a real upstream API break (find and fix the call site) or noise (whitespace / ordering / overload reshuffling).

### Why basedpyright didn't catch the 4.0.4 `write_pose_prior` regression

The pycolmap 4.0.4 bump changed `Database.write_pose_prior` from `(image_id, pose_prior)` to `(pose_prior, use_pose_prior_id=False)`, with the image binding now travelling inside `PosePrior.corr_data_id`. The check that should have surfaced this at type-check time didn't, because:

- Our committed `typings/pycolmap/` predated the bump and still declared the old 2-arg signature.
- The pycolmap 4.0.4 wheel's *own* bundled `_core/__init__.pyi` also still declared the old signature — they shipped pre-baked stubs from an older binary.

Both stub sources agreed with the call site and disagreed with the runtime. Static analysis cannot save you when the stubs themselves are stale relative to the binding. The fix is to make stub regeneration a mandatory step of the pycolmap version bump — see the command above.

## See also

- Root `pyproject.toml` pins the `pybind11-stubgen` fork at `sarlinpe/pybind11-stubgen` (branch `sarlinpe/fix-2024-08`). That fork carries pycolmap-aware fixes from one of the pycolmap maintainers; replacing it with mainline pybind11-stubgen produces noisier output.
