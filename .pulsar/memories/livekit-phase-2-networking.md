---
updated: 2026-05-20
---

# LiveKit Phase 2: pick a media-plane transport that works for both airgapped-LAN demo and cloud-hosted deployments

## Goal
Get the LiveKit media plane (WebRTC UDP `50000-50100` + ICE-TCP `7881`) reachable by client headsets in both deployment shapes the project must support:

1. **Airgapped convention demo** — backend on a high-powered laptop on a router, arbitrary attendee phones / headsets join the same WiFi. No internet required.
2. **Cloud hosting** — backend on a remote VPS, clients connect from anywhere.

The current `livekit-plan/02-ngrok-routing.md` is solving the wrong problem: it tries to bridge the dev-sandbox topology (COI sandbox behind home NAT) to public clients via ngrok. That's a dev-environment concern, not the project's networking architecture.

## State
- Phase 1 (`cb3f866d`) shipped: `livekit-server:v1.12.0` digest-pinned, ports `7880/7881/50000-50100` in `compose.yml`, healthcheck wired.
- Phase 2 is the active blocker. Phases 3-7 unchanged (ML2/Android spike → backend `/livekit/token` → `INetworkTransport` refactor → real `LiveKitTransport` → cutover).
- Two `wip` commits on the branch (`fa7e9650`, `1ffcfd57`) renumbered phases to insert ngrok-routing as Phase 2 and filled out `02-ngrok-routing.md`, plus added smoke-scene scaffolding in `apps/MakeItSing/Assets/_LiveKitSpike/`. These violate prose/code commit hygiene and need `/tidy-commits` before merge. Also includes four `response*.md` scratch files at repo root (some unrelated to LiveKit) and Rider `.lscache` files that shouldn't be tracked.
- Existing `state-sync` service rides the gateway's ngrok HTTPS tunnel via gRPC-over-h2c (`docker/gateway/entrypoint.sh:11-14`). User initially cited this as precedent for LiveKit-over-ngrok; it isn't — gRPC is TCP, WebRTC media is UDP.

## Decisions
- **Ngrok cannot carry the media plane.** Verified against 2026 docs: no UDP on any tier (structural, not a paywall). TCP endpoints work but require a payment method on file even on free. Signaling-over-ngrok (`wss://${PUBLIC_DOMAIN}/livekit`) would work — it's HTTP-shaped like state-sync — but the media plane needs a separate transport.
- **Tailscale Funnel is strictly worse than ngrok here:** HTTPS-only, three ports (443/8443/10000), no UDP, no raw TCP. Architectural regression.
- **Tailscale mesh works for media but is disqualified by the use case.** User requirement: arbitrary attendee phones at a convention demo. Cannot require every participant to join a tailnet.
- **The actual architecture is "LiveKit advertises a reachable IP for the active deployment."** Public tunnels (ngrok / Funnel) were a category error — they provide a public endpoint for one protocol shape, not a public IP. WebRTC needs an actual reachable IP route for UDP datagrams.
- **Airgapped case needs nothing special.** Laptop has a LAN IP (e.g. `192.168.1.10`). LiveKit advertises that. Clients on the same WiFi send UDP directly. No NAT between client and server → ICE picks a host candidate. Bypass ngrok entirely for LiveKit in this topology.
- **Cloud case is the same shape with two variables changed:** LAN IP → VPS public IP, self-signed/no-TLS → Let's Encrypt. Same compose stack, only `LIVEKIT_NODE_IP`, `LIVEKIT_SIGNALING_URL`, and the TLS cert source change.
- **coturn is the cloud-case insurance policy, not a hard requirement.** One additional compose service (digest-pinned image) advertising the same public IP. Without it, ~10-15% of mobile clients on restrictive carrier NATs will fail. Off by default; on for production if telemetry shows failures. Goes in an optional `compose.coturn.yml` overlay.

## Open questions
- How should the dev-sandbox topology be unblocked for the user's own headset smoke test? Options: (a) modify `/workspace/scripts/src/scripts/sandbox/` to expose LiveKit ports on the host's LAN bridge instead of `incusbr0`, (b) run a second ngrok TCP tunnel for `:7881` with card-on-file (dev-only), (c) just run LiveKit outside the sandbox for the dev smoke test. User has said "we can do whatever we need to to this sandbox" — option (a) is in scope.
- LiveKit v1.12.0 config schema: exact knob for advertising the external IP — `rtc.use_external_ip` + `node_ip`, vs `LIVEKIT_NODE_IP` env, vs a config file. Resolve at implementation time against the server's docs.
- Whether to split current Phase 2 into 2a (dev smoke path) and 2b (demo / cloud deployment with `compose.public.yml` + optional coturn), or rewrite Phase 2 as a single "LiveKit advertises the right external address; ports are open" task with deployment-specific overlays.

## Key files
- `livekit-plan/02-ngrok-routing.md` — the phase doc that needs to be rewritten or replaced. Currently assumes ngrok-as-public-IP.
- `livekit-plan/README.md` — phase numbering / status board.
- `docker/gateway/entrypoint.sh` — Caddy config; lines 11-14 show the `h2c` setup that makes state-sync work over ngrok and explains why that precedent doesn't transfer to UDP. Would need a `handle_path /livekit/*` route if signaling rides this gateway.
- `compose.yml` — `livekit` service definition (ports `7880/7881/50000-50100`), `ngrok` service definition (lines ~200-217, `http`-only).
- `apps/MakeItSing/Assets/_LiveKitSpike/` — smoke spike scaffolding; the SDK and echo-bot patterns to use when validating the chosen transport end-to-end.
- `/workspace/scripts/src/scripts/sandbox/` — Pulsar sandbox typer app. Incus-managed, COI container on `10.250.250.x` / `incusbr0`. Would need a proxy device or bridge change to expose LiveKit ports on the host LAN for dev smoke testing.

## Pending threads
- Decide between rewrite vs. split for Phase 2 (single task with overlays, or 2a/2b). User has not yet picked.
- Once decided, implement: (1) LiveKit external-IP config, (2) firewall port doc (`50000-50100/udp`, `7880/tcp`, `7881/tcp`), (3) airgapped-vs-cloud compose layering (precedent: `compose.cuda.yml` / `compose.rocm.yml`), (4) optional `compose.coturn.yml` overlay for cloud.
- Resolve dev-sandbox unblock (sandbox change vs. dev-only tunnel vs. run outside sandbox) so Phase 3's ML2 / Android smoke test isn't blocked on networking.
- Clean up the two `wip` commits and the `response*.md` / `.lscache` files before this branch is mergeable.
