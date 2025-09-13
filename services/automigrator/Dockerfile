FROM ghcr.io/astral-sh/uv:0.7.22-python3.13-bookworm-slim AS dev

ENV \
    # Don't buffer stdout/stderr (so logs appear immediately)
    PYTHONUNBUFFERED=1 \
    # Disable writing .pyc files to disk
    PYTHONDONTWRITEBYTECODE=1 \
    # Enable bytecode compilation, to improve cold-start performance.
    UV_COMPILE_BYTECODE=1 \
    # Disable installer metadata, to create a deterministic layer.
    UV_NO_INSTALLER_METADATA=1 \
    # Enable copy mode to support bind mount caching.
    UV_LINK_MODE=copy

# Move the venv out of the project directory to prevent docker compose bind mounts from clobbering it
ENV UV_PROJECT_ENVIRONMENT=/opt/uv/venv

ENV PICCOLO_CONF="src.db.conf"

WORKDIR /app/services/automigrator

# Install dependencies
COPY services/automigrator/pyproject.toml services/automigrator/uv.lock ./
COPY common/ /app/common
# COPY services/api /app/services/api
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --no-editable

# Install project
COPY services/automigrator/ .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

# Copy the entrypoint and make it executable
COPY --chmod=0755 services/automigrator/entrypoint.sh /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]