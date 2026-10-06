ARG CADDY_IMAGE

FROM ${CADDY_IMAGE}

# Copy the entrypoint and make it executable
COPY --chmod=0755 workloads/gateway/entrypoint.sh /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]