FROM ghcr.io/astral-sh/uv:0.7.22-python3.13-bookworm-slim AS dev

WORKDIR /app/services/visual-localization-system/localize

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
    UV_LINK_MODE=copy \
    # Set torch cache directory
    TORCH_HOME=/opt/torch_cache \
    # Set pip cache directory
    PIP_CACHE_DIR=/root/.cache/pip \
    # Set virtual environment location
    UV_PROJECT_ENVIRONMENT=/opt/uv/venv \
    VIRTUAL_ENV=/opt/uv/venv

# Install git (in order to install lightglue) + libGL for OpenCV
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    git ca-certificates \
    libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Create the virtual environment
RUN uv venv $UV_PROJECT_ENVIRONMENT

# Copy main package lock files
COPY services/visual-localization-system/localize/pyproject.toml \
    services/visual-localization-system/localize/uv.lock \
    services/visual-localization-system/localize/README.md \
    /app/services/visual-localization-system/localize/

# Copy nn package lock files
COPY services/visual-localization-system/nn/pyproject.toml \
    services/visual-localization-system/nn/uv.lock \
    services/visual-localization-system/nn/README.md \
    /app/services/visual-localization-system/nn/

# Copy core package lock files
COPY services/visual-localization-system/core/pyproject.toml \
    services/visual-localization-system/core/uv.lock \
    services/visual-localization-system/core/README.md \
    /app/services/visual-localization-system/core/

# Copy common package lock files
COPY services/visual-localization-system/common/pyproject.toml \
    services/visual-localization-system/common/uv.lock \
    /app/services/visual-localization-system/common/

# Install torch and cuda
RUN --mount=type=cache,id=uvcache,sharing=locked,target=/root/.cache/uv \
    uv sync \
    --locked \
    --no-dev \
    --no-install-project \
    --no-editable \
    --only-group torch

# Copy nn
COPY services/visual-localization-system/nn \
    /app/services/visual-localization-system/nn/

# Install nn
RUN --mount=type=cache,id=uvcache,sharing=locked,target=/root/.cache/uv \
    uv sync \
    --locked \
    --no-dev \
    --no-install-project \
    --no-editable \
    --only-group torch \
    --only-group nn

# Preload nn models so they are cached in the Docker image
RUN --mount=type=cache,id=uvcache,sharing=locked,target=/root/.cache/uv \
    uv run --no-sync python - <<'PY'
from nn.dir import load_DIR
from nn.lightglue import load_lightglue
from nn.superpoint import load_superpoint

_ = load_DIR("cpu")
_ = load_superpoint("indoor", 2500, "cpu")
_ = load_superpoint("outdoor", 2500, "cpu")
_ = load_lightglue("cpu")
PY

# Copy core
COPY services/visual-localization-system/core \
    /app/services/visual-localization-system/core/

# Copy common
COPY services/visual-localization-system/common/ /app/services/visual-localization-system/common

# Install remaining dependencies
RUN --mount=type=cache,id=uvcache,sharing=locked,target=/root/.cache/uv \
    uv sync \
    --locked \
    --no-dev \
    --no-editable \
    --no-install-project \
    --all-groups 

# Install project itself
COPY services/visual-localization-system/localize/ .
RUN --mount=type=cache,id=uvcache,sharing=locked,target=/root/.cache/uv \
    uv sync \
    --locked \
    --no-dev \
    --no-editable \
    --all-groups 

# Copy the entrypoint and make it executable
COPY --chmod=0755 services/visual-localization-system/localize/entrypoint.sh /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]