# ORAS / OCI Registry Caching for GitHub Actions CI

Research conducted 2026-03-04. Context: evaluating ORAS (OCI Registry As Storage) as an alternative to `actions/cache` for caching multi-GB Unity `Library/` directories in CI.

## 1. ORAS CLI in GitHub Actions

### Installation

The official action is [`oras-project/setup-oras`](https://github.com/oras-project/setup-oras):

```yaml
steps:
  - uses: oras-project/setup-oras@v1
  # Installs default version (currently 1.2.2)

  - uses: oras-project/setup-oras@v1
    with:
      version: 1.2.2
  # Pin a specific version (no 'v' prefix)
```

Source: [setup-oras on GitHub Marketplace](https://github.com/marketplace/actions/setup-oras)

### Authentication with ghcr.io using GITHUB_TOKEN

```yaml
- name: Login to GHCR with ORAS
  run: echo "${{ secrets.GITHUB_TOKEN }}" | oras login ghcr.io --username "${{ github.actor }}" --password-stdin
```

Alternatively, if `docker/login-action` has already been used in the workflow, ORAS can use Docker's credential store (it reads `~/.docker/config.json`).

The workflow must declare `packages: write` permission:

```yaml
permissions:
  packages: write
```

When using `GITHUB_TOKEN`, data transfer to/from ghcr.io is **free and does not count against the repository's usage quota**. This is a major advantage over `actions/cache`, which uses GitHub's cache service with its own storage limits.

Sources:
- [Working with the Container registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [GitHub Packages billing](https://docs.github.com/en/billing/concepts/product-billing/github-packages)
- [Storing Blobs on the GitHub Container Registry](https://www.aahlenst.dev/blog/storing-blobs-on-github-container-registry/)

## 2. Pre-built GitHub Actions for ORAS caching

**There are no pre-built cache-save/cache-restore GitHub Actions wrapping ORAS.** The ORAS project provides only [`oras-project/setup-oras`](https://github.com/oras-project/setup-oras) (CLI installer). There is no `oras-project/cache-action` or community equivalent that provides the `actions/cache`-style key/restore-keys pattern.

The closest community project is [`heliconialabs/oras-pull`](https://github.com/heliconialabs/oras-pull), which only wraps the pull side.

**Implication**: We need to write our own save/restore steps using raw `oras push` / `oras pull` commands (or wrap them in a composite action). This is straightforward — ORAS's CLI is simple enough that a wrapper action adds little value.

## 3. ORAS push/pull syntax

### Push a directory

```bash
# Push a directory — ORAS automatically tars it and applies gzip compression
oras push ghcr.io/myorg/myrepo/cache/unity-library:myproject-linux64 \
  --artifact-type application/vnd.placeframe.unity-cache.v1 \
  ./Library/:application/vnd.oci.image.layer.v1.tar+gzip
```

Key behaviors:
- **Directories are automatically tarred** by ORAS before upload. The `./dir/` syntax (trailing slash) triggers directory mode.
- **Default media types**: Files default to `application/vnd.oci.image.layer.v1.tar`. Directories default to `application/vnd.oci.image.layer.v1.tar+gzip` (tar + gzip compressed).
- **Custom media types** can be specified per file/directory: `./path:custom/media+type`
- **Multi-file push** creates separate layers, enabling deduplication: `oras push ref:tag file1 file2 dir/`
- **Concurrency** defaults to 5 parallel uploads, configurable with `--concurrency N`

### Pull to a directory

```bash
oras pull ghcr.io/myorg/myrepo/cache/unity-library:myproject-linux64 -o ./
```

The `-o` flag specifies the output directory. Directories are automatically un-tarred.

### Tagging strategy for cache keys

OCI tags are the equivalent of cache keys. Tags can contain alphanumeric characters, hyphens, underscores, and dots. Forward slashes are NOT allowed in tags but ARE allowed in repository paths.

Recommended approach for Unity Library caches:

```
ghcr.io/{owner}/{repo}/cache/unity-library:{project}-{platform}-{hash}
```

Example:
```
ghcr.io/placeframe/placeframe/cache/unity-library:mapregistrationtool-linux64-abc123
```

Where `{hash}` is derived from `hashFiles('apps/MapRegistrationTool/Assets/**', 'apps/MapRegistrationTool/Packages/**', 'apps/MapRegistrationTool/ProjectSettings/**')`.

**Unlike `actions/cache`, there are no restore-keys for prefix matching.** You must implement fallback logic yourself, e.g. by trying tags in order:

```bash
# Try exact match first, then fallback to platform-only tag
oras pull ghcr.io/.../cache:project-platform-${HASH} -o ./ 2>/dev/null \
  || oras pull ghcr.io/.../cache:project-platform-latest -o ./ 2>/dev/null \
  || echo "No cache found, starting fresh"
```

To support this, always push to both the exact tag AND a `latest`-style fallback tag:

```bash
oras push ghcr.io/.../cache:project-platform-${HASH} ./Library/
oras tag ghcr.io/.../cache:project-platform-${HASH} project-platform-latest
```

`oras tag` is a server-side operation (no re-upload).

Sources:
- [ORAS Pushing and Pulling guide](https://oras.land/docs/how_to_guides/pushing_and_pulling/)
- [oras push command reference](https://oras.land/docs/commands/oras_push/)
- [Universal Packages on GitHub With ORAS](https://www.kenmuse.com/blog/universal-packages-on-github-with-oras/)

## 4. Compression

### What ORAS does by default

- **Directories** are tarred and gzip-compressed automatically. The resulting layer has media type `application/vnd.oci.image.layer.v1.tar+gzip`.
- **Individual files** are stored as uncompressed tar layers by default.
- **There are no ORAS flags to control compression algorithm or level.** The `oras push` command has no `--compression`, `--zstd`, or similar flags.

### Pre-compressing with zstd

To use zstd (which is significantly faster than gzip for multi-GB archives), pre-compress manually and push the resulting tarball as a single file with a custom media type:

```bash
# Compress with zstd (multithreaded, level 3 = good speed/ratio balance)
tar -cf - Library/ | zstd -T0 -3 -o library-cache.tar.zst

# Push as a single file (not a directory — avoids ORAS's gzip)
oras push ghcr.io/.../cache:project-platform-${HASH} \
  --artifact-type application/vnd.placeframe.unity-cache.v1 \
  library-cache.tar.zst:application/vnd.placeframe.cache.layer.v1+zstd
```

Restore:

```bash
oras pull ghcr.io/.../cache:project-platform-${HASH} -o /tmp/cache/
zstd -d -T0 /tmp/cache/library-cache.tar.zst --stdout | tar -xf - -C ./
```

### Performance comparison for multi-GB archives

For a ~3 GiB Unity Library directory (typical for IL2CPP projects):

| Metric | gzip (ORAS default) | zstd -3 (pre-compressed) | zstd -1 (fastest) |
|---|---|---|---|
| Compression speed | ~50 MB/s (single-threaded) | ~500 MB/s (multi-threaded, 2-core runner) | ~700 MB/s |
| Decompression speed | ~250 MB/s | ~1000 MB/s | ~1000 MB/s |
| Compression ratio | ~2.5-3x | ~2.5-3x | ~2.2-2.5x |
| Estimated compress time (3 GiB) | ~60s | ~6s | ~4s |
| Estimated decompress time (3 GiB) | ~12s | ~3s | ~3s |

**zstd is the clear winner for CI caching.** The compression speed advantage is 10x due to multithreading and algorithm efficiency. Decompression is 3-4x faster. Compression ratio is comparable.

GitHub-hosted runners have 2 vCPUs (`ubuntu-latest`), so `zstd -T0` will use 2 threads. Even with just 2 threads, zstd massively outperforms single-threaded gzip.

Sources:
- [Building Images: Gzip vs Zstd](https://depot.dev/blog/building-images-gzip-vs-zstd)
- [zstd vs gzip performance comparison](https://jothiprasath.com/blog/gzip-vs-zstd/)
- [Zstandard home page](http://facebook.github.io/zstd/)

## 5. ghcr.io limits

### Per-layer size limit

**10 GB per layer.** This is the binding constraint. A 25 GiB image split across multiple <10 GB layers works. A single layer >10 GB fails.

For Unity caches: a typical `Library/` directory is 2-5 GiB uncompressed, compressing to 1-2 GiB. Well within limits.

### Upload timeout

**10 minutes per upload.** On GitHub-hosted runners (network bandwidth to ghcr.io is fast since both are in Azure), multi-GB uploads typically complete in 1-3 minutes.

### Storage and data transfer (billing)

| Plan | Included Storage | Included Data Transfer/month |
|---|---|---|
| GitHub Free | 500 MB | 1 GB |
| GitHub Pro | 2 GB | 10 GB |
| GitHub Team | 2 GB | 10 GB |
| GitHub Enterprise Cloud | 50 GB | 100 GB |

**Critical exceptions:**
- **Public repositories**: Packages (including container images) are **free** — no storage or data transfer charges.
- **GITHUB_TOKEN transfers**: Data transferred using `GITHUB_TOKEN` in GitHub Actions (both hosted and self-hosted runners) **does not count against the repository's data transfer quota**.
- **Container registry specifically**: GitHub states "Container image storage and bandwidth for the Container registry is currently free" — though they reserve the right to change this with notice.

**For Placeframe**: If the repository is public, there are effectively no limits. If private, the "currently free" container registry policy plus the GITHUB_TOKEN exemption means this is also free in practice.

### Retention / garbage collection

**There is no automatic garbage collection of container images on ghcr.io.** Images persist indefinitely unless manually deleted. Old cache tags can be cleaned up via:

```bash
# List all tags
oras repo tags ghcr.io/myorg/myrepo/cache/unity-library

# Delete old tags (requires delete:packages permission)
oras manifest delete ghcr.io/myorg/myrepo/cache/unity-library:old-tag
```

Or via the GitHub Packages web UI / API.

**Recommendation**: Implement a cleanup step in CI or a scheduled workflow that deletes cache artifacts older than N days.

Sources:
- [ghcr.io max file size discussion](https://github.com/orgs/community/discussions/77429)
- [GitHub Packages billing](https://docs.github.com/en/billing/concepts/product-billing/github-packages)
- [Working with the Container registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Rate limits discussion](https://github.com/orgs/community/discussions/49671)

## 6. Alternative approaches (non-ORAS)

### `actions/cache` (the default)

- **New limit as of November 2025**: repositories can now exceed 10 GB with paid plans (Pro/Team/Enterprise). Free tier remains at 10 GB per repository.
- **LRU eviction**: when the cache exceeds the configured limit, least-recently-used entries are evicted.
- **Main limitation for Unity**: 5 builds x 3 GiB compressed Library caches = 15 GiB. Exceeds the free 10 GB limit. With the new paid expansion, this becomes feasible but adds cost.
- **Performance**: `actions/cache` uses Azure Blob Storage under the hood with chunked upload/download. Performance is decent but not exceptional for multi-GB files.

Source: [GitHub Actions cache size can now exceed 10 GB per repository](https://github.blog/changelog/2025-11-20-github-actions-cache-size-can-now-exceed-10-gb-per-repository/)

### Docker Buildx registry cache

```yaml
- uses: docker/setup-buildx-action@v3
- uses: docker/build-push-action@v6
  with:
    cache-from: type=registry,ref=ghcr.io/myorg/myrepo/buildcache:key
    cache-to: type=registry,ref=ghcr.io/myorg/myrepo/buildcache:key,mode=max
```

- Only works for Docker image build layers, not arbitrary files.
- Useful for caching Docker build steps (e.g., package installation layers) but not for caching Unity Library directories.
- Already used implicitly in Placeframe's build workflow via BuildKit.

Sources:
- [Docker GitHub Actions cache](https://docs.docker.com/build/cache/backends/gha/)
- [Cache management with GitHub Actions](https://docs.docker.com/build/ci/github-actions/cache/)

### `crane` (google/go-containerregistry)

`crane` can push/pull OCI artifacts similar to ORAS:

```bash
# Push a tarball as an OCI image layer
crane append -f library-cache.tar.zst -t ghcr.io/myorg/myrepo/cache:key
# Pull it back
crane pull ghcr.io/myorg/myrepo/cache:key - | tar xf -
```

- Less ergonomic than ORAS for file/directory operations (designed for container images, not arbitrary artifacts).
- No official GitHub Action for installation.
- **Not recommended** — ORAS is purpose-built for this use case.

### `skopeo`

- Designed for copying images between registries and inspecting manifests.
- Can theoretically be used for cache operations but requires manual manifest construction.
- Pre-installed on `ubuntu-latest` runners.
- **Not recommended** — too low-level for simple caching.

Source: [skopeo on GitHub](https://github.com/containers/skopeo)

### S3/GCS/Azure Blob external cache

- Unlimited storage, no per-layer limits.
- Requires cloud credentials (secret management overhead).
- Options like [`runs-on/cache`](https://runs-on.com/caching/s3-cache-for-github-actions/) provide drop-in replacements for `actions/cache` backed by S3.
- **Overkill for Placeframe** — ghcr.io provides free storage and the ORAS workflow is simpler.

## 7. Authentication inside Docker containers (GameCI/unityci images)

### How `GITHUB_TOKEN` works in container jobs

When a GitHub Actions job uses `container:` to run inside a Docker image:

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    container:
      image: unityci/editor:ubuntu-6000.0.66f1-linux-il2cpp-3
    steps:
      - name: Login to GHCR
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: echo "$GITHUB_TOKEN" | oras login ghcr.io --username "${{ github.actor }}" --password-stdin
```

Key points:
- **`GITHUB_TOKEN` is NOT automatically available as an environment variable inside the container.** It must be explicitly passed via the `env:` key on the step or job level.
- **`secrets.GITHUB_TOKEN`** is always available as a secret context expression — you just need to map it to an environment variable.
- **`github.actor`** and other context expressions work normally inside container jobs — they are injected by the runner, not the container.
- **The `docker/login-action` step sets up `~/.docker/config.json`**, which persists across steps in the same job. If you use `docker/login-action` before ORAS steps, ORAS will automatically pick up the credentials from Docker's config. However, `docker/login-action` runs on the runner host, not inside the container — so for `container:` jobs, use `oras login` directly.

### Installing ORAS inside a container job

The `oras-project/setup-oras` action is a TypeScript action that runs on the runner. For `container:` jobs on Linux, it should work because the runner mounts the tools directory into the container. However, if there are issues, ORAS can be installed manually:

```yaml
- name: Install ORAS
  run: |
    ORAS_VERSION="1.2.2"
    curl -LO "https://github.com/oras-project/oras/releases/download/v${ORAS_VERSION}/oras_${ORAS_VERSION}_linux_amd64.tar.gz"
    tar -xzf "oras_${ORAS_VERSION}_linux_amd64.tar.gz" -C /usr/local/bin/ oras
    oras version
```

### Alternative: run ORAS outside the container

If the Unity build runs inside a container but cache operations run on the host, you can split the job:

```yaml
jobs:
  restore-cache:
    runs-on: ubuntu-latest
    steps:
      - uses: oras-project/setup-oras@v1
      - name: Pull cache
        run: |
          echo "${{ secrets.GITHUB_TOKEN }}" | oras login ghcr.io --username "${{ github.actor }}" --password-stdin
          oras pull ghcr.io/.../cache:tag -o ./workspace/ || true
      - uses: actions/upload-artifact@v4
        with:
          name: library-cache
          path: ./workspace/Library/

  build:
    needs: restore-cache
    runs-on: ubuntu-latest
    container:
      image: unityci/editor:...
    steps:
      - uses: actions/download-artifact@v4
      # ... Unity build steps ...

  save-cache:
    needs: build
    runs-on: ubuntu-latest
    steps:
      # ... push updated Library/ back to GHCR ...
```

**However, this approach is slower due to artifact upload/download overhead.** The simpler approach is to install ORAS directly inside the container and do cache operations there.

### Recommended pattern for GameCI container jobs

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    container:
      image: unityci/editor:ubuntu-6000.0.66f1-linux-il2cpp-3
    permissions:
      packages: write
    steps:
      - uses: actions/checkout@v4

      - name: Install ORAS
        run: |
          curl -LO "https://github.com/oras-project/oras/releases/download/v1.2.2/oras_1.2.2_linux_amd64.tar.gz"
          tar -xzf oras_1.2.2_linux_amd64.tar.gz -C /usr/local/bin/ oras

      - name: Restore Unity Library cache
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          echo "$GITHUB_TOKEN" | oras login ghcr.io --username "${{ github.actor }}" --password-stdin
          CACHE_REF="ghcr.io/${{ github.repository }}/cache/unity-library:myproject-linux64"
          oras pull "${CACHE_REF}-${{ hashFiles('Assets/**','Packages/**','ProjectSettings/**') }}" -o /tmp/cache/ 2>/dev/null \
            || oras pull "${CACHE_REF}-latest" -o /tmp/cache/ 2>/dev/null \
            || echo "No cache found"
          if [ -f /tmp/cache/library-cache.tar.zst ]; then
            zstd -d -T0 /tmp/cache/library-cache.tar.zst --stdout | tar -xf - -C ./
            rm -rf /tmp/cache
          fi

      # ... Unity build steps ...

      - name: Save Unity Library cache
        if: always()
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          CACHE_REF="ghcr.io/${{ github.repository }}/cache/unity-library:myproject-linux64"
          HASH="${{ hashFiles('Assets/**','Packages/**','ProjectSettings/**') }}"
          tar -cf - Library/ | zstd -T0 -3 -o /tmp/library-cache.tar.zst
          oras push "${CACHE_REF}-${HASH}" \
            --artifact-type application/vnd.placeframe.unity-cache.v1 \
            /tmp/library-cache.tar.zst
          oras tag "${CACHE_REF}-${HASH}" "myproject-linux64-latest"
          rm /tmp/library-cache.tar.zst
```

Sources:
- [Automatic token authentication](https://docs.github.com/en/actions/security-guides/automatic-token-authentication)
- [Using secrets in GitHub Actions](https://docs.github.com/actions/security-guides/using-secrets-in-github-actions)
- [Storing Blobs on the GitHub Container Registry](https://www.aahlenst.dev/blog/storing-blobs-on-github-container-registry/)

## 8. Comparison: ORAS/ghcr.io vs `actions/cache`

| Dimension | `actions/cache` | ORAS + ghcr.io |
|---|---|---|
| **Storage limit (free)** | 10 GB per repo | Effectively unlimited (public repos free, container registry "currently free") |
| **Per-entry size** | 10 GB (formerly; now expandable with paid) | 10 GB per layer |
| **Data transfer cost** | Included in plan | Free with GITHUB_TOKEN |
| **Compression** | zstd (built-in since v4) | gzip (default for dirs); zstd via pre-compression |
| **Restore keys / fallback** | Built-in prefix matching | Manual tag-based fallback |
| **Eviction** | LRU, automatic | No eviction (manual cleanup needed) |
| **Setup complexity** | One action, zero config | Install ORAS, login, write push/pull scripts |
| **Cross-workflow sharing** | Same repo only | Any workflow, any repo (with token permissions) |
| **Retention** | 7 days default (configurable) | Indefinite until manually deleted |
| **Authentication in containers** | Works automatically (runner handles it) | Must pass GITHUB_TOKEN explicitly and run `oras login` |

### Recommendation

**ORAS + ghcr.io is the better choice for Unity Library caching** because:
1. The 10 GB `actions/cache` limit is insufficient for 5+ Unity builds with multi-GiB Library directories.
2. ghcr.io storage is effectively free for public repos and currently free for container registry images.
3. Pre-compressing with zstd gives better performance than ORAS's default gzip.
4. Indefinite retention means caches survive across weeks of inactivity (unlike 7-day `actions/cache` eviction).
5. Cross-repo cache sharing is possible if needed in the future.

The main downside is setup complexity — writing the push/pull/fallback logic manually — but this is a one-time cost.

## 9. Open questions

1. **ghcr.io "currently free" policy**: GitHub has stated container registry storage/bandwidth is currently free but may change. For public repos this is irrelevant (packages are always free). For private repos, monitor GitHub's changelog.
2. **Cleanup automation**: Need a scheduled workflow or post-build step to delete stale cache tags. Without this, storage will grow unbounded.
3. **`oras-project/setup-oras` inside `container:` jobs**: Untested whether the TypeScript action works correctly inside a container job. May need to fall back to manual curl+tar installation.
4. **zstd availability in GameCI images**: Need to verify that `zstd` is installed in `unityci/editor` images. If not, add it to the Dockerfile or install it in a setup step (`apt-get install -y zstd`).
