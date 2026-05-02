FROM neural-networks-base AS dev

# PyTorch's default caching allocator uses fixed-size segments, which fragment under
# varying per-request peaks (chaotic image sizes, retrieval top-k results, keypoint
# counts) and eventually OOM despite ample free memory. Expandable segments use CUDA
# virtual memory to grow segments on demand, eliminating that fragmentation class.
ENV PYTORCH_ALLOC_CONF=expandable_segments:True

WORKDIR /app/docker/localizer

COPY docker/localizer/pylock.toml ./pylock.toml
RUN --mount=type=cache,id=uvcache,sharing=locked,target=/root/.cache/uv \
    uv pip install -r pylock.toml

COPY packages/python/core /app/packages/python/core
COPY packages/python/common /app/packages/python/common
COPY docker/localizer /app/docker/localizer
RUN uv pip install --no-deps --no-sources \
    /app/packages/python/common \
    /app/packages/python/core \
    /app/docker/localizer

RUN uv pip check

COPY --chmod=0755 docker/localizer/entrypoint.sh /usr/local/bin/entrypoint.sh

# Stamped late so only the trailing ENV layer invalidates per commit; upstream pip-install layers stay cached.
ARG GIT_COMMIT_SHA
ENV GIT_COMMIT_SHA=${GIT_COMMIT_SHA}

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
