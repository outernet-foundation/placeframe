# Docker Build Digest Reproducibility

Research conducted 2026-03-20. Context: evaluating whether `.env.lock` (Docker image digests) can be committed locally like a package lock file, with CI verifying rather than generating.

## The question

Can `docker buildx bake` produce byte-identical image digests across different machines, so that a developer can build locally, commit the digest, and CI can verify the build produces the same digest? What BuildKit features exist for this, and what are the practical barriers?

## How image digests work

For identical digests, ALL of the following must match:

- **Layer digests** — sha256 of compressed tar per layer. Affected by file content, permissions, timestamps, and file ordering within the tar.
- **Image config digest** — sha256 of JSON config blob. Contains `created` timestamp, layer diff IDs, history entries, arch/OS/variant fields.
- **Image manifest digest** — sha256 of JSON manifest referencing config + layers. This is what `@sha256:...` pins in image references.

If all layers match and the config matches, the manifest matches. Attestations (provenance/SBOM) are stored as additional manifest entries and must be disabled or they break index-level reproducibility on every build.

## BuildKit's reproducibility features

| Feature | Min version | What it controls |
|---|---|---|
| `SOURCE_DATE_EPOCH` env var | BuildKit v0.11 / Buildx v0.10 | `created` fields in image config, history, annotations |
| `rewrite-timestamp=true` exporter option | BuildKit v0.13 | Rewrites file timestamps *inside layers* to match epoch |
| `--provenance=false` | Buildx v0.10+ | Disables provenance attestation (non-reproducible by design) |
| `--sbom=false` | Buildx v0.10+ | Disables SBOM attestation |

**`SOURCE_DATE_EPOCH`** is auto-propagated from the client environment by buildx. Set it to a deterministic value (e.g., `git log -1 --pretty=%ct`) and metadata timestamps become reproducible.

**`rewrite-timestamp=true`** is the critical addition from BuildKit v0.13. Without it, `SOURCE_DATE_EPOCH` only controls metadata — file timestamps inside layers (from `COPY`, `RUN`, etc.) remain non-deterministic. With it, all file mtimes in all layers are clamped to the epoch.

**Provenance is non-reproducible by design.** It embeds per-build timestamps and builder identity. The current setup already uses `--provenance=false --sbom=false`, which is correct and necessary.

### Using these with `docker buildx bake`

`SOURCE_DATE_EPOCH` propagates automatically from the environment. `rewrite-timestamp` is set via the output attribute:

```hcl
target "myservice" {
  output = ["type=image,name=registry/image,push=true,rewrite-timestamp=true"]
}
```

Or via CLI override: `docker buildx bake --set "*.output=type=image,rewrite-timestamp=true"`

### Known bugs

