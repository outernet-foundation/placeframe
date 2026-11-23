ARG NEURAL_NETWORKS_BASE

FROM ${NEURAL_NETWORKS_BASE}

# PyTorch's default caching allocator uses fixed-size segments, which fragment under
# varying per-job allocation patterns and eventually OOM despite ample free memory.
# Expandable segments use CUDA virtual memory to grow segments on demand, eliminating
# that fragmentation class.
ENV PYTORCH_ALLOC_CONF=expandable_segments:True

# glibc malloc keeps most of the memory a reconstruction frees: it is spread over per-thread arenas, with free blocks
# between live ones that glibc never returns, and it accumulates over jobs, so a long-lived worker ends up holding
# gigabytes while idle. jemalloc's background thread returns unused pages to the system after each job.
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends libjemalloc2=5.3.0-3 \
    && rm -rf /var/lib/apt/lists/*
ENV LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libjemalloc.so.2 \
    MALLOC_CONF=background_thread:true

WORKDIR /app/workloads/reconstructor

ENV UV_TOOLS_ENVIRONMENT=/opt/uv/tools

COPY workloads/reconstructor/pylock.toml ./pylock.toml
RUN --mount=type=cache,id=uvcache,sharing=locked,target=/root/.cache/uv \
    uv pip install -r pylock.toml

COPY packages/python/core /app/packages/python/core
COPY packages/python/common /app/packages/python/common
COPY packages/generated/python/lease-server-client /app/packages/generated/python/lease-server-client
COPY workloads/reconstructor /app/workloads/reconstructor
RUN uv pip install --no-deps --no-sources \
    /app/packages/python/common \
    /app/packages/python/core \
    /app/packages/generated/python/lease-server-client \
    /app/workloads/reconstructor

RUN uv pip check

COPY --chmod=0755 workloads/reconstructor/entrypoint.sh /usr/local/bin/entrypoint.sh

# RECONSTRUCTOR_SHA is the content-addressed tree tag of this image's build context (computed by boatyard over the .dockerignore allowlist) and is stamped onto every ReconstructionMetrics by run_reconstruction so each reconstruction's manifest records which reconstructor build produced it.
ARG RECONSTRUCTOR_SHA
ENV RECONSTRUCTOR_SHA=${RECONSTRUCTOR_SHA}

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
