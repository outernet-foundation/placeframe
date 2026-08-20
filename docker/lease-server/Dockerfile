ARG UV_BASE_DIGEST

FROM ghcr.io/astral-sh/uv${UV_BASE_DIGEST} AS base

WORKDIR /app/docker/lease-server

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
    # Set virtual environment location
    UV_PROJECT_ENVIRONMENT=/opt/uv/venv \
    VIRTUAL_ENV=/opt/uv/venv

# Create the virtual environment
RUN uv venv $UV_PROJECT_ENVIRONMENT

# Git is required to resolve VCS dependencies in the lock file (e.g. logconf)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY docker/lease-server/pylock.toml ./pylock.toml
RUN --mount=type=cache,id=uvcache,sharing=locked,target=/root/.cache/uv \
    uv pip install -r pylock.toml

# Copy source code
COPY packages/python/common/ /app/packages/python/common
COPY packages/python/core/ /app/packages/python/core
COPY packages/generated/python/datamodels/ /app/packages/generated/python/datamodels
COPY docker/lease-server /app/docker/lease-server/

# Copy the entrypoint and make it executable
COPY --chmod=0755 docker/lease-server/entrypoint.sh /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

FROM base AS dev

# Install editable packages for development
RUN uv pip install --no-deps --no-sources \
    -e /app/packages/python/common \
    -e /app/packages/python/core \
    -e /app/packages/generated/python/datamodels \
    -e /app/docker/lease-server

# Verify that all declared dependencies were installed
RUN uv pip check

FROM base AS prod

# Install non-editable packages for production
RUN uv pip install --no-deps --no-sources \
    /app/packages/python/common \
    /app/packages/python/core \
    /app/packages/generated/python/datamodels \
    /app/docker/lease-server

# Verify that all declared dependencies were installed
RUN uv pip check
