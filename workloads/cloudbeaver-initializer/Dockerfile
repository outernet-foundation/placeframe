ARG POSTGRES_BOOKWORM_IMAGE

FROM ${POSTGRES_BOOKWORM_IMAGE}

# Copy the entrypoint and make it executable
COPY --chmod=0755 workloads/cloudbeaver-initializer/entrypoint.sh /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]