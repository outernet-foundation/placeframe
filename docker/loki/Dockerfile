ARG LOKI_DIGEST
FROM grafana/loki:3.5.0${LOKI_DIGEST}

COPY docker/loki/config.yaml /etc/loki/config.yaml
COPY docker/loki/box.yaml /etc/loki/box.yaml
