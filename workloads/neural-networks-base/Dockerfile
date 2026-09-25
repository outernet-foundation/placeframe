ARG UV_BASE_IMAGE

FROM ${UV_BASE_IMAGE}

WORKDIR /app

ENV \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_NO_INSTALLER_METADATA=1 \
    UV_LINK_MODE=copy \
    TORCH_HOME=/opt/torch_cache \
    TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL=1 \
    UV_PROJECT_ENVIRONMENT=/opt/uv/venv \
    VIRTUAL_ENV=/opt/uv/venv

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    git ca-certificates \
    libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 \
    && rm -rf /var/lib/apt/lists/*

RUN uv venv $UV_PROJECT_ENVIRONMENT

ARG TORCH_DEVICE
COPY workloads/neural-networks-base/pylock.neural-networks-*.toml .
RUN --mount=type=cache,id=uvcache,sharing=locked,target=/root/.cache/uv \
    UV_HTTP_TIMEOUT=600 UV_HTTP_RETRIES=10 \
    uv pip install -r pylock.neural-networks-${TORCH_DEVICE}.toml

COPY packages/python/neural-networks /app/packages/python/neural-networks
RUN uv pip install --no-deps --no-sources /app/packages/python/neural-networks/third-party/deep-image-retrieval
RUN uv pip install --no-deps --no-sources /app/packages/python/neural-networks

RUN uv run python -c "import neural_networks.preload"
