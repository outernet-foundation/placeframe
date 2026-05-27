ARG UV_BASE_DIGEST

FROM ghcr.io/astral-sh/uv${UV_BASE_DIGEST} AS base

WORKDIR /app/docker/livekit-token

ENV \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_NO_INSTALLER_METADATA=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/uv/venv \
    VIRTUAL_ENV=/opt/uv/venv

RUN uv venv $UV_PROJECT_ENVIRONMENT

COPY docker/livekit-token/pylock.toml ./pylock.toml
RUN --mount=type=cache,id=uvcache,sharing=locked,target=/root/.cache/uv \
    uv pip install -r pylock.toml

COPY docker/livekit-token /app/docker/livekit-token/

COPY --chmod=0755 docker/livekit-token/entrypoint.sh /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

FROM base AS dev

RUN uv pip install --no-deps --no-sources -e /app/docker/livekit-token

RUN uv pip check

FROM base AS prod

RUN uv pip install --no-deps --no-sources /app/docker/livekit-token

RUN uv pip check
