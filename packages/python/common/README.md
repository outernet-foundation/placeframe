# placeframe-common

Shared Python utilities for Placeframe's backend services: boto/S3 helpers, Docker SDK helpers, Litestar middleware, and JWT utilities. Distribution name `placeframe-common`, import name `placeframe_common`.

Consumed by the `api`, `lease-server`, `localizer`, `reconstructor`, `database-manager`, and `scripts` packages in the [placeframe](https://github.com/outernet-foundation/placeframe) repo, and by the [placeframe-capture-tool](https://github.com/outernet-foundation/placeframe-capture-tool) repo via PyPI. Versions are published to PyPI from per-package git tags; the committed `pyproject.toml` version is a permanent `0.0.0.dev0` sentinel patched at publish time.
