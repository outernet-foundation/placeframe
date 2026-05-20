# Phase 2 — Ngrok routing for LiveKit

## Context

Phase 1 stood up the LiveKit server inside compose, but it's only reachable on the compose network. The Phase 3 smoke spike (and every real device session afterward) needs a URL the Magic Leap 2 and Android Mobile devices can actually dial. The original plan deferred this with the assumption that colocalized testing would happen on a shared LAN, with clients dialing `ws://<host-lan-ip>:7880` directly. In practice the dev environment runs in a sandbox where the COI container's published port is **not** on the host's LAN, so LAN-direct doesn't work from headsets on the user's WiFi.

This phase fills the gap by routing LiveKit traffic through the existing ngrok tunnel and the Caddy gateway sidecar (`docker/gateway/`), the same path every other backend service uses. The phase exists because LiveKit is the first service that needs the WebRTC media plane reachable from outside the compose network — every prior route through Caddy has been plain HTTPS. Confirming that the ngrok + Caddy combination can carry both LiveKit's signaling WebSocket **and** its media transport is the open technical question; Phase 0 task 3 of `../livekit-plan.md` flagged it but never resolved it.

**This phase exists outside the original 6-phase breakdown.** It was inserted between the original Phase 1 and Phase 2 (now Phase 3) after the spike build was completed and the ML2 needed an external URL. Phases 3–7 are unchanged in scope; only their numbering shifted by one.

