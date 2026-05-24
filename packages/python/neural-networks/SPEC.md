# packages/python/neural-networks/SPEC.md

## What this is

`neural-networks` is the workspace package that holds the PyTorch model loaders the localizer and reconstructor services use: a global-descriptor retrieval model (DIR / Resnet-101-AP-GeM, via a vendored copy of `naver/deep-image-retrieval`), a local feature extractor (ALIKED, from the `lightglue` package), and a feature matcher (LightGlue, same package). The whole package is two source files. Its existence as a separate package is structural rather than substantive: the three accelerator-specific PyTorch builds (CPU / CUDA / ROCm) need a single place to live behind mutually-exclusive `uv` extras, and the localizer and reconstructor both import from that one place via accelerator-tagged dependency groups.

## Shape

### Source layout

    packages/python/neural-networks/
    |--- pyproject.toml                  cpu/cuda/rocm extras + conflicts + per-extra torch indexes
    |--- README.md                       (empty)
    |--- main.py                         unused `uv init` stub
    |--- src/neural_networks/
    |   |--- models.py                   3 loaders + DIR Module wrapper
    |   |--- preload.py                  imports models.py and calls each loader once (CPU)
    |   `--- py.typed
    `--- third-party/deep-image-retrieval/
        |--- pyproject.toml              name="dirtorch", packages=["vendored/dirtorch"]
        |--- vendored/PROVENANCE         upstream commit pin + import date
        `--- vendored/dirtorch/          full naver/deep-image-retrieval @ 610247f7

The vendored library is exposed to the workspace as a separate package named `dirtorch`, version `0.0.0`, with the wheel built from `vendored/dirtorch/`. `neural-networks/pyproject.toml` lists `dirtorch` as a regular dependency; the workspace edge is at the repo root (`packages/python/neural-networks/third-party/deep-image-retrieval` is a workspace member; `dirtorch = { workspace = true }` is the resolution edge).

### The three loaders

`src/neural_networks/models.py` exposes three top-level functions, all with the same shape  -  `freeze parameters -> .eval() -> .to(device)`:

- `load_DIR(device="cpu") -> DIR`  -  returns a `Module` wrapping the dirtorch Resnet-101-AP-GeM retrieval network. The checkpoint is fetched from a self-hosted GitHub Releases URL into `torch.hub.get_dir()/dirtorch/Resnet-101-AP-GeM.pt`. `DIR.forward` does mean/std normalization, runs the network, then yanks the output to numpy for PCA whitening (`dirtorch.utils.common.whiten_features`), then back to a tensor on the original device. Returns `{"global_descriptor": Tensor[1, D]}`.
- `load_aliked(nms_radius=None, detection_threshold=None, max_num_keypoints=None, device="cpu")`  -  returns `lightglue.ALIKED`. Kwargs are forwarded only if non-`None`, so passing nothing yields ALIKED defaults (`nms_radius=2`, `detection_threshold=0.2`).
- `load_lightglue(device="cpu")`  -  returns `lightglue.LightGlue` configured with `features="aliked"`, `width_confidence=-1` (disabled), `depth_confidence=0.95` (enabled early-stop), `mp=True` (mixed-precision autocast). The 30-line comment on this function is the source of truth for these settings; see "Rationale" below.

`_freeze` is the shared parameter-freeze helper used by all three loaders. It calls `requires_grad_(False)` on every parameter so forward passes produce non-grad tensors regardless of the ambient grad-mode flag  -  relevant because `torch.set_grad_enabled` / `no_grad` / `inference_mode` are all thread-local, and both services invoke these models from asyncio executor threads where the main-thread flag does not apply.

### Consumers

`docker/localizer/src/localize.py:62` and `docker/reconstructor/src/reconstructor/run_reconstruction.py:28` both import the same three loaders identically and feed each into a typed wrapper from `packages/python/core/src/core/model_wrappers.py`  -  `make_global_descriptor_extractor`, `make_local_feature_extractor`, `make_local_feature_matcher_for_tensors` (localizer) or `_for_arrays` (reconstructor). The neural-networks package returns loosely-typed `Any` models; `core.model_wrappers` is where typed-tensor signatures get stamped on the call path.

The reconstructor additionally keeps a bare reference to the ALIKED model (`run_reconstruction.py:64-71`) so it can override `dkd.n_limit` per job. The typed wrapper is the call entry point; the bare reference exists only for configuration.

`DEVICE = "cuda" if torch.cuda.is_available() else "cpu"` in both services. ROCm reports through PyTorch's CUDA-API shim, so the literal string `"cuda"` is correct on ROCm too.

### Conflicting accelerator extras

The torch dependency is gated behind three mutually-exclusive `optional-dependencies` extras: `cpu`, `cuda`, `rocm`. The `pyproject.toml` block:

    [project.optional-dependencies]
    cpu  = ["lightglue", "torch>=2.9.1", "torchvision>=0.24.1"]
    cuda = ["lightglue", "torch>=2.9.1", "torchvision>=0.24.1"]
    rocm = ["lightglue", "torch>=2.9.1", "torchvision>=0.24.1", "pytorch-triton-rocm>=3.5.1"]

    [tool.uv.sources]
    torch = [
        { index = "pytorch-cpu",  extra = "cpu"  },
        { index = "pytorch-cuda", extra = "cuda" },
        { index = "pytorch-rocm", extra = "rocm" },
    ]
    # torchvision and pytorch-triton-rocm: same pattern

    [tool.uv]
    conflicts = [[{ extra = "cpu" }, { extra = "cuda" }, { extra = "rocm" }]]

...plus three `[[tool.uv.index]]` entries pointing at `whl/cpu`, `whl/cu128`, and `whl/rocm6.4`.

**`lightglue` is in every extra on purpose.** It transitively pulls torch, and uv only redirects torch to the per-accelerator index if an extra is actively selected  -  "actively selected" requires *something* declared in the extra. Removing lightglue from one of the extras silently pulls torch from PyPI on that accelerator. Any new dependency that drags torch in transitively must follow the same pattern.

**Plain `uv sync --all-packages` does not install torch.** The conflicts block makes uv refuse to install three mutually exclusive extras simultaneously, so by default it installs none. To get torch into the workspace venv (for type-checking, for running `docker/localizer/tests/` outside Docker, for the localizer's `dump_openapi` to work, for `dirtorch/test_dir.py` to import), pass `--extra cpu` / `--extra cuda` / `--extra rocm` to `uv sync`. The root `CLAUDE.md` records this for the COI environment.

### Docker base image and the preload trick

The `neural-networks-base` image (`docker/neural-networks-base/Dockerfile`) is the heavy-lifting layer that the localizer and reconstructor build `FROM`. It does three things:

1. Installs a per-accelerator lockfile: `pylock.neural-networks-${TORCH_DEVICE}.toml` (one of `cpu` / `cuda` / `rocm`). The three lockfiles are committed; `uv run lock-python` regenerates them.
2. Installs the `dirtorch` and `neural-networks` source packages with `--no-deps --no-sources`.
3. Runs `python -c "import neural_networks.preload"`. `preload.py` calls each loader once on CPU; the side effect is that `torch.hub` downloads the DIR checkpoint into `TORCH_HOME=/opt/torch_cache` and the layer commits the weights into the image. Lightglue/ALIKED weights are similarly resolved by the lightglue package's own hub-cache calls. No service ever imports `preload` at runtime; it exists solely to bake the weights into a build layer.

`compose.bake.yml` defines `neural-networks-base-cuda` and `neural-networks-base-rocm` targets (no `cpu` target  -  cpu is for local type-checking, not for the deployable image set). The localizer and reconstructor Dockerfiles begin with `FROM neural-networks-base AS dev`; `compose.bake.yml` passes `neural-networks-base: "target:neural-networks-base-{cuda,rocm}"` as `additional_contexts` so the `FROM` resolves to the matching accelerator base.

### Per-service deptry wiring

Both consumer services declare:

    [dependency-groups]
    neural-networks-cpu  = ["neural-networks[cpu]"]
    neural-networks-cuda = ["neural-networks[cuda]"]
    neural-networks-rocm = ["neural-networks[rocm]"]

...and `[tool.deptry.per_rule_ignores] DEP003 = ["torch"]` + `DEP004 = ["neural_networks"]`. The reason (per the comment in the localizer pyproject): the consumer services import `torch` directly but cannot declare it directly, because torch is split across the three platform-conflicting extras in `neural-networks` and declaring bare `torch` would create resolution conflicts. The dependency-group + deptry overrides are the workaround.

## Constraints

### Why a separate package at all

This package's substantive code is small. Its existence as a workspace package is structural  -  it's the one place the three accelerator-specific torch builds and their indexes are configured. Both the localizer and reconstructor need the same model code; both need the same per-accelerator torch wheel; neither can declare torch directly without creating conflicts. Pulling the loaders + extras into one package is the smallest unit that lets the consumers depend on `neural-networks[cuda]` (or `[rocm]`) and get the right torch wheel along with it.

### Why `lightglue` is in every extra

uv's `[tool.uv.sources]` redirection only triggers when an extra is actually exercised, and "exercised" means the extra has to contain something. lightglue itself dangles `torch` transitively, so it has to be listed in each per-accelerator extra to make the torch source redirection apply to its transitive resolution. This is documented in the pyproject comment but matters enough to surface here: any new dependency that pulls torch in transitively will need the same treatment.

### Why the vendored dirtorch

`naver/deep-image-retrieval` is not on PyPI; the only distribution mechanism is the upstream Git repo. Vendoring at a pinned commit (`610247f7...`, recorded in `vendored/PROVENANCE`) lets us treat it as a regular workspace package while keeping the diff against upstream minimal  -  the only local addition is an empty `__init__.py` to make the directory a package. Re-vendoring is a tar swap. Most of the dirtorch tree (dataset loaders, kapture support, R-MAC nets, training loops) is unused; keeping it intact rather than carving out the two functions actually called (`load_model`, `whiten_features`) minimizes the diff that would have to be re-applied after a re-vendor.

The DIR weight URL itself is a self-hosted mirror under outernet-foundation's GitHub Releases  -  upstream's Google Drive link broke. The mirror is committed-by-reference in `models.py:28`.

### Why two checkpoint-loading hacks

Both hacks survive a long history of subtle PyTorch and sklearn changes:

- `sys.modules["sklearn.decomposition.pca"] = _pca` (module-level in `models.py`). The DIR checkpoint contains a pickled sklearn PCA object referencing `sklearn.decomposition.pca`  -  a module path that disappeared in sklearn 0.24 when the module was made private (`_pca`). Pickle resolves classes by `module.qualname`, so the remap is what makes the checkpoint load on modern sklearn. The pattern is lifted directly from Hierarchical-Localization.
- `torch.load = _load_legacy` inside `load_DIR`. PyTorch 2.6 flipped `torch.load`'s default to `weights_only=True`, which refuses arbitrary pickled objects. The DIR checkpoint is a dict containing a sklearn PCA object  -  not just a state-dict  -  so loading requires `weights_only=False`. The monkey-patch is scoped to one call.

Both hacks could be eliminated by rebuilding the DIR checkpoint as a pure state-dict plus a separately-serialized whitening matrix. That work hasn't happened because DIR is dated (2019) and the rebuild effort is better spent on a successor retrieval model (DINOv2 + GeM pooling or similar)  -  see the README license-posture table for the candidate set.

### Why the LightGlue settings are what they are

`width_confidence=-1`, `depth_confidence=0.95`, `mp=True` together account for ~40% matching-latency reduction with no match-count drift on Ampere+ GPUs. The full V1/V2/V3 benchmark log, the explanation of why width pruning corrupts under `pad_sequence` batching, and the conditions under which the "batch_size=1 + width pruning" alternative might become net-positive again all live as a comment on `load_lightglue` in `models.py:120-150`. **That comment is the source of truth for these settings  -  this SPEC does not duplicate it.** When in doubt, re-read the comment; when changing the settings, the comment is the place to update first.

### Why `preload.py`

Cold weight downloads at service-startup time would add tens of seconds of latency to the first request after a deploy, plus tie service availability to the upstream weight-host's uptime. The preload trick  -  calling each loader at *image build* time so the hub-cache lands in a baked layer  -  moves that latency to build time and makes runtime startup network-independent. The two consumers never import `preload` themselves; the Dockerfile's `import` line is the only caller.

### Why the numpy round-trip in `DIR.forward`

`dirtorch.utils.common.whiten_features` is a numpy implementation that operates on `(N, D)` arrays via sklearn's PCA internals. There is no torch-native version in dirtorch. `DIR.forward` extracts features on the device, hauls them to host memory for whitening, and pushes the result back. Per-call cost is a 128-or-N-element host transfer round-trip. It hasn't shown up in profiles; if it did, porting the whitening matmul to torch is straightforward (the whitening matrix is small and constant per checkpoint).

## See also

- `packages/python/core/src/core/model_wrappers.py`  -  typed-tensor seam over the three model callables. Returns `Any`-typed models from `neural-networks` get their typed signatures stamped here; both services consume the wrapped versions.
- `packages/python/core/src/core/lightglue.py`  -  `Keypoints` / `Descriptors` / `KeypointsArrays` / `DescriptorsArrays` / `MatchIndices` `NewType` brands and the `lightglue_match` / `lightglue_match_tensors` batching code that the wrappers drive.
- `docker/neural-networks-base/Dockerfile`  -  base image build steps, `TORCH_HOME` location, and the `preload` import that bakes weights into a layer.
- `docker/localizer/src/localize.py:58-69` and `docker/reconstructor/src/reconstructor/run_reconstruction.py:67-74`  -  the two consumer call sites. Both load all three models once at module import.
- The 30-line comment on `load_lightglue` in `src/neural_networks/models.py`  -  the source of truth for LightGlue tuning. Re-read before changing `width_confidence`, `depth_confidence`, or `mp`.
