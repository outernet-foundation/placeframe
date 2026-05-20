# Phase 1 — LiveKit compose service

## Context

We are swapping MakeItSing's Photon Realtime transport for self-hosted LiveKit. The full plan is split across `README.md` and Phases 1–7 in this directory; see `README.md` for the dependency graph.

**This phase is the minimum infrastructure to run the Phase 3 spike.** It adds the LiveKit server to the docker compose stack, scaffolds the env keys, and pins the image digest. Nothing more — no API endpoint, no settings model fields, no codegen. Phase 4 picks up where this leaves off.

The artifacts produced here are **durable** — designed to land on mainline as the first real commit of the swap. If the Phase 3 spike fails, this phase still survives unmodified for any WebRTC-SFU experiment; the only revertible piece is the one-stanza compose block.

Read `/placeframe/CLAUDE.md` before starting. Especially the pinning rule (no `:latest`, all images digest-pinned), commit-style conventions, and the no-bare-`docker compose` rule.

## Goal

After this phase:
- `uv run up` brings up a healthy LiveKit server alongside the existing services.
- `.env.sample` documents the three LiveKit env keys.
- `.env.lock` contains a `LIVEKIT_IMAGE` digest pin.
- Nothing else changes — no Unity, no API, no codegen.

## Work

### 1. Pick a LiveKit server version and pin it by digest

The CLAUDE.md rule: no `:latest`, no `stable`, no mutable tags. All container images use content-addressed `@sha256:...` references in `.env.lock`.

1. Pick the latest stable LiveKit server release from <https://github.com/livekit/livekit/releases>.
2. Resolve its digest:
   ```bash
   docker buildx imagetools inspect docker.io/livekit/livekit-server:v1.X.Y
   ```
   Capture the `Manifest`'s `Digest:` line — that's the `sha256:...` we pin.
3. Add to `/placeframe/.env.lock`:
   ```
   LIVEKIT_IMAGE=docker.io/livekit/livekit-server@sha256:<digest>
   ```
   If `scripts/src/scripts/context_sha.py` (or similar) automates digest resolution for other images, follow that pattern. Otherwise pin by hand and add a one-line comment in `.env.sample` pointing at the release tag for future bumps.

**Phase 3 reuses this exact image.** Pick the version intentionally — not as a placeholder. The digest decision propagates to every subsequent phase.

### 2. Add the LiveKit service to compose

Add to `/placeframe/compose.yml` (in the place adjacent to other long-running services like Keycloak/MinIO/Postgres — look at the existing structure):

```yaml
livekit:
  image: ${LIVEKIT_IMAGE:?err}
  environment:
    LIVEKIT_KEYS: "${LIVEKIT_API_KEY:?err}: ${LIVEKIT_API_SECRET:?err}"
    LIVEKIT_PORT: "7880"
    LIVEKIT_RTC_TCP_PORT: "7881"
    LIVEKIT_RTC_UDP_PORT_RANGE_START: "50000"
    LIVEKIT_RTC_UDP_PORT_RANGE_END: "50100"
  ports:
    - "7880:7880"
    - "7881:7881"
    - "50000-50100:50000-50100/udp"
  healthcheck:
    test: ["CMD", "wget", "-qO-", "http://localhost:7880/"]
    interval: 10s
    timeout: 3s
    retries: 5
  restart: unless-stopped
```

**No Postgres, no Redis.** Single-node LiveKit keeps room state in memory; that's adequate for the ~12-headset target.

No Dockerfile — the LiveKit image is upstream. Nothing to allowlist in `.dockerignore`.

### 3. Add env scaffolding

`/placeframe/.env.sample` gains:

```
# LiveKit (server-side credentials)
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=devsecretmustbeatleast32charslongforhmacsha256
LIVEKIT_URL=ws://livekit:7880
```

The real `/placeframe/.env` (gitignored) needs the same three keys. **Do not touch the real `.env`** — the user manages it. Stop and tell them to set the keys if they aren't already present.

`LIVEKIT_URL` here is the URL Unity clients dial. Inside the compose network the service is `ws://livekit:7880`, but Unity runs on host devices, not in compose — they need a URL that resolves over WiFi (e.g. `ws://<host-lan-ip>:7880`). For Phase 1's purposes any non-empty value is fine; Phase 3 supplies the device-reachable URL into the smoke scene directly.

For production the API key/secret must be regenerated per environment.

## Commit hygiene

Single source-code commit covering: `compose.yml`, `.env.sample`, `.env.lock`. Conventional commit style. No prose changes in this phase (`docker/SPEC.md` updates happen later in Phase 4 or Phase 7 — your choice).

No `Co-Authored-By`. No `--no-verify`. If a hook fails, fix the issue and make a new commit (never amend).

## Exit criteria

- `uv run up` brings up `livekit` alongside other services; healthcheck reaches healthy state.
- `curl http://localhost:7880/` returns LiveKit's root-route HTML (or any 2xx response, depending on server version).
- `uv run --no-sync preflight` is green.
- `.env.lock` has `LIVEKIT_IMAGE` pinned by digest.
- Source-code commit lands on the working branch.

## Out of scope

- Token-mint endpoint, settings, codegen — Phase 4.
- Unity SDK install — Phase 3 (smoke scene) and Phase 6 (real transport).
- Gateway/ngrok WebSocket route — Phase 4 or deferred entirely depending on deployment topology.
- Multi-node LiveKit / Redis-backed room state.
