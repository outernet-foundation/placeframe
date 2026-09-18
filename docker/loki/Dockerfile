ARG LOKI_DIGEST
FROM ghcr.io/outernet-foundation/mirror/docker.io/grafana/loki${LOKI_DIGEST}

COPY docker/loki/config.yaml /etc/loki/config.yaml
COPY docker/loki/box.yaml /etc/loki/box.yaml