Read before starting:
- `/placeframe/CLAUDE.md` — especially the `:latest` ban (the LiveKit image is already pinned in `.env.lock` from Phase 1; don't reintroduce moving refs), no inline imports, no docstrings.
- `/placeframe/docker/gateway/entrypoint.sh` — the existing Caddyfile assembly. New routes go here, not in a separate file.
- `/placeframe/docker/SPEC.md` — service inventory and ngrok exposure conventions; the new route should be reflected here.

## Goal

After this phase:
- A client outside the compose network (the Magic Leap 2 on the user's WiFi) can reach LiveKit's signaling endpoint via `wss://${PUBLIC_DOMAIN}/livekit/...` through the existing ngrok tunnel and Caddy gateway.
- The data-channel round-trip from the Phase 3 spike (Magic Leap 2 → SFU → echo bot → SFU → Magic Leap 2) succeeds end-to-end via that ngrok path, **or** the failure mode is understood and the chosen fallback (TURN, ngrok TCP tunnel, separate LAN deployment) is documented and configured.
- `docker/SPEC.md` is updated to describe the external exposure path so future readers understand which LiveKit traffic crosses ngrok and which is LAN-only.

## The technical problem

LiveKit splits into two transport layers, each with different reachability requirements:

| Layer | Port (default) | Protocol | Crosses ngrok HTTPS? |
|---|---|---|---|
| Signaling | 7880 | WebSocket-over-HTTP(S) | Yes — plain WS upgrade |
| RTC media (default) | 50000–50100 UDP | UDP datagrams | No — ngrok free is HTTPS-only |
| RTC media (TCP fallback) | 7881 TCP | Raw TCP (ICE-TCP) | No — separate TCP, can't ride HTTPS path |

Signaling is mechanical: add a `reverse_proxy livekit:7880` route to Caddy, the existing HTTPS termination handles the WebSocket upgrade. The hard part is media. WebRTC's ICE picks a candidate pair after signaling; if neither UDP nor a separate TCP path is reachable from the headset, the data channel never establishes even when signaling succeeds.

The fallback options, in order of plausibility:

1. **A self-hosted TURN server** (e.g. coturn) sitting in compose, exposed via ngrok or a separate static-IP path. LiveKit can be configured to advertise a TURN URL clients will relay through. This is the canonical LiveKit answer for NAT-traversal-impossible deployments.
2. **An ngrok TCP tunnel for LiveKit's TCP fallback port (7881).** Adds a second ngrok endpoint to `.env`; only works if the user's ngrok plan supports raw TCP tunnels (free tier does, with the caveat that the URL changes per session unless the plan supports reserved TCP addresses).
3. **WireGuard / Tailscale tunnel between the headset's network and the host.** Out-of-band relative to ngrok; requires headset-side client install (Tailscale ships an Android app but ML2 support is unverified).
4. **Resign and accept LAN-direct.** Move LiveKit's compose ports out of the sandbox onto the user's actual host network so `ws://<host-lan-ip>:7880` works. Inverts the deployment model but is the simplest answer if the sandbox is the obstacle.

The task order below validates signaling first (cheap), then surfaces which fallback is actually needed by attempting a real round-trip.

## Work

### 1. Validate signaling can be reverse-proxied

Add a route to `docker/gateway/entrypoint.sh`'s `backend_routes` snippet, matching the existing handlers' style. Path-stripped reverse proxy to `livekit:7880`:

```caddy
handle_path /livekit/* {
    reverse_proxy livekit:7880
}
```

`handle_path` strips the matched prefix before forwarding — so `wss://${PUBLIC_DOMAIN}/livekit/rtc?access_token=…` arrives at LiveKit as `/rtc?access_token=…`, which is what the SDK expects. Caddy handles WebSocket upgrades on `reverse_proxy` automatically; no extra directive needed.

Restart the gateway (`uv run up` will re-render the Caddyfile). Verify with `curl -sI https://${PUBLIC_DOMAIN}/livekit/` — should return a 200 from LiveKit's HTTP root (the same response that `wget -qO- http://livekit:7880/` produces in the healthcheck).

### 2. Validate signaling end-to-end with a fresh JWT

From a host that is not the dev environment (e.g. a laptop on the user's WiFi, or the Magic Leap 2 directly), connect to the routed URL using the existing smoke-spike tooling:

```bash
# On any machine that can reach ${PUBLIC_DOMAIN}:
LIVEKIT_URL="wss://${PUBLIC_DOMAIN}/livekit" \
uv run --no-sync --with livekit python apps/MakeItSing/Assets/_LiveKitSpike/echo_bot.py "$BOT_JWT"
```

Expected: "Echo bot connected as identity=bot. Ctrl-C to exit." A 401 means the JWT's `iss`/`aud` don't match the server's `LIVEKIT_KEYS` — check `.env`. A 4xx other than 401 means Caddy routing is wrong (likely a path prefix mismatch). A connection that *hangs* in signaling means the WS upgrade is being dropped somewhere in the tunnel — debug with `caddy adapt` and `docker logs placeframe-gateway-1`.

### 3. Attempt a data-channel round-trip and observe ICE candidates

With signaling working, the spike's `Connect → PublishData → DataReceived` round-trip is the real test. Run the Phase 3 smoke spike against `wss://${PUBLIC_DOMAIN}/livekit` and watch the LiveKit server logs for ICE candidate selection:

```bash
docker logs -f placeframe-livekit-1 | grep -i "participant active\|connectionType\|ice"
```

Three possible outcomes:

- **`connectionType: udp` with a srflx candidate selected** — the headset's NAT happens to allow some UDP egress to LiveKit's public reflexive IP. Lucky path; document the deployment but plan for case (b) since not all networks will be this permissive.
- **`connectionType: tcp` via the 7881 candidate** — only if you configured an ngrok TCP tunnel for 7881 in this phase, or the headset can reach LiveKit's 7881 directly somehow. The realistic outcome on a vanilla ngrok HTTPS setup is that 7881 is not reachable and ICE doesn't get a TCP candidate at all.
- **ICE never picks a pair; the SDK times out after ~30s** — the most likely vanilla-ngrok outcome. Move to task 4.

### 4. Pick a media fallback and configure it

Based on task 3's result, pick the simplest workable option from the list above:

- **If task 3 succeeded on UDP** (option (a) for media): nothing more to configure. Document the dependency on UDP reflexive in `docker/SPEC.md`.
- **If task 3 failed and the user's ngrok plan supports a TCP tunnel**: add a second ngrok tunnel for port 7881, set `LIVEKIT_RTC_TCP_EXTERNAL_URL` (or whatever the current server config field is — check `docker.io/livekit/livekit-server` docs for the running version) so signaling advertises the public TCP candidate. Re-run task 3 expecting `connectionType: tcp`.
- **If neither**: stand up coturn alongside LiveKit (a single Dockerfile-less compose service with the image digest-pinned in `.env.lock`), configure LiveKit's TURN section to advertise it, and re-run task 3 expecting `connectionType: relay`. Read coturn's [README](https://github.com/coturn/coturn) and pick a stable release before pinning.
- **If the user prefers to defer media routing entirely**: document that the smoke spike succeeds in signaling but fails in media, and proceed to Phase 3's device test using a same-LAN deployment of the LiveKit container (move the compose service off the sandbox, onto the host's docker daemon directly). This unblocks Phase 3 without solving the cross-network case; flag the deferred work as a follow-up ticket.

The choice depends on user input — don't guess. Ask before subscribing the user to a paid ngrok tier or adding coturn.

### 5. Update `docker/SPEC.md`

In a separate prose commit (per the prose-and-code separation rule in `/placeframe/CLAUDE.md`), add a "LiveKit external exposure" subsection to `docker/SPEC.md`. Cover:
- Which LiveKit ports are reachable from outside compose and via what mechanism (Caddy reverse-proxy on `/livekit/*`, optional ngrok TCP tunnel for 7881, optional coturn relay).
- The signaling URL clients should use (`wss://${PUBLIC_DOMAIN}/livekit`).
- Whether the deployment uses UDP, TCP-fallback, or TURN-relay for media, and how to flip between them.

## Exit criteria

This phase passes when **all** of the following are true:
- `wss://${PUBLIC_DOMAIN}/livekit/rtc?access_token=…` accepts a LiveKit SDK connection from outside the compose network (signaling reachable).
- A data-channel round-trip from a real external client (Magic Leap 2 or Android Mobile preferred, a Python client on a separate machine acceptable) completes end-to-end via the routed URL — or the chosen fallback (TCP tunnel / coturn / same-LAN re-deployment) does the same.
- `docker/SPEC.md` reflects the configured exposure model.

The Phase 3 spike consumes this phase's output. If this phase resolves to "same-LAN re-deployment" rather than ngrok, Phase 3's URL guidance changes accordingly — flag that in the spike's README.

## Commit hygiene

Per `/placeframe/CLAUDE.md`:
- Source-config changes (Caddy entrypoint, any compose / `.env.sample` / `.env.lock` updates) go in one or more code commits, separate from prose.
- `docker/SPEC.md` update is its own prose commit.
- If TURN or an additional ngrok endpoint is added, the digest pin / endpoint config lives in `.env.lock` per the repo's `:latest`-ban and pinning rules.

## Out of scope

- Multi-region or multi-node LiveKit deployment — the original plan's "single-node, in-memory" scope still holds.
- Authenticated TURN credentials issued per-user — if coturn lands, use a shared static credential for the colocalized demo; per-user issuance is a follow-up.
- Anything in `apps/MakeItSing/` — that's Phases 3 and 5–7.
- Re-architecting the gateway to terminate WebRTC directly (e.g. by Caddy proxying SRT/RTP). Out of scope; the SFU does that.
