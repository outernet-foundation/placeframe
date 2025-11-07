FROM ghcr.io/astral-sh/uv:0.7.22-python3.13-bookworm-slim AS dev

ENV \
    # Don't buffer stdout/stderr (so logs appear immediately)
    PYTHONUNBUFFERED=1 \
    # Disable writing .pyc files to disk
    PYTHONDONTWRITEBYTECODE=1 \
    # Enable bytecode compilation, to improve cold-start performance.
    UV_COMPILE_BYTECODE=1 \
    # Enable copy mode to support bind mount caching.
    UV_LINK_MODE=copy

# Move the venv out of the project directory to prevent docker compose bind mounts from clobbering it
ENV UV_PROJECT_ENVIRONMENT=/opt/uv/venv

WORKDIR /app/services/visual-localization-system/api

# Install dependencies
COPY services/visual-localization-system/api/pyproject.toml services/visual-localization-system/api/uv.lock ./
COPY services/visual-localization-system/common/ /app/services/visual-localization-system/common
COPY services/visual-localization-system/core/ /app/services/visual-localization-system/core
COPY services/visual-localization-system/models/ /app/services/visual-localization-system/models/
COPY services/visual-localization-system/localize/clients/python/ /app/services/visual-localization-system/localize/clients/python/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --no-editable

# Install project
COPY services/visual-localization-system/api/ .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

# Copy the entrypoint and make it executable
COPY --chmod=0755 services/visual-localization-system/api/entrypoint.sh /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]