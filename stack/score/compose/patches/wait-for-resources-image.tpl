# score-compose synthesizes the wait-for-resources gate with a bare `alpine`
# image — the one unpinned reference the compose artifact would otherwise carry.
# Redirect it through the ALPINE_IMAGE lock hole (workloads/images.yml declares
# alpine, so the mirror job keeps the mirrored digest current), resolved from
# images.lock at up time like every other third-party runtime image.
- op: set
  path: services.wait-for-resources.image
  value: ${ALPINE_IMAGE:?err}
  description: Pin the wait-for-resources gate to the mirrored alpine digest from images.lock
