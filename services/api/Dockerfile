FROM ghcr.io/astral-sh/uv:0.7.22-python3.13-bookworm-slim AS dev

# Don't buffer stdout/stderr (so logs appear immediately)
ENV PYTHONUNBUFFERED=1

# Disable writing .pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1

# Enable bytecode compilation, to improve cold-start performance.
ENV UV_COMPILE_BYTECODE=1

# Disable installer metadata, to create a deterministic layer.
ENV UV_NO_INSTALLER_METADATA=1

# Enable copy mode to support bind mount caching.
ENV UV_LINK_MODE=copy

# Move the venv out of the project directory to prevent docker compose bind mounts from clobbering it
ENV UV_PROJECT_ENVIRONMENT=/opt/uv/venv

ENV PICCOLO_CONF="src.db.conf"

WORKDIR /app/services/api

# Copy dependency files first for better caching
COPY services/api/pyproject.toml services/api/uv.lock ./

# Copy common
COPY common/ /app/common

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --no-editable

# Copy application code
COPY services/api/ /app/services/api

# Install the project itself
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

# Copy the entrypoint and make it executable
COPY --chmod=0755 services/api/entrypoint.sh /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]