- `rewrite-timestamp` + `COPY --link` broken in BuildKit v0.13.0–v0.13.1, fixed in v0.13.2
- `rewrite-timestamp` conflicts with `unpack=false` exporter option (through BuildKit v0.17.3)
- BuildKit v0.20.0 added `"variant": "v8"` field to ARM64 image configs, breaking cross-version reproducibility (fixed in PR #5776)
- `BUILDKIT_INLINE_CACHE=1` breaks reproducibility due to non-deterministic ordering of cache metadata entries (unfixed since 2022)

## The real problem: Dockerfile non-determinism

A 2026 academic study ("It's Not Just Timestamps", arxiv 2602.17678) analyzed 2,000 GitHub repos:

- **2.7%** of Dockerfiles are reproducible by default
- **21.3%** become reproducible with `SOURCE_DATE_EPOCH` + `rewrite-timestamp`
- **78.7% remain non-reproducible** even with all infrastructure fixes

The dominant sources beyond timestamps:

| Source | Prevalence | Example |
|---|---|---|
| File ordering in tar layers | 78.1% | `RUN apt-get install` creates files in non-deterministic order |
| System logs | 43.3% | `/var/log/apt/*`, `/var/log/dpkg.log` contain timestamps and ordering |
| Caches and databases | 36.8% | npm cache, pip cache, fontconfig cache |
| Compiled artifacts | 20% | `.pyc` files embed timestamps |
| Application-specific | 13% | Random seeds, generated UUIDs |

### Package manager non-determinism

**apt-get**: Does not honor `SOURCE_DATE_EPOCH` for package selection. Floating repos mean `apt-get install python3` resolves to different versions on different days. Fix: use [repro-sources-list.sh](https://github.com/reproducible-containers/repro-sources-list.sh) to pin apt sources to `snapshot.debian.org/archive/debian/<timestamp>/`. Also creates non-deterministic logs and caches that must be deleted.

**pip**: Embeds timestamps in caches. Fix: use `--no-cache-dir` and `PYTHONDONTWRITEBYTECODE=1`. Pin all versions with hashes (`--require-hashes`).

**npm**: Cache contains timestamps. Fix: `npm ci` with clean cache, or delete cache after install.

### File ordering

This is the biggest barrier. When `RUN apt-get install -y foo` creates files across multiple directories, the order those files appear in the tar layer depends on filesystem iteration order, which varies by kernel version, filesystem, and inode allocation. There is no BuildKit-level fix for this — it would require tar layer creation to sort entries deterministically, which is an open feature request.

## Assessment

**Full reproducibility is not practically achievable for your Dockerfiles.** The 78.7% failure rate is dominated by file ordering in tar layers, which has no BuildKit-level fix. Your services install system packages (apt), Python packages (pip/uv), and various tools — every `RUN` instruction that touches the filesystem is a source of non-deterministic file ordering.

You could theoretically achieve reproducibility by:
1. Setting `SOURCE_DATE_EPOCH` + `rewrite-timestamp=true`
2. Pinning apt sources to snapshot.debian.org
3. Pinning every package version (including transitive)
4. Deleting all caches, logs, and `.pyc` files
5. Ensuring identical BuildKit versions everywhere
6. Using `--no-cache` on every build

But even then, file ordering in tar layers would likely break it. And the maintenance burden of snapshot-pinned apt sources and fully-pinned transitive dependencies would be substantial.

**Recommendation: keep the current architecture.** CI generates `.env.lock` (it's the only environment that builds and pushes to GHCR), developers use `.env.local.lock` for local builds. The digest in `.env.lock` is the registry manifest digest from GHCR, which is authoritative and deterministic by definition (same push = same digest). This is not the same problem as package lock files — package resolution is a pure function of inputs, Docker builds are not.

The `.env.lock` question is a red herring for the CI/CD split. What matters for T1 is that `.env.lock` is already committed to dev by the CI `commit` job, and main gets it via fast-forward. No changes needed.

## Sources

- [Docker Docs: Reproducible builds](https://docs.docker.com/build/ci/github-actions/reproducible-builds/)
- [BuildKit build-repro.md](https://github.com/moby/buildkit/blob/master/docs/build-repro.md)
- [arxiv 2602.17678: "It's Not Just Timestamps: A Study on Docker Reproducibility"](https://arxiv.org/html/2602.17678v1)
- [Akihiro Suda: Bit-for-bit reproducible builds with Dockerfile](https://medium.com/nttlabs/bit-for-bit-reproducible-builds-with-dockerfile-7cc2b9faed9f)
- [Akihiro Suda: DockerCon 2023 Reproducible Builds](https://medium.com/nttlabs/dockercon-2023-reproducible-builds-with-buildkit-for-software-supply-chain-security-0e5aedd1aaa7)
- [BuildKit #1876: BUILDKIT_INLINE_CACHE non-determinism](https://github.com/moby/buildkit/issues/1876)
- [BuildKit #5774: v0.20.0 ARM64 variant field](https://github.com/moby/buildkit/issues/5774)
- [BuildKit #4746: rewrite-timestamp + COPY --link](https://github.com/moby/buildkit/issues/4746)
- [Buildx #2733: rewrite-timestamp + unpack conflict](https://github.com/docker/buildx/issues/2733)
- [moby/moby #48391: containerd cached build digest divergence](https://github.com/moby/moby/issues/48391)
- [reproducible-containers/repro-sources-list.sh](https://github.com/reproducible-containers/repro-sources-list.sh)
