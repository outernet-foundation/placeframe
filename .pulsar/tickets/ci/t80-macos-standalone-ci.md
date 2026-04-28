---
id: T80
title: "macOS standalone CI builds"
status: design-needed
depends_on: [T7]
---

# T80: macOS standalone CI builds

## Goal

Add macOS standalone builds to the Unity CI workflow.

## Context

macOS IL2CPP builds can only be produced natively on macOS — same cross-compilation restriction as Windows (see T75 research). Unlike Windows and Linux, macOS has no Docker option at all — Apple's licensing prohibits running macOS in containers on non-Apple hardware. GitHub's `macos-latest` runners are bare VMs.

This means macOS CI builds will necessarily run without container isolation, losing the reproducibility that GameCI Docker images provide for Linux builds. Every macOS Unity CI setup in the ecosystem uses bare runner + Unity install (cached or fresh). This is a known trade-off with no workaround.

The same Unity licensing constraints from T75 apply: macOS builds would need to share the 2-seat Personal license, requiring serialization with other CI builds.

## Key files

- `.github/workflows/unity.yml` — add macOS build jobs
- `scripts/src/scripts/build_unity.py` — macOS platform support

## Next step

**Design needed.** Determine which projects need macOS standalone builds and whether the no-container trade-off is acceptable. T75 (Windows IL2CPP) should be resolved first — the licensing serialization strategy chosen there will directly constrain macOS builds.
