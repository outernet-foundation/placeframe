FROM ghcr.io/astral-sh/uv:0.9.11-python3.13-bookworm-slim AS dev

WORKDIR /app/docker/reconstructor

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

# Install torch and cuda
COPY docker/reconstructor/pylock.torch.toml ./pylock.torch.toml
RUN --mount=type=cache,id=uvcache,sharing=locked,target=/root/.cache/uv \
    uv pip install -r pylock.torch.toml

# Install neural-networks dependencies
COPY docker/reconstructor/pylock.neural-networks.toml ./pylock.neural-networks.toml
RUN --mount=type=cache,id=uvcache,sharing=locked,target=/root/.cache/uv \
    uv pip install -r pylock.neural-networks.toml

# Install neural-networks
COPY packages/neural-networks /app/packages/neural-networks
RUN uv pip install --no-deps /app/packages/neural-networks

# Preload neural-networks models to cache them in the image
RUN uv run python -c "import neural_networks.preload"

# Install remaining dependencies
COPY docker/reconstructor/pylock.toml ./pylock.toml
RUN --mount=type=cache,id=uvcache,sharing=locked,target=/root/.cache/uv \
    uv pip install -r pylock.toml

# Install the project itself
COPY pyproject.toml /app/pyproject.toml
COPY packages/core /app/packages/core
COPY packages/common /app/packages/common
COPY docker/reconstructor /app/docker/reconstructor
RUN uv pip install --no-deps \
    /app/packages/common \
    /app/packages/core \
    /app/docker/reconstructor

# Copy the entrypoint and make it executable
COPY --chmod=0755 docker/reconstructor/entrypoint.sh /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]