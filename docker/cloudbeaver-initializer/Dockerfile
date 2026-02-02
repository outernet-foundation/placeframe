ARG POSTGRES_BOOKWORM_DIGEST

# Explicitly define the repo and tag so the digest can be appended
FROM docker.io/library/postgres:16-bookworm${POSTGRES_BOOKWORM_DIGEST}

# Copy the entrypoint and make it executable
COPY --chmod=0755 docker/cloudbeaver-initializer/entrypoint.sh /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]