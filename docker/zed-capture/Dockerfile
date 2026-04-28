ARG ZED_BASE_DIGEST
FROM stereolabs/zed:5.2-runtime-jetson-jp6.1.0${ZED_BASE_DIGEST}

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app/zed

ENV \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_NO_INSTALLER_METADATA=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/uv/venv \
    VIRTUAL_ENV=/opt/uv/venv

# Stereolabs base images don't include Python 3.13
RUN uv python install 3.13

RUN uv venv $UV_PROJECT_ENVIRONMENT

# Download pyzed wheel matching the installed ZED SDK version.
# get_python_api.py downloads the wheel then tries to pip-install it (which fails
# in a uv venv since pip isn't present). We ignore its exit code and install with uv.
RUN uv pip install requests && \
    (uv run --python 3.13 /usr/local/zed/get_python_api.py || true) && \
    ls pyzed*.whl && \
    uv pip install pyzed*.whl && \
    uv pip uninstall requests

# Install remaining dependencies from lock file
COPY docker/zed-capture/pylock.toml ./pylock.toml
RUN --mount=type=cache,id=uvcache,sharing=locked,target=/root/.cache/uv \
    uv pip install -r pylock.toml

# Install source packages
COPY packages/python/common /app/packages/python/common
COPY packages/python/core /app/packages/python/core
COPY docker/zed-capture /app/zed
RUN uv pip install --no-deps --no-sources \
    /app/packages/python/common \
    /app/packages/python/core \
    /app/zed

RUN uv pip check

COPY --chmod=0755 docker/zed-capture/entrypoint.sh /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
