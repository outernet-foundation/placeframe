ARG UV_BASE_IMAGE

FROM ${UV_BASE_IMAGE} AS dev

WORKDIR /app/workloads/api

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

# Install dependencies
COPY workloads/auth-initializer/pylock.toml ./pylock.toml
RUN --mount=type=cache,id=uvcache,sharing=locked,target=/root/.cache/uv \
    uv pip install -r pylock.toml

# Install project
COPY workloads/auth-initializer /app/workloads/auth-initializer
RUN uv pip install --no-deps --no-sources \
    /app/workloads/auth-initializer

# Verify that all declared dependencies were installed
RUN uv pip check

# Copy the entrypoint and make it executable
COPY --chmod=0755 workloads/auth-initializer/entrypoint.sh /usr/local/bin/entrypoint.sh

COPY workloads/auth-initializer/realm-export /templates

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]