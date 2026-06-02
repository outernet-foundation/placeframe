---
updated: 2026-05-29
---

# Reconstructor JWT expires mid-run; progress writes silently 401 and `/succeed` is at risk

## Goal

The reconstructor fetches a Keycloak JWT once when it acquires a lease, then keeps using it for the entire reconstruction. Real runs are longer than the token's TTL, so the second half of a reconstruction loses observability (per-frame progress writes all return 401 with `{"detail":"Token expired: Signature has expired"}`) and — more dangerously — the terminal `succeed_lease`/`fail_lease` call uses the same expired token, so a long reconstruction can finish on the GPU but never get committed to the DB.

## State

- Observed live on capture `85c17785-f702-45b1-817a-5018f57a2c46`, lease `38bb86b1-b9e4-4374-900e-83fad17686ea` on 2026-05-29:
  - Lease acquired 17:05:31; reconstruction healthy on GPU, advancing ~6 frames / 10s.
  - First `[progress write failed] (401)` at 17:11:16 — i.e. roughly **5m45s after lease acquisition**.
  - Every subsequent per-frame progress POST 401s; reconstructor keeps reconstructing.
  - API's `progress_current` row froze at the last successful write; client poll returns the stale value, so the phone UI looks hung.
- Nothing has been fixed yet. No code changes on disk for this issue.
- `.env` declares `KEYCLOAK_ACCESS_TOKEN_LIFESPAN=3600`, but the observed expiry was ~5m45s. Either Keycloak isn't honoring the realm override for this client, or `data["expires_in"]` came back small enough that `TokenManager` cached only ~5–6 min. Worth confirming on a fresh investigation — but the bug is real regardless of the exact TTL number.

## Decisions

- The bug is on the **reconstructor side**, not the API or Keycloak. The API correctly rejects an expired bearer with 401; that's by design.
- Two symptoms, one cause:
  1. **Progress observability is lost** — `progress_publisher.ReconstructionPublisher._flush` fires a fire-and-forget `update_progress` call and `_log_progress_failure` just `print`s the exception. Once the token expires, every subsequent flush 401s silently.
  2. **Terminal call is at risk** — the same `api_client.default_headers["Authorization"]` set once in `worker_loop` before `request_lease` is reused for the eventual `succeed_lease` / `fail_lease`. If the run is longer than the TTL, the terminal call also 401s and the reconstruction's outcome is lost.
- Correct shape of the fix is to make the API client always send a fresh token, not to extend the TTL. TTL extension is a bandaid: it just moves the failure threshold and still breaks for the longest reconstructions. Options:
  - Hook into the generated client's request pipeline so every outgoing call re-resolves `await auth.get_token()` via `TokenManager` (whose cache + SKEW logic already handles refresh).
  - Or wrap calls in a 401-retry-once-after-refresh interceptor.
  - The single-shot "set `configuration.access_token` and `default_headers` once per loop iteration" pattern in `docker/reconstructor/src/reconstructor/main.py:40-42` is the root cause and needs to go.
- `progress_publisher`'s `print(f"[progress write failed] {exc}")` should also distinguish 401s loudly — they're not the same class of failure as a transient network blip and currently masquerade as one.

## Open questions

- Why is the actual observed TTL ~5m45s when `.env` declares 3600s? Is Keycloak's realm-export `accessTokenLifespan` being applied? Is the reconstructor's client (`auth_client_id`) overriding it with a client-scoped lifespan? Or is `expires_in` falling through to the `300` default in `TokenManager.get_token` because the response is missing the field?
- Did the *prior* succeeded reconstruction in the same session (which completed at 17:05:31) also hit 401s near the end? If yes, `succeed_lease` somehow still worked — interesting and worth understanding before designing the fix. If no, it was just shorter than the TTL and got lucky.
- Should `TokenManager.get_token` be wired into the generated `placeframe_api_client.Configuration` via its access-token callback (the OpenAPI generator supports one) rather than the current "manually stamp `default_headers` once" pattern?

## Key files

- `docker/reconstructor/src/reconstructor/main.py` — `worker_loop` stamps the bearer header exactly once per loop iteration at lines 40-42; this is the bug site.
- `docker/reconstructor/src/reconstructor/progress_publisher.py` — `_log_progress_failure` (line 80) is where the 401 currently disappears into a `print`.
- `packages/python/common/src/common/token_manager.py` — `TokenManager.get_token` already caches with a 60s skew and refreshes when expired; the fix is making the API client *call it on every request*, not changing this class.
- `docker/api/src/auth.py` — line 91 is where the API raises `NotAuthorizedException("Token expired: ...")` that the reconstructor sees as a 401.
- `docker/keycloak/realm-export/placeframe.json` — realm `accessTokenLifespan` config, parameterized by `KEYCLOAK_ACCESS_TOKEN_LIFESPAN`.

## Pending threads

- Confirm the actual TTL on the wire (decode a fresh reconstructor JWT's `exp` claim vs `iat`) so the open question above is settled before designing the fix.
- Check the prior succeeded reconstruction's Loki logs near its terminal `succeed_lease` call for any 401s.
- Then implement the structural fix: route every reconstructor API call through `TokenManager.get_token` so the cached-and-auto-refreshing token is what's actually sent. After that, the `[progress write failed]` log line can be downgraded from "silent loss" to "genuinely a transient issue."
