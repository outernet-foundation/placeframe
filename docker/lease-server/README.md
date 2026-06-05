# placeframe-lease-server

Internal control-plane work-queue. Hosts four lease endpoints (`request`, `progress`, `succeed`, `fail`) that the `reconstructor` polls to claim and complete reconstruction jobs. Bound only to the compose-internal network — no gateway upstream, no auth middleware. See `docker/SPEC.md` for the network-as-auth-boundary rationale.
