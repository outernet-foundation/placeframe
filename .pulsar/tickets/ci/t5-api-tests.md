---
id: T5
title: Integration tests for API service
status: design-needed
depends_on: []
---

# T5: Integration tests for API service

See `ci-background.md` for shared CI context.

## Goal

Automated tests that verify the API service's endpoints work correctly against real database and storage backends.

## Context

`docker/api/tests/` currently contains only `__init__.py` — no actual tests. The API is a Litestar ASGI app that talks to PostgreSQL, MinIO, and Keycloak. Testing it meaningfully requires these services running.

## Key files

- `docker/api/src/api/` — the API application
- `docker/api/tests/` — empty test directory
- `compose.yml` — service definitions for postgres, minio, keycloak

## Approach considerations

- **Unit tests** can test request/response handling with Litestar's built-in test client (HTTPX-based), mocking database and storage calls
- **Integration tests** need real postgres + minio + keycloak running — probably via `docker compose` with a test-specific profile or a dedicated test compose file
- Consider using pytest fixtures that spin up services via `testcontainers-python` for full isolation
- Keycloak auth can be tested with a pre-configured test realm (already exists: `docker/keycloak/realm-export/placeframe.json`)

## Depends on

Nothing.

## Done when

**Requires Docker (verify with services running):**
- `uv run pytest docker/api/tests/` passes against real postgres + minio + keycloak
