ARG UV_BASE_DIGEST

FROM ghcr.io/astral-sh/uv${UV_BASE_DIGEST}

WORKDIR /app/docker/rathole-client

ENV \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_NO_INSTALLER_METADATA=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/uv/venv \
    VIRTUAL_ENV=/opt/uv/venv \
    RUST_LOG=info

ARG RATHOLE_URL=https://github.com/rapiz1/rathole/releases/download/v0.5.0/rathole-x86_64-unknown-linux-gnu.zip
ARG RATHOLE_SHA256=3e7d0d0f365120cd3cd351d147d1a12ee960c8068b464d4dd533a3821873b80e

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl unzip \
    && rm -rf /var/lib/apt/lists/* \
    && curl -fsSL -o /tmp/rathole.zip "$RATHOLE_URL" \
    && echo "$RATHOLE_SHA256  /tmp/rathole.zip" | sha256sum -c - \
    && unzip -o /tmp/rathole.zip -d /usr/local/bin \
    && chmod 0755 /usr/local/bin/rathole \
    && rm /tmp/rathole.zip

RUN uv venv $UV_PROJECT_ENVIRONMENT

COPY docker/rathole-client/pylock.toml ./pylock.toml
RUN --mount=type=cache,id=uvcache,sharing=locked,target=/root/.cache/uv \
    uv pip install -r pylock.toml

COPY docker/rathole-client /app/docker/rathole-client
RUN uv pip install --no-deps --no-sources /app/docker/rathole-client
RUN uv pip check
RUN test -f /opt/uv/venv/lib/python3.13/site-packages/placeframe_rathole_client/templates/client.toml.j2

ENTRYPOINT ["uv", "run", "--no-sync", "python", "-m", "placeframe_rathole_client.main"]
