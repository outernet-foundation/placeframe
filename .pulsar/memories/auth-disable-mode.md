---
updated: 2026-05-27
---

# Add an `AUTH_MODE=disabled` air-gap-friendly mode to the placeframe stack

## Goal

Make authentication optional across the whole stack so a true air-gapped deployment can run without Keycloak, without TLS, and without distributing a self-signed CA to client devices. In an air-gapped LAN, anyone with network access has root anyway — OAuth on top of that is mostly ceremony, and the cert-distribution overhead for `GATEWAY_TLS_MODE=internal` (manually trusting Caddy's root CA on every Unity client) is the specific pain point that motivates this. The discussion that prompted this memory concluded that "disable auth + cleartext" is the architecturally honest answer for air-gap, not "use Caddy's internal CA + tell users to install certs."

## State

- Not started. No code in this initiative has been written. The session that spawned this memory is doing the Localtonet tunnel-swap on `feature/livekit-container` — that work is unrelated and should not be conflated with this initiative.
- The current stack assumes auth is always on: the Litestar API middleware always verifies a JWT, the reconstructor always fetches a Keycloak client-credentials token before calling the API's lease endpoints, the gateway's Caddyfile routes `/auth/*` to Keycloak and has `forward_auth keycloak:8080` on `/loki/*`, and the Unity API client wrapper always attaches a Bearer token.
- `GATEWAY_TLS_MODE` currently has two modes (`plain` for proxy-fronted deployments, `internal` for LAN with Caddy's internal CA). A third mode `none` (cleartext HTTP on `:8080`) needs to be added for air-gap.

## Decisions

- Introduce a single discriminator env var `AUTH_MODE` with values `keycloak` (default) and `disabled`. The compose stack and every auth-aware service reads it.
- In `disabled` mode the API middleware should bypass JWT verification and synthesize a fake principal so downstream code paths that assume "there's a user" stay uniform — do not strip the principal concept from the codebase.
- Keycloak, `auth-initializer`, and the Keycloak-dependent paths in `state-sync` move behind a compose profile (e.g. `keycloak`). Air-gap mode just doesn't include the profile, so those containers never start.
- The reconstructor's service-to-service auth skips the token fetch entirely when `AUTH_MODE=disabled`.
- Unity clients learn the server's auth mode from a server config endpoint hit at startup (NOT a build-time flag) so the same APK works against both modes. The API client wrapper has a "skip auth" branch that omits the Bearer token.
- Caddyfile gets a conditional branch (or a separate file selected by env) that drops `/auth/*` and the `forward_auth` directive when auth is disabled.
- Add `GATEWAY_TLS_MODE=none` alongside `plain` / `internal`. In `none`, Caddy serves cleartext on `:8080`. Android Unity apps need `android:usesCleartextTraffic="true"` (or a per-domain `network_security_config.xml` entry) to talk to a `none`-mode gateway. This manifest tweak is part of the initiative.
- Scope estimate from the prompting discussion: about a day of work end-to-end, plus regression testing that the `AUTH_MODE=keycloak` default path still works after the changes.

## Open questions

- Should the Unity "what auth mode does this server use?" probe be a dedicated endpoint or piggyback on an existing health/config endpoint? Probably the latter, but not decided.
- Does `GATEWAY_TLS_MODE=none` need to coexist with `AUTH_MODE=keycloak`? Strictly the modes are orthogonal, but shipping cleartext-with-OAuth-passwords is a footgun. Worth a guard that rejects that combination at startup.
- Are there any non-API services (Grafana, MinIO console, CloudBeaver) that need their own auth-disabled story, or do we just leave them out of the air-gap profile entirely?
- For the Unity Android manifest change: do we ship `usesCleartextTraffic="true"` unconditionally (simpler, but weakens the default-mode security posture) or scope it to the placeframe domain via `network_security_config.xml` (more work, but clean)?

## Key files

- `compose.yml` (root) — where Keycloak, `auth-initializer`, `state-sync`, gateway, and `migrate-database` are defined; this is where the `keycloak` compose profile gets added and `AUTH_MODE` gets plumbed.
- `docker/api/` — Litestar app with the auth middleware that needs the `AUTH_MODE=disabled` bypass.
- `docker/reconstructor/` — has the Keycloak client-credentials token fetch that needs to be skipped in disabled mode.
- `docker/state-sync/` — Keycloak-dependent paths to gate behind the profile.
- `docker/gateway/Caddyfile` — needs conditional branching for `/auth/*` routing, the `/loki/*` `forward_auth` directive, and a `none` TLS mode that serves cleartext on `:8080`.
- `.env.sample` — declare `AUTH_MODE` and the new `GATEWAY_TLS_MODE=none` value with their semantics. The existing comment block about `internal` CA + "out of band" trust is the trigger for this initiative and should reference it.
- `docker/SPEC.md` — service inventory and auth model; the spec must be updated first per repo policy (spec-first on disagreement).
- Unity API client wrapper (under `apps/MakeItSing/` and `apps/AndroidMobile/`) — where the Bearer token is attached; needs the "skip auth" branch driven by a startup probe.
- Unity Android manifest(s) under both apps' `Assets/Plugins/Android/` — for the `usesCleartextTraffic` / `network_security_config.xml` change.

## Pending threads

- Implement the initiative when an air-gap deployment becomes a real requirement (no active customer demanding it as of 2026-05-27). The natural starting point is updating `docker/SPEC.md` with the new auth and TLS modes, then plumbing `AUTH_MODE` through compose and the API middleware, then the reconstructor and Unity client, then the Caddyfile / `GATEWAY_TLS_MODE=none` / Android manifest changes last.
