FROM ghcr.io/astral-sh/uv:0.9.11-python3.13-bookworm-slim AS dev

WORKDIR /app/docker/orchestrator

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
    # Set pip cache directory
    PIP_CACHE_DIR=/root/.cache/pip \
    # Set virtual environment location
    UV_PROJECT_ENVIRONMENT=/opt/uv/venv \
    VIRTUAL_ENV=/opt/uv/venv

# Create the virtual environment
RUN uv venv $UV_PROJECT_ENVIRONMENT

# Install dependencies
COPY docker/orchestrator/pylock.toml ./pylock.toml
RUN --mount=type=cache,id=uvcache,sharing=locked,target=/root/.cache/uv \
    uv pip install -r pylock.toml

# Install project
COPY packages/common/ /app/packages/common
COPY packages/core/ /app/packages/core
COPY packages/datamodels/ /app/packages/datamodels
COPY docker/orchestrator /app/docker/orchestrator/
RUN uv pip install --no-deps --no-sources \
    /app/packages/common \
    /app/packages/core \
    /app/packages/datamodels \
    /app/docker/orchestrator

# Verify that all declared dependencies were installed
RUN uv pip check

# Copy the entrypoint and make it executable
COPY --chmod=0755 docker/orchestrator/entrypoint.sh /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]