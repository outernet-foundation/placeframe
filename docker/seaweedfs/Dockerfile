ARG SEAWEEDFS_DIGEST
FROM ghcr.io/outernet-foundation/mirror/docker.io/chrislusf/seaweedfs${SEAWEEDFS_DIGEST}

COPY --chmod=0755 docker/seaweedfs/entrypoint-wrapper.sh /usr/local/bin/entrypoint-wrapper.sh
