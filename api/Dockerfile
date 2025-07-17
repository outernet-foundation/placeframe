FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

WORKDIR /app

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./
COPY api/pyproject.toml ./api/

# Install dependencies
RUN uv sync --locked --no-install-project

# Copy application code
COPY . .

# Install the project itself
RUN uv sync --locked