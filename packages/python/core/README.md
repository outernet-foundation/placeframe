# placeframe-core

Domain vocabulary for Placeframe's backend: Pydantic wire schemas (transforms, camera configs, capture manifests, reconstruction options/metrics), OpenCV↔Unity coordinate-frame primitives, image and intrinsics canonicalization, HDF5/FAISS-OPQ artifact formats, and the global confidence-calibration model. Distribution name `placeframe-core`, import name `placeframe_core`.

Consumed by the `api`, `lease-server`, `localizer`, `reconstructor`, `zed-capture`, and `scripts` packages in the [placeframe](https://github.com/outernet-foundation/placeframe) repo. Versions are published to PyPI from per-package git tags; the committed `pyproject.toml` version is a permanent `0.0.0.dev0` sentinel patched at publish time.
