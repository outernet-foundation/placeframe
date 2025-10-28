FROM ghcr.io/astral-sh/uv:0.7.22-python3.13-bookworm-slim AS dev

ENV \
    # Don't buffer stdout/stderr (so logs appear immediately)
    PYTHONUNBUFFERED=1 \
    # Disable writing .pyc files to disk
    PYTHONDONTWRITEBYTECODE=1 \
    # Enable bytecode compilation, to improve cold-start performance.
    UV_COMPILE_BYTECODE=1 \
    # Ensure layers are deterministic by not including installer metadata
    # UV_NO_INSTALLER_METADATA=1 \
    # Enable copy mode to support bind mount caching.
    UV_LINK_MODE=copy

# Install git (required for Hierarchical-Localization to install lightglue) + libGL for OpenCV
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    git ca-certificates \
    libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/services/visual-localization-system/run-reconstruction

# Make hloc third-party code (e.g. SuperGlue) available
ENV PYTHONPATH="/app/services/visual-localization-system/third-party/Hierarchical-Localization/third_party:${PYTHONPATH}"
ENV PYTHONPATH="/app/services/visual-localization-system/third-party/Hierarchical-Localization/third_party/deep-image-retrieval:${PYTHONPATH}"

ENV TORCH_HOME=/opt/torch_cache

# Put the virtual environment outside the project directory to prevent docker compose bind mounts from clobbering it
ENV UV_PROJECT_ENVIRONMENT=/opt/uv/venv
# uv pip sync uses VIRTUAL_ENV rather than UV_PROJECT_ENVIRONMENT, so set that too
ENV VIRTUAL_ENV=/opt/uv/venv
ENV PIP_CACHE_DIR=/root/.cache/uv

# Create the virtual environment
RUN uv venv /opt/uv/venv

# Install hloc and its dependencies (including cuda libraries) into a separate layer so we can cache it
COPY services/visual-localization-system/third-party/ /app/services/visual-localization-system/third-party
COPY services/visual-localization-system/run-reconstruction/pylock.hloc.toml /app/services/visual-localization-system/run-reconstruction/pylock.hloc.toml
RUN --mount=type=cache,id=uvcache,sharing=locked,target=/root/.cache/uv \
    uv pip sync --preview /app/services/visual-localization-system/run-reconstruction/pylock.hloc.toml

# Preload pretrained models to cache them in the docker image
RUN --mount=type=cache,id=uvcache,target=/root/.cache/uv \
    uv run python - <<'PY'
import torch
from hloc.extractors.dir import DIR
from hloc.extractors.superpoint import SuperPoint
from lightglue import LightGlue

# PyTorch 2.6 flips torch.load default to weights_only=True, so we temporarily force legacy loading to read DIR’s pickled checkpoint; 
# see: https://dev-discuss.pytorch.org/t/bc-breaking-change-torch-load-is-being-flipped-to-use-weights-only-true-by-default-in-the-nightlies-after-137602/2573
_orig_load = torch.load
def _load_legacy(*args, **kwargs):
    kwargs.setdefault("weights_only", False)
    return _orig_load(*args, **kwargs)

torch.load = _load_legacy
_ = DIR({})
torch.load = _orig_load

_ = SuperPoint({'weights': 'indoor'})
_ = SuperPoint({'weights': 'outdoor'})
_ = LightGlue(features="superpoint")
PY

# Install remaining dependencies
COPY common/ /app/common
COPY services/visual-localization-system/run-reconstruction/pyproject.toml services/visual-localization-system/run-reconstruction/uv.lock ./
RUN --mount=type=cache,id=uvcache,sharing=locked,target=/root/.cache/uv \
    # --inexact prevents uv sync from uninstalling packages installed by hloc pip sync
    uv sync --locked --no-editable --all-groups --no-group dev --no-install-project 

# Install project itself
COPY services/visual-localization-system/run-reconstruction/ .
RUN --mount=type=cache,id=uvcache,sharing=locked,target=/root/.cache/uv \
    uv sync --locked --no-editable --all-groups --no-group dev

# Copy the entrypoint and make it executable
COPY --chmod=0755 services/visual-localization-system/run-reconstruction/entrypoint.sh /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]