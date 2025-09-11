FROM ghcr.io/astral-sh/uv:0.7.22-python3.13-bookworm-slim AS dev

WORKDIR /app/tasks/create-database

COPY tasks/create-database/pyproject.toml tasks/create-database/uv.lock ./

# Copy common
COPY common/ /app/common

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --no-editable

# Copy application code
COPY tasks/create-database/ .

# Install the project itself
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable

# Entrypoint
RUN apt-get update && apt-get install -y --no-install-recommends dos2unix && rm -rf /var/lib/apt/lists/*
COPY tasks/create-database/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN dos2unix /usr/local/bin/entrypoint.sh && chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]