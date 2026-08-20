ARG POSTGIS_DIGEST
FROM postgis/postgis:16-3.4-alpine${POSTGIS_DIGEST}

COPY --chmod=0755 docker/postgres/entrypoint-wrapper.sh /usr/local/bin/entrypoint-wrapper.sh
