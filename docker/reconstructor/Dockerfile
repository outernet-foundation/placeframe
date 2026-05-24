FROM neural-networks-base AS dev

# PyTorch's default caching allocator uses fixed-size segments, which fragment under
# varying per-job allocation patterns and eventually OOM despite ample free memory.
# Expandable segments use CUDA virtual memory to grow segments on demand, eliminating
# that fragmentation class.
ENV PYTORCH_ALLOC_CONF=expandable_segments:True

WORKDIR /app/docker/reconstructor

ENV UV_TOOLS_ENVIRONMENT=/opt/uv/tools

COPY docker/reconstructor/pylock.toml ./pylock.toml
RUN --mount=type=cache,id=uvcache,sharing=locked,target=/root/.cache/uv \
    uv pip install -r pylock.toml

COPY packages/python/core /app/packages/python/core
COPY packages/python/common /app/packages/python/common
COPY packages/generated/python/api-client /app/packages/generated/python/api-client
COPY docker/reconstructor /app/docker/reconstructor
RUN uv pip install --no-deps --no-sources \
    /app/packages/python/common \
    /app/packages/python/core \
    /app/packages/generated/python/api-client \
    /app/docker/reconstructor

RUN uv pip check

COPY --chmod=0755 docker/reconstructor/entrypoint.sh /usr/local/bin/entrypoint.sh

# RECONSTRUCTOR_SHA is the content-addressed hash of this image's build context (computed by build_scripts.placeframe.context_sha.compute_service_shas) and is stamped onto every ReconstructionMetrics by run_reconstruction so each reconstruction's manifest records which reconstructor build produced it.
ARG RECONSTRUCTOR_SHA
ENV RECONSTRUCTOR_SHA=${RECONSTRUCTOR_SHA}

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
