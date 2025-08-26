FROM ghcr.io/astral-sh/uv:0.7.22-python3.13-bookworm-slim AS dev

WORKDIR /app/services/resconstruction_worker

COPY services/resconstruction_worker/pyproject.toml services/resconstruction_worker/uv.lock ./

# Copy common
COPY common/ /app/common

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --no-editable

# Copy application code
COPY services/resconstruction_worker/ .

# Install the project itself
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable

# Entrypoint
RUN apt-get update && apt-get install -y --no-install-recommends dos2unix && rm -rf /var/lib/apt/lists/*
RUN dos2unix /app/services/resconstruction_worker/entrypoint.sh && chmod +x /app/services/resconstruction_worker/entrypoint.sh

ENTRYPOINT ["/app/services/resconstruction_worker/entrypoint.sh"]