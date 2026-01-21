ARG UV_BASE_DIGEST

FROM ghcr.io/astral-sh/uv${UV_BASE_DIGEST} AS dev

WORKDIR /app/docker/reconstructor

ENV \
    # Don't buffer stdout/stderr (so logs appear immediately)
    PYTHONUNBUFFERED=1 \
    # Disable writing .pyc files to disk
    PYTHONDONTWRITEBYTECODE=1 \
    # Enable bytecode compilation, to improve cold-start performance.
    UV_COMPILE_BYTECODE=1 \
    # Ensure layers are deterministic by not including installer metadata
    UV_NO_INSTALLER_METADATA=1 \
    # Enable copy mode to support bind mount caching.
    UV_LINK_MODE=copy \
    # Set torch cache directory
    TORCH_HOME=/opt/torch_cache \
    # Enable experimental AOTriton fast attention kernels for ROCm (speeds up LightGlue on ROCm)
    TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL=1 \
    # Set main and tool virtual environment locations
    UV_PROJECT_ENVIRONMENT=/opt/uv/venv \
    VIRTUAL_ENV=/opt/uv/venv \
    UV_TOOLS_ENVIRONMENT=/opt/uv/tools

RUN uv venv $UV_PROJECT_ENVIRONMENT 

# Install git (in order to install lightglue) + libGL for OpenCV
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    git ca-certificates \
    libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Install neural-networks dependencies
ARG TORCH_DEVICE
COPY docker/reconstructor/pylock.neural-networks-*.toml .
RUN --mount=type=cache,id=uvcache,sharing=locked,target=/root/.cache/uv \
    UV_HTTP_TIMEOUT=600 UV_HTTP_RETRIES=10 \
    uv pip install -r pylock.neural-networks-${TORCH_DEVICE}.toml

# Install neural-networks package
COPY packages/python/neural-networks /app/packages/python/neural-networks
RUN uv pip install --no-deps --no-sources /app/packages/python/neural-networks/third-party/deep-image-retrieval
RUN uv pip install --no-deps --no-sources /app/packages/python/neural-networks

# Preload neural-networks models to cache them in the image
RUN uv run python -c "import neural_networks.preload"

# Install remaining dependencies
COPY docker/reconstructor/pylock.toml ./pylock.toml
RUN --mount=type=cache,id=uvcache,sharing=locked,target=/root/.cache/uv \
    uv pip install -r pylock.toml

# Install remaining packages and the project itself
COPY packages/python/core /app/packages/python/core
COPY packages/python/common /app/packages/python/common
COPY packages/generated/python/api-client /app/packages/generated/python/api-client
COPY docker/reconstructor /app/docker/reconstructor
RUN uv pip install --no-deps --no-sources \
    /app/packages/python/common \
    /app/packages/python/core \
    /app/packages/generated/python/api-client \
    /app/docker/reconstructor

# Verify that all declared dependencies were installed
RUN uv pip check

# Copy the entrypoint and make it executable
COPY --chmod=0755 docker/reconstructor/entrypoint.sh /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]