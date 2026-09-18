ARG POSTGRES_BOOKWORM_DIGEST

# Explicitly define the repository so the digest can be appended
FROM ghcr.io/outernet-foundation/mirror/docker.io/library/postgres${POSTGRES_BOOKWORM_DIGEST}

# Copy the entrypoint and make it executable
COPY --chmod=0755 docker/cloudbeaver-initializer/entrypoint.sh /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]