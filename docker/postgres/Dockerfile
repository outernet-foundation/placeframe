ARG POSTGIS_DIGEST
FROM ghcr.io/outernet-foundation/mirror/docker.io/postgis/postgis${POSTGIS_DIGEST}

COPY --chmod=0755 docker/postgres/entrypoint-wrapper.sh /usr/local/bin/entrypoint-wrapper.sh
