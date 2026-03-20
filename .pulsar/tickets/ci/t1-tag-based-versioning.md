---
id: T1
title: Replace versions.json with per-package git tags
status: plan-needed
constraint: build/src/build_scripts/placeframe/ci/CLAUDE.md#ci-commit-free-invariant
violators:
  - build/src/build_scripts/placeframe/ci/publish_packages.py
  - build/src/build_scripts/placeframe/ci/create_release.py
  - build/src/build_scripts/placeframe/ci/commit_artifacts.py
  - build/versions.json
  - packages/unity/Placeframe/Assets/Package/Core/package.json
  - packages/unity/Placeframe/Assets/Package/ARFoundation/package.json
  - packages/unity/Placeframe/Assets/Package/MagicLeap/package.json
depends_on: []
plan: t1-plan.md
---

`publish_packages.py` uses hash-based change detection and reads/writes `versions.json`. `create_release.py` bumps version in `versions.json` and commits. `commit_artifacts.py` commits `versions.json` and patched `package.json` files.

Should use git tags for versioning (`git tag --list "{prefix}*" --sort=-v:refname`), `git diff --quiet` for change detection, ephemeral `package.json` patching (patch before `npm publish`, restore immediately after), and `0.0.0-local` as permanent `package.json` version. Bootstrap tags must be created from current `versions.json` values before merging.

Tag naming: `core-v1.0.3`, `arfoundation-v1.0.3`, `release-v0.2.0`, `outernet-client-v0.1.9`, etc.
