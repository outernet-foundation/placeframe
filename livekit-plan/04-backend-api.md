# Phase 4 — Backend API (token-mint endpoint + codegen)

## Context

Phase 1 added the LiveKit server to compose. Phase 3 verified the SDK works on ML2 + Android Mobile. This phase finishes the **server-side** half of the swap: a `POST /livekit/token` endpoint that mints LiveKit JWTs for authenticated callers, settings plumbing, router registration, and regeneration of the C# API client so Phase 6's Unity transport has a typed method to call.

**No Unity code changes in this phase.** Picks up from where Phase 1 left off — the compose service, `.env.sample` keys, and `.env.lock` digest pin are already in place.

Read `/placeframe/CLAUDE.md` for project conventions before starting — especially the codegen commit hygiene, `common.bash` for any shell-out, no inline imports, no docstrings.

Phase 4 and Phase 5 are independent — different parts of the repo, no shared files. They may run in parallel or in either order after Phase 3 passes.

## Goal

After this phase:
- `POST /api/livekit/token` returns `{token, url, identity}` for an authenticated caller.
- The auto-generated C# API client (`packages/generated/csharp/api-client/`) exposes a `PostLivekitToken` method that Phase 6 will call.
- Settings (`livekit_api_key`, `livekit_api_secret`, `livekit_url`) are declared on the API service's settings model.

## Work

### 1. Settings additions

Add to `/placeframe/docker/api/src/settings.py` (or equivalent — look for where other env-backed settings are declared on the Settings model):

```python
livekit_api_key: str
livekit_api_secret: str
livekit_url: str
```

`livekit_url` is the URL Unity clients dial — `ws://livekit:7880` inside the compose network is wrong for Unity (Unity is on the host LAN, not the compose network). Use whatever URL is appropriate for the dev/colocalized deployment. For LAN-only colocalized: `ws://<host-lan-ip>:7880`. Treat the value as supplied via env (it already is, from Phase 1's `.env.sample`).

### 2. Token-mint endpoint

The endpoint lives in `/placeframe/docker/api/src/routers/livekit.py`. Mirror the controller pattern already used elsewhere in `docker/api/src/routers/` — read `leases.py` and one other router file first to match conventions (Litestar `Controller` class, auth dependency name, settings injection style).

Authentication: LiveKit identity must be **server-derived from the validated Keycloak `sub` claim**, not client-supplied. This is the key design choice — it gives slot-claim (Phase 6) stable identities to map to playerIds. Look at how the existing routes obtain the authenticated user (probably an `AuthenticatedUser` dependency from `docker/api/src/auth.py`) and match it.

Sketch (adapt names/types to match the project):

```python
import time
from datetime import timedelta
from typing import Annotated

import jwt
from litestar import Controller, post
from litestar.params import Body
from pydantic import BaseModel

from ..settings import Settings


class LiveKitTokenRequest(BaseModel):
    room: str


class LiveKitTokenResponse(BaseModel):
    token: str
    url: str
    identity: str


class LiveKitController(Controller):
    path = "/livekit"

    @post("/token")
    async def mint_token(
        self,
        data: Annotated[LiveKitTokenRequest, Body()],
        settings: Settings,
        request_user: AuthenticatedUser,
    ) -> LiveKitTokenResponse:
        identity = request_user.subject
        now = int(time.time())
        claims = {
            "iss": settings.livekit_api_key,
            "sub": identity,
            "iat": now,
            "exp": now + int(timedelta(hours=6).total_seconds()),
            "video": {
                "room": data.room,
                "roomJoin": True,
                "canPublish": True,
                "canSubscribe": True,
                "canPublishData": True,
            },
        }
        token = jwt.encode(claims, settings.livekit_api_secret, algorithm="HS256")
        return LiveKitTokenResponse(token=token, url=settings.livekit_url, identity=identity)
```

Adjust the auth dependency, settings access, and import paths to match what `leases.py` does. If the project has a base controller or shared response model pattern, use that.

PyJWT is the encoder. If it isn't already a transitive dep of `docker/api/`, add it to that service's `pyproject.toml` and re-run `uv run lock-python`. Don't pull in a JWT library that isn't already on the dependency list without thinking — prefer the one already declared by an adjacent service if possible.

### 3. Router registration

Register `LiveKitController` in `docker/api/src/main.py` wherever the other routers are registered. Match the surrounding registration style — `route_handlers` list, `Litestar(...)` construction.

### 4. Codegen

Order matters (per `/placeframe/CLAUDE.md` "Generation pipeline" section):

```bash
uv run up --quiet-pull                           # bring up the stack, verify livekit healthcheck passes
uv run generate-clients --project docker/api     # regenerate API clients including the new endpoint
```

Skip `generate-datamodels` and `lock-python` unless you changed schema (`database/*.sql`) or `pyproject.toml` respectively. Adding PyJWT would require `lock-python` between sync and generate-clients.

The new `PostLivekitToken` async method will appear automatically in `packages/generated/csharp/api-client/`. **Do not edit generated code by hand.**

### 5. (Optional) Gateway WebSocket route

If external (ngrok) access to LiveKit signaling is needed, add a Caddy route in `/placeframe/docker/gateway/entrypoint.sh` proxying `/livekit` → `ws://livekit:7880`. **Skip this for the LAN-only colocalized target** — Unity clients dial `ws://<host>:7880` directly. Document in the PR description either way so the choice is visible.

Open question #4 from the README (deployment topology) is relevant here. If unresolved, default to LAN-only and skip this step.

## Commit hygiene

Two or three commits, in this order:

1. **Source code commit.** All of: `docker/api/src/routers/livekit.py`, `docker/api/src/settings.py`, `docker/api/src/main.py`, any `pyproject.toml` / `uv.lock` / `pylock.toml` changes from adding PyJWT (if needed). Conventional commit-style message.
2. **Codegen commit.** Contents: only files under `packages/generated/`. Message: exactly `Run generate-clients` — no body, no rationale.
3. **(If needed) Prose commit.** If `docker/SPEC.md` needs an entry for the new service (it should — service inventory + the token-mint endpoint + the colocalized-LAN deployment model), put it in its own commit, never sharing a commit with code. Phase 7 also touches `docker/SPEC.md`; if you'd rather defer the prose entry there, that's acceptable, but note in the PR that the spec entry is pending.

No `Co-Authored-By`. No `--no-verify`. If a hook fails, fix the underlying issue and make a new commit (never amend).

## Exit criteria

- `uv run --no-sync preflight` is green.
- Manual smoke test from the host:
  ```bash
  curl -X POST http://localhost:8080/api/livekit/token \
       -H "Authorization: Bearer $KEYCLOAK_TOKEN" \
       -H "Content-Type: application/json" \
       -d '{"room":"test"}'
  ```
  returns `{token, url, identity}` with a JWT that decodes correctly.
- A `livekit-server-sdk` Python script using the minted token can `Room.connect(url, token)` to "connected" state. Disconnect immediately afterward — wire-up check only.
- The new `PostLivekitToken` method exists in `packages/generated/csharp/api-client/src/PlaceframeApiClient/`.
- Commits are clean (no codegen in the source commit, no source in the codegen commit, no prose mixed in).

## Out of scope

- Anything in `apps/MakeItSing/` — Phases 5–7.
- Anonymous/guest token paths (open question #1).
- Voice/audio capabilities (the `video` claim is the canonical LiveKit grant name even for data-only use).
- Multi-node LiveKit / Redis-backed room state.
- ngrok-UDP exposure work.